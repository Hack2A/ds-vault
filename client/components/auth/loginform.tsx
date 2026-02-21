"use client";

import { navigate } from "@/lib/navigation";
import { authService } from "@/services/authService";
import { useForm } from "react-hook-form";
import GoogleAuth from "./GoogleAuth";

type LoginFormData = {
    email: string;
    password: string;
};

export default function LoginForm() {
    const {
        register,
        handleSubmit,
        formState: { errors },
    } = useForm<LoginFormData>();

    const onSubmit = (data: LoginFormData) => {
        authService.login(data).then((response) => {
            if (response.data.tokens) {
                localStorage.setItem("token", response.data.tokens.access);
                navigate("/dashboard", true);
            }
        });
    };

    return (
        <div className="w-full max-w-md">
            <div className="mb-8">
                <h2 className="text-3xl font-bold text-[#F1F5F9] mb-2">Sign In</h2>
                <p className="text-[#94A3B8]">Enter your credentials to access your vault</p>
            </div>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                {/* Email Field */}
                <div>
                    <label
                        htmlFor="email"
                        className="block text-sm font-medium text-[#F1F5F9] mb-2"
                    >
                        Email
                    </label>
                    <input
                        id="email"
                        type="email"
                        {...register("email", {
                            required: "Email is required",
                            pattern: {
                                value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                                message: "Invalid email address",
                            },
                        })}
                        className="w-full px-4 py-3 bg-[#1E293B] border border-[#7C3AED]/30 rounded-xl text-[#F1F5F9] placeholder-[#94A3B8] focus:outline-none focus:ring-2 focus:ring-[#7C3AED] focus:border-transparent transition-all"
                        placeholder="Enter your email"
                    />
                    {errors.email && (
                        <p className="mt-2 text-sm text-red-400">{errors.email.message}</p>
                    )}
                </div>

                {/* Password Field */}
                <div>
                    <label
                        htmlFor="password"
                        className="block text-sm font-medium text-[#F1F5F9] mb-2"
                    >
                        Password
                    </label>
                    <input
                        id="password"
                        type="password"
                        {...register("password", {
                            required: "Password is required",
                            minLength: {
                                value: 6,
                                message: "Password must be at least 6 characters",
                            },
                        })}
                        className="w-full px-4 py-3 bg-[#1E293B] border border-[#7C3AED]/30 rounded-xl text-[#F1F5F9] placeholder-[#94A3B8] focus:outline-none focus:ring-2 focus:ring-[#7C3AED] focus:border-transparent transition-all"
                        placeholder="Enter your password"
                    />
                    {errors.password && (
                        <p className="mt-2 text-sm text-red-400">
                            {errors.password.message}
                        </p>
                    )}
                </div>

                {/* Submit Button */}
                <button
                    type="submit"
                    className="w-full py-3 px-4 bg-linear-to-r from-[#5B21B6] to-[#7C3AED] text-white font-semibold rounded-xl shadow-lg shadow-[#7C3AED]/30 hover:shadow-[#7C3AED]/50 hover:scale-[1.02] transition-all focus:outline-none focus:ring-2 focus:ring-[#7C3AED]/50 cursor-pointer"
                >
                    Sign In
                </button>
            </form>

            {/* Divider */}
            <div className="my-4 flex items-center gap-4">
                <div className="flex-1 h-px bg-[#7C3AED]/20"></div>
                <span className="text-sm text-[#94A3B8]">or continue with</span>
                <div className="flex-1 h-px bg-[#7C3AED]/20"></div>
            </div>

            {/* Google OAuth */}
            <GoogleAuth
                buttonText="signin_with"
                redirectPath="/dashboard"
                onSuccess={(response) => {
                    console.log("Google login successful:", response);
                    navigate("/dashboard", true);
                }}
                onError={(error) => {
                    console.error("Google login failed:", error);
                }}
            />

            {/* Sign up link */}
            <p className="mt-2 text-center text-[#94A3B8]">
                Don't have an account?{" "}
                <button
                    onClick={() => navigate("/register")}
                    className="text-[#10B981] hover:text-[#10B981]/80 font-semibold transition-colors cursor-pointer"
                >
                    Sign up
                </button>
            </p>
        </div>
    );
}