"use client";

import { useForm } from "react-hook-form";
import GoogleAuth from "./GoogleAuth";
import { navigate } from "@/lib/navigation";

type RegisterFormData = {
    email: string;
    uname: string;
    password: string;
    confirmPassword: string;
};

export default function RegisterForm() {
    const {
        register,
        handleSubmit,
        watch,
        formState: { errors },
    } = useForm<RegisterFormData>();

    const password = watch("password");

    const onSubmit = (data: RegisterFormData) => {
        console.log(data);
    };

    return (
        <div className="w-full max-w-md h-full flex flex-col justify-center">
            <div className="mb-8">
                <h2 className="text-3xl font-bold text-[#F1F5F9] mb-2">Create Account</h2>
                <p className="text-[#94A3B8]">Get started with your secure vault</p>
            </div>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
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

                {/* Username Field */}
                <div>
                    <label
                        htmlFor="uname"
                        className="block text-sm font-medium text-[#F1F5F9] mb-2"
                    >
                        Username
                    </label>
                    <input
                        id="uname"
                        type="text"
                        {...register("uname", {
                            required: "Username is required",
                            minLength: {
                                value: 3,
                                message: "Username must be at least 3 characters",
                            },
                            pattern: {
                                value: /^[a-zA-Z0-9_]+$/,
                                message: "Username can only contain letters, numbers, and underscores",
                            },
                        })}
                        className="w-full px-4 py-3 bg-[#1E293B] border border-[#7C3AED]/30 rounded-xl text-[#F1F5F9] placeholder-[#94A3B8] focus:outline-none focus:ring-2 focus:ring-[#7C3AED] focus:border-transparent transition-all"
                        placeholder="Enter your username"
                    />
                    {errors.uname && (
                        <p className="mt-2 text-sm text-red-400">{errors.uname.message}</p>
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

                {/* Confirm Password Field */}
                <div>
                    <label
                        htmlFor="confirmPassword"
                        className="block text-sm font-medium text-[#F1F5F9] mb-2"
                    >
                        Confirm Password
                    </label>
                    <input
                        id="confirmPassword"
                        type="password"
                        {...register("confirmPassword", {
                            required: "Please confirm your password",
                            validate: (value) =>
                                value === password || "Passwords do not match",
                        })}
                        className="w-full px-4 py-3 bg-[#1E293B] border border-[#7C3AED]/30 rounded-xl text-[#F1F5F9] placeholder-[#94A3B8] focus:outline-none focus:ring-2 focus:ring-[#7C3AED] focus:border-transparent transition-all"
                        placeholder="Confirm your password"
                    />
                    {errors.confirmPassword && (
                        <p className="mt-2 text-sm text-red-400">
                            {errors.confirmPassword.message}
                        </p>
                    )}
                </div>

                {/* Submit Button */}
                <button
                    type="submit"
                    className="w-full py-3 px-4 bg-linear-to-r from-[#5B21B6] to-[#7C3AED] text-white font-semibold rounded-xl shadow-lg shadow-[#7C3AED]/30 hover:shadow-[#7C3AED]/50 hover:scale-[1.02] transition-all focus:outline-none focus:ring-2 focus:ring-[#7C3AED]/50 cursor-pointer"
                >
                    Create Account
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
                buttonText="signup_with"
                redirectPath="/dashboard"
                onSuccess={(response) => {
                    console.log("Google signup successful:", response);
                    navigate("/dashboard", true);
                }}
                onError={(error) => {
                    console.error("Google signup failed:", error);
                }}
            />

            {/* Sign in link */}
            <p className="mt-2 text-center text-[#94A3B8]">
                Already have an account?{" "}
                <button
                    onClick={() => navigate("/login")}
                    className="text-[#10B981] hover:text-[#10B981]/80 font-semibold transition-colors cursor-pointer"
                >
                    Sign in
                </button>
            </p>
        </div>
    );
}