"use client";

import { useState } from "react";
import NewItem from "@/components/home/newItem";
import AddItemModal from "@/components/home/AddItemModal";
import VaultItem from "@/components/home/VaultItem";
import ViewVaultModal from "@/components/home/ViewVaultModal";
import { Vault, ShieldCheck } from "lucide-react";

type VaultItemData = {
    id: string;
    name: string;
    content: string;
    isAdvanced: boolean;
};

export default function Home() {
    const [isAddModalOpen, setIsAddModalOpen] = useState(false);
    const [isViewModalOpen, setIsViewModalOpen] = useState(false);
    const [selectedItem, setSelectedItem] = useState<VaultItemData | null>(null);

    // Mock data - replace with actual API calls
    const [vaultItems, setVaultItems] = useState<VaultItemData[]>([
        {
            id: "1",
            name: "Bank Account Details",
            content: "Account Number: 1234567890\nIFSC: BANK0001234\nBranch: Main Street",
            isAdvanced: false,
        },
        {
            id: "2",
            name: "Private Keys",
            content: "Bitcoin Wallet Private Key:\n5Kb8kLf9zgWQnogidDA76MzPL6TsZZY36hWXMssSzNydYXYB9KF",
            isAdvanced: true,
        },
        {
            id: "3",
            name: "Password Manager",
            content: "Master Password: SuperSecurePass123!\nRecovery Email: user@example.com",
            isAdvanced: false,
        },
        {
            id: "4",
            name: "SSH Keys",
            content: "-----BEGIN OPENSSH PRIVATE KEY-----\nb3BlbnNzaC1rZXktdjEAAAAABG5vbmUA...",
            isAdvanced: true,
        },
    ]);

    const handleAddItem = (data: any) => {
        const newItem: VaultItemData = {
            id: Date.now().toString(),
            name: data.itemName,
            content: data.itemContent,
            isAdvanced: data.isAdvanced,
        };
        setVaultItems([...vaultItems, newItem]);
        // In real app, make API call here
    };

    const handleViewItem = (item: VaultItemData) => {
        setSelectedItem(item);
        setIsViewModalOpen(true);
    };

    const normalVaultItems = vaultItems.filter(item => !item.isAdvanced);
    const advancedVaultItems = vaultItems.filter(item => item.isAdvanced);

    return (
        <div className="min-h-screen w-[90%] p-6 flex items-center justify-center">
            <div className="mx-auto space-y-8 min-w-[90%]">
                {/* Header */}
                <div className="text-center space-y-2">
                    <h1 className="text-4xl font-bold text-[#F1F5F9]">
                        Secure Vault
                    </h1>
                    <p className="text-[#94A3B8]">
                        Your encrypted storage for sensitive information
                    </p>
                </div>

                {/* Add New Item Section */}
                <NewItem onClick={() => setIsAddModalOpen(true)} />

                {/* Access Vault Section */}
                <div className="space-y-6">
                    <h2 className="text-2xl font-bold text-[#F1F5F9] flex items-center gap-2">
                        <Vault className="w-7 h-7 text-[#7C3AED]" />
                        Access Vault
                    </h2>

                    <div className="grid md:grid-cols-2 gap-6">
                        {/* Normal Vault */}
                        <div className="space-y-4">
                            <div className="flex items-center gap-2 mb-4">
                                <div className="w-8 h-8 bg-[#7C3AED]/20 rounded-lg flex items-center justify-center">
                                    <Vault className="w-5 h-5 text-[#7C3AED]" />
                                </div>
                                <h3 className="text-lg font-semibold text-[#F1F5F9]">
                                    Normal Vault
                                </h3>
                                <span className="text-xs text-[#94A3B8] bg-[#1E293B] px-2 py-1 rounded-full">
                                    {normalVaultItems.length} items
                                </span>
                            </div>

                            <div className="space-y-3">
                                {normalVaultItems.length > 0 ? (
                                    normalVaultItems.map((item) => (
                                        <VaultItem
                                            key={item.id}
                                            id={item.id}
                                            name={item.name}
                                            isAdvanced={false}
                                            onClick={() => handleViewItem(item)}
                                        />
                                    ))
                                ) : (
                                    <div className="text-center p-8 bg-[#1E293B] border border-[#7C3AED]/20 rounded-xl">
                                        <p className="text-[#94A3B8] text-sm">
                                            No items in normal vault
                                        </p>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Advanced/Secured Vault */}
                        <div className="space-y-4">
                            <div className="flex items-center gap-2 mb-4">
                                <div className="w-8 h-8 bg-[#10B981]/20 rounded-lg flex items-center justify-center">
                                    <ShieldCheck className="w-5 h-5 text-[#10B981]" />
                                </div>
                                <h3 className="text-lg font-semibold text-[#F1F5F9]">
                                    Advanced Vault
                                </h3>
                                <span className="text-xs text-[#94A3B8] bg-[#1E293B] px-2 py-1 rounded-full">
                                    {advancedVaultItems.length} items
                                </span>
                            </div>

                            <div className="space-y-3">
                                {advancedVaultItems.length > 0 ? (
                                    advancedVaultItems.map((item) => (
                                        <VaultItem
                                            key={item.id}
                                            id={item.id}
                                            name={item.name}
                                            isAdvanced={true}
                                            onClick={() => handleViewItem(item)}
                                        />
                                    ))
                                ) : (
                                    <div className="text-center p-8 bg-[#1E293B] border border-[#10B981]/20 rounded-xl">
                                        <p className="text-[#94A3B8] text-sm">
                                            No items in advanced vault
                                        </p>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Modals */}
            <AddItemModal
                isOpen={isAddModalOpen}
                onClose={() => setIsAddModalOpen(false)}
                onSubmit={handleAddItem}
            />

            <ViewVaultModal
                isOpen={isViewModalOpen}
                item={selectedItem}
                onClose={() => {
                    setIsViewModalOpen(false);
                    setSelectedItem(null);
                }}
            />
        </div>
    );
}