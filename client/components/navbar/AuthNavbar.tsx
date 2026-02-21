"use client";

import Link from "next/link";

export default function AuthNavbar() {
    return (
        <div className="w-full flex items-center justify-between p-4">
            <Link href="/">Cryptrael Vault</Link>
        </div>
    );
}