"use client";

import { navigate } from "@/lib/navigation";
import { motion } from "framer-motion";

export default function Hero() {
    return (
        <section className="relative min-h-screen bg-linear-to-br from-[#0F172A] via-[#1E293B] to-[#0F172A] overflow-hidden">
            {/* Animated gradient blobs */}
            <div className="absolute top-0 left-10 w-96 h-96 bg-[#5B21B6] rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob"></div>
            <div className="absolute top-40 right-20 w-96 h-96 bg-[#7C3AED] rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000"></div>
            <div className="absolute bottom-20 left-1/2 w-96 h-96 bg-[#10B981] rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob animation-delay-4000"></div>

            <div className="relative max-w-7xl mx-auto px-6 pt-25 pb-24 lg:pb-32">
                <div className="grid lg:grid-cols-2 gap-12 items-center">
                    {/* Left: Text Content */}
                    <motion.div
                        initial={{ opacity: 0, y: 30 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.8 }}
                        className="space-y-8"
                    >
                        <div className="inline-flex items-center px-4 py-2 bg-[#7C3AED]/10 border border-[#7C3AED]/30 rounded-full backdrop-blur-sm">
                            <span className="text-[#10B981] text-sm font-medium">🔒 Enterprise-Grade Security</span>
                        </div>

                        <h1 className="text-5xl lg:text-7xl font-bold text-[#F1F5F9] leading-tight">
                            Unbreakable Digital Security.{" "}
                            <span className="bg-linear-to-r from-[#7C3AED] to-[#10B981] bg-clip-text text-transparent">
                                Immutable by Design.
                            </span>
                        </h1>

                        <p className="text-xl text-[#94A3B8] leading-relaxed max-w-xl">
                            Cryptrael Vault combines military-grade AES-256 encryption with blockchain-powered integrity verification.
                            Your data isn't just encrypted—it's cryptographically sealed and auditable forever.
                        </p>

                        <div className="flex flex-col sm:flex-row gap-4">
                            <motion.button
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                className="px-8 py-4 bg-linear-to-r from-[#5B21B6] to-[#7C3AED] text-white font-semibold rounded-2xl shadow-lg shadow-[#7C3AED]/30 hover:shadow-[#7C3AED]/50 transition-all"
                                onClick={() => navigate("/register")}
                            >
                                Get Started
                            </motion.button>
                            <motion.button
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                className="px-8 py-4 bg-transparent border-2 border-[#7C3AED] text-[#F1F5F9] font-semibold rounded-2xl hover:bg-[#7C3AED]/10 transition-all"
                            >
                                View Architecture
                            </motion.button>
                        </div>

                        {/* Trust Indicators */}
                        <div className="flex items-center gap-8 pt-8">
                            <div>
                                <div className="text-3xl font-bold text-[#F1F5F9]">256-bit</div>
                                <div className="text-sm text-[#94A3B8]">AES Encryption</div>
                            </div>
                            <div className="w-px h-12 bg-[#94A3B8]/20"></div>
                            <div>
                                <div className="text-3xl font-bold text-[#F1F5F9]">99.99%</div>
                                <div className="text-sm text-[#94A3B8]">Uptime SLA</div>
                            </div>
                            <div className="w-px h-12 bg-[#94A3B8]/20"></div>
                            <div>
                                <div className="text-3xl font-bold text-[#F1F5F9]">SOC 2</div>
                                <div className="text-sm text-[#94A3B8]">Compliant</div>
                            </div>
                        </div>
                    </motion.div>

                    {/* Right: Illustration */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ duration: 1, delay: 0.2 }}
                        className="relative hidden lg:block"
                    >
                        {/* Glassmorphic Vault Illustration */}
                        <div className="relative w-full h-150 flex items-center justify-center">
                            {/* Central vault */}
                            <motion.div
                                animate={{
                                    rotateY: [0, 360],
                                }}
                                transition={{
                                    duration: 20,
                                    repeat: Infinity,
                                    ease: "linear"
                                }}
                                className="relative w-72 h-72 bg-linear-to-br from-[#5B21B6]/40 to-[#7C3AED]/40 backdrop-blur-xl rounded-3xl border border-[#7C3AED]/30 shadow-2xl shadow-[#7C3AED]/20"
                                style={{ transformStyle: "preserve-3d" }}
                            >
                                {/* Lock icon */}
                                <div className="absolute inset-0 flex items-center justify-center">
                                    <svg className="w-32 h-32 text-[#10B981]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                                    </svg>
                                </div>
                            </motion.div>

                            {/* Orbiting blockchain nodes */}
                            {[...Array(6)].map((_, i) => (
                                <motion.div
                                    key={i}
                                    animate={{
                                        rotate: 360,
                                    }}
                                    transition={{
                                        duration: 15 + i * 2,
                                        repeat: Infinity,
                                        ease: "linear",
                                    }}
                                    className="absolute inset-0"
                                    style={{
                                        transformOrigin: "center",
                                    }}
                                >
                                    <div
                                        className="absolute w-12 h-12 bg-linear-to-br from-[#7C3AED] to-[#10B981] rounded-full shadow-lg shadow-[#7C3AED]/50"
                                        style={{
                                            top: `${50 + 40 * Math.sin((i * Math.PI * 2) / 6)}%`,
                                            left: `${50 + 40 * Math.cos((i * Math.PI * 2) / 6)}%`,
                                            transform: "translate(-50%, -50%)",
                                        }}
                                    >
                                        <div className="w-full h-full rounded-full border-2 border-white/20 flex items-center justify-center">
                                            <div className="w-2 h-2 bg-white rounded-full"></div>
                                        </div>
                                    </div>
                                </motion.div>
                            ))}
                        </div>
                    </motion.div>
                </div>
            </div>

            {/* Bottom gradient fade */}
            <div className="absolute bottom-0 left-0 right-0 h-32 bg-linear-to-t from-[#0F172A] to-transparent"></div>
        </section>
    );
}
