import random
import sys
import os
import uuid
from django.core.cache import cache

# Add the project root to sys.path so the Encryption module can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from Encryption.seed_phrase import SeedPhrase, SeedPhraseAuth

from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import OTPCode, UserProfile
from .serializers import LoginSerializer, RegisterSerializer, VerifyOTPSerializer

OTP_EXPIRY_MINUTES = 10


def get_tokens_for_user(user):
    """Generate JWT access and refresh tokens for a user."""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


def generate_otp():
    """Return a random 6-digit OTP string."""
    return f"{random.randint(100000, 999999)}"


class RegisterView(APIView):
    """
    POST api/auth/register/
    Body: { username, email, password, password2 }
    Returns: 201 with session_token on success, 400 on validation error.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.get('email', '')
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']

            session_token = str(uuid.uuid4())
            code = generate_otp()

            # Save in cache for OTP_EXPIRY_MINUTES
            cache.set(
                session_token,
                {
                    'type': 'register',
                    'username': username,
                    'email': email,
                    'password': password,
                    'otp': code,
                },
                timeout=OTP_EXPIRY_MINUTES * 60
            )

            # Send OTP via email
            html_message = render_to_string('email/otp_email.html', {
                'username': username,
                'otp': code,
                'expiry': OTP_EXPIRY_MINUTES,
                'action_type': 'register',
            })
            
            send_mail(
                subject="🔐 Cryptrael Vault Registration - Verify Your Account",
                message=(
                    f"Hi {username},\n\n"
                    f"Your one-time password (OTP) for registration is: {code}\n\n"
                    f"This OTP is valid for {OTP_EXPIRY_MINUTES} minutes.\n"
                    f"Do not share this code with anyone.\n\n"
                    f"— Cryptrael Vault Team"
                ),
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False,
                html_message=html_message,
            )

            return Response(
                {
                    "message": f"OTP sent to {email}. Please verify to complete registration.",
                    "session_token": session_token,
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    POST api/auth/login/
    Body: { username, password }
    Step 1 of 2FA — verifies credentials then sends OTP to email.
    Returns: { message, session_token }  (NO JWT yet)
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        from django.contrib.auth.models import User
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = None

        if user is None or not user.check_password(password):
            return Response(
                {"detail": "Invalid credentials. Please try again."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Invalidate any previous unused OTPs for this user
        OTPCode.objects.filter(user=user, is_used=False).update(is_used=True)

        # Generate and store new OTP
        code = generate_otp()
        otp_obj = OTPCode.objects.create(user=user, code=code)

        # Send OTP via email
        html_message = render_to_string('email/otp_email.html', {
            'username': user.username,
            'otp': code,
            'expiry': OTP_EXPIRY_MINUTES,
            'action_type': 'login',
        })
        
        send_mail(
            subject="🔐 Cryptrael Vault Login - Verify Your Identity",
            message=(
                f"Hi {user.username},\n\n"
                f"Your one-time password (OTP) is: {code}\n\n"
                f"This OTP is valid for {OTP_EXPIRY_MINUTES} minutes.\n"
                f"Do not share this code with anyone.\n\n"
                f"— Cryptrael Vault Team"
            ),
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            fail_silently=False,
            html_message=html_message,
        )

        return Response(
            {
                "message": f"OTP sent to {user.email}. Please verify to complete login.",
                "session_token": str(otp_obj.session_token),
            },
            status=status.HTTP_200_OK,
        )


class VerifyOTPView(APIView):
    """
    POST api/auth/verify-otp/
    Body: { session_token, otp }
    Step 2 of 2FA — verifies OTP and returns JWT tokens.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        session_token = str(serializer.validated_data['session_token'])
        otp = serializer.validated_data['otp']

        # 1. Check if token exists in cache (Registration Flow)
        cached_data = cache.get(session_token)
        if cached_data and cached_data.get('type') == 'register':
            if cached_data['otp'] != otp:
                return Response(
                    {"detail": "Invalid OTP. Please try again."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            # OTP is correct, create the user
            from django.contrib.auth.models import User
            try:
                user = User.objects.create_user(
                    username=cached_data['username'],
                    email=cached_data['email'],
                    password=cached_data['password']
                )
            except Exception as e:
                return Response(
                    {"detail": "Error creating account. The username or email may have been taken."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Generate and hash 12-word seed phrase
            auth = SeedPhraseAuth()
            seed_phrase_words = auth.generate_phrase(word_count=12)
            seed_phrase_hash = auth._phrase_to_hash(seed_phrase_words)

            # Store the hashed seed phrase in the UserProfile
            UserProfile.objects.create(user=user, seed_phrase_hash=seed_phrase_hash)

            # Clear cache
            cache.delete(session_token)
            
            tokens = get_tokens_for_user(user)

            return Response(
                {
                    "message": "Account created successfully. SAVE YOUR SEED PHRASE OUTSIDE THIS APP.",
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                    },
                    "seed_phrase": seed_phrase_words,
                    **tokens,
                },
                status=status.HTTP_201_CREATED,
            )

        # 2. Check if token exists in DB (Login Flow)
        try:
            otp_obj = OTPCode.objects.get(session_token=session_token)
        except OTPCode.DoesNotExist:
            return Response(
                {"detail": "Invalid session token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check already used
        if otp_obj.is_used:
            return Response(
                {"detail": "This OTP has already been used."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check expiry
        expiry_time = otp_obj.created_at + timedelta(minutes=OTP_EXPIRY_MINUTES)
        if timezone.now() > expiry_time:
            otp_obj.is_used = True
            otp_obj.save()
            return Response(
                {"detail": "OTP has expired. Please login again to get a new OTP."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check code match
        if otp_obj.code != otp:
            return Response(
                {"detail": "Invalid OTP. Please try again."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # All checks passed — mark as used and issue JWT
        otp_obj.is_used = True
        otp_obj.save()

        user = otp_obj.user
        tokens = get_tokens_for_user(user)

        return Response(
            {
                "message": "OTP verified successfully.",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                },
                **tokens,
            },
            status=status.HTTP_200_OK,
        )


class ProfileView(APIView):
    """
    GET api/auth/profile/
    Returns the authenticated user's profile info.
    Requires: Authorization: Bearer <access_token>
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response(
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "date_joined": user.date_joined,
            },
            status=status.HTTP_200_OK,
        )
