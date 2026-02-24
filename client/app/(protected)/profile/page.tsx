"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { User, Mail, Lock, Shield, LogOut } from "lucide-react";

export default function Profile() {
    const router = useRouter();
    const [showSignOutConfirm, setShowSignOutConfirm] = useState(false);

    // Mock data - replace with actual user data from API/context
    const userData = {
        name: "John Doe",
        email: "john.doe@example.com",
        totalItems: 4,
        advancedItems: 2,
    };

    const handleSignOut = () => {
        // Clear the authentication cookie
        document.cookie = "token=; path=/; max-age=0";
        // Redirect to login page
        router.push("/login");
    };

    return (
        <div className="min-h-screen w-full p-6">
            <div className="max-w-3xl mx-auto space-y-6">
                {/* Header */}
                <div className="text-center space-y-2 mb-8">
                    <div className="w-24 h-24 bg-linear-to-br from-[#5B21B6] to-[#7C3AED] rounded-full flex items-center justify-center mx-auto shadow-2xl shadow-[#7C3AED]/50">
                        <User className="w-12 h-12 text-white" />
                    </div>
                    <h1 className="text-3xl font-bold text-[#F1F5F9]">Profile</h1>
                    <p className="text-[#94A3B8]">Manage your account information</p>
                </div>

                {/* Profile Information Card */}
                <div className="bg-[#1E293B] border border-[#7C3AED]/30 rounded-2xl shadow-xl shadow-[#7C3AED]/10 overflow-hidden">
                    {/* User Details */}
                    <div className="p-6 space-y-6">
                        {/* Name */}
                        <div className="flex items-center gap-4 p-4 bg-[#0F172A] rounded-xl border border-[#7C3AED]/20">
                            <div className="w-12 h-12 bg-[#7C3AED]/20 rounded-lg flex items-center justify-center shrink-0">
                                <User className="w-6 h-6 text-[#7C3AED]" />
                            </div>
                            <div className="flex-1">
                                <p className="text-sm text-[#94A3B8] mb-1">Username</p>
                                <p className="text-lg font-semibold text-[#F1F5F9]">{userData.name}</p>
                            </div>
                        </div>

                        {/* Email */}
                        <div className="flex items-center gap-4 p-4 bg-[#0F172A] rounded-xl border border-[#7C3AED]/20">
                            <div className="w-12 h-12 bg-[#7C3AED]/20 rounded-lg flex items-center justify-center shrink-0">
                                <Mail className="w-6 h-6 text-[#7C3AED]" />
                            </div>
                            <div className="flex-1">
                                <p className="text-sm text-[#94A3B8] mb-1">Email</p>
                                <p className="text-lg font-semibold text-[#F1F5F9]">{userData.email}</p>
                            </div>
                        </div>
                    </div>

                    {/* Divider */}
                    <div className="border-t border-[#7C3AED]/20"></div>

                    {/* Vault Statistics */}
                    <div className="p-6">
                        <h2 className="text-xl font-bold text-[#F1F5F9] mb-4">Vault Statistics</h2>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            {/* Total Items */}
                            <div className="p-4 bg-[#0F172A] rounded-xl border border-[#7C3AED]/20">
                                <div className="flex items-center gap-3 mb-2">
                                    <div className="w-10 h-10 bg-[#7C3AED]/20 rounded-lg flex items-center justify-center">
                                        <Lock className="w-5 h-5 text-[#7C3AED]" />
                                    </div>
                                    <p className="text-sm text-[#94A3B8]">Items Secured</p>
                                </div>
                                <p className="text-3xl font-bold text-[#F1F5F9] ml-13">{userData.totalItems}</p>
                            </div>

                            {/* Advanced Items */}
                            <div className="p-4 bg-[#0F172A] rounded-xl border border-[#10B981]/20">
                                <div className="flex items-center gap-3 mb-2">
                                    <div className="w-10 h-10 bg-[#10B981]/20 rounded-lg flex items-center justify-center">
                                        <Shield className="w-5 h-5 text-[#10B981]" />
                                    </div>
                                    <p className="text-sm text-[#94A3B8]">Advanced Secured</p>
                                </div>
                                <p className="text-3xl font-bold text-[#F1F5F9] ml-13">{userData.advancedItems}</p>
                            </div>
                        </div>
                    </div>

                    {/* Divider */}
                    <div className="border-t border-[#7C3AED]/20"></div>

                    {/* Sign Out Button */}
                    <div className="p-6">
                        <button
                            onClick={() => setShowSignOutConfirm(true)}
                            className="w-full py-3 px-4 bg-red-600 hover:bg-red-700 text-white font-semibold rounded-xl shadow-lg shadow-red-600/30 hover:shadow-red-600/50 hover:scale-[1.02] transition-all focus:outline-none focus:ring-2 focus:ring-red-600/50 flex items-center justify-center gap-2 cursor-pointer"
                        >
                            <LogOut className="w-5 h-5" />
                            Sign Out
                        </button>
                    </div>
                </div>
            </div>

            {/* Sign Out Confirmation Modal */}
            {showSignOutConfirm && (
                <>
                    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-40" />
                    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
                        <div className="bg-[#1E293B] border border-red-500/30 rounded-2xl shadow-2xl shadow-red-500/20 w-full max-w-md p-6">
                            <div className="text-center mb-6">
                                <div className="w-16 h-16 bg-red-600/20 rounded-full flex items-center justify-center mx-auto mb-4">
                                    <LogOut className="w-8 h-8 text-red-500" />
                                </div>
                                <h3 className="text-2xl font-bold text-[#F1F5F9] mb-2">Sign Out?</h3>
                                <p className="text-[#94A3B8]">
                                    Are you sure you want to sign out of your account?
                                </p>
                            </div>
                            <div className="flex gap-3">
                                <button
                                    onClick={() => setShowSignOutConfirm(false)}
                                    className="flex-1 py-3 px-4 bg-[#475569] text-white font-semibold rounded-xl hover:bg-[#64748B] transition-all cursor-pointer"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleSignOut}
                                    className="flex-1 py-3 px-4 bg-red-600 text-white font-semibold rounded-xl hover:bg-red-700 transition-all cursor-pointer"
                                >
                                    Sign Out
                                </button>
                            </div>
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}