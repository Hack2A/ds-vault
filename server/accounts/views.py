import random
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import OTPCode
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
    Returns: 201 with tokens on success, 400 on validation error.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            tokens = get_tokens_for_user(user)
            return Response(
                {
                    "message": "Account created successfully.",
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                    },
                    **tokens,
                },
                status=status.HTTP_201_CREATED,
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
        send_mail(
            subject="Your DS-Vault Login OTP",
            message=(
                f"Hi {user.username},\n\n"
                f"Your one-time password (OTP) is: {code}\n\n"
                f"This OTP is valid for {OTP_EXPIRY_MINUTES} minutes.\n"
                f"Do not share this code with anyone.\n\n"
                f"— DS-Vault Team"
            ),
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            fail_silently=False,
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

        session_token = serializer.validated_data['session_token']
        otp = serializer.validated_data['otp']

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
                "message": "Login successful.",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                },
                **tokens,
            },
            status=status.HTTP_200_OK,
        )
