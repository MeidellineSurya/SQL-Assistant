"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { clearTokens, getRefreshToken } from "@/lib/auth";
import type { User } from "@/types";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    api
      .me()
      .then(setUser)
      .catch(() => router.replace("/login"));
  }, [router]);

  async function handleLogout() {
    const refreshToken = getRefreshToken();
    if (refreshToken) await api.logout(refreshToken).catch(() => {});
    clearTokens();
    router.push("/login");
  }

  return (
    <div className="flex min-h-screen">
      <aside className="w-56 shrink-0 border-r bg-gray-50 p-4">
        <p className="mb-6 text-sm font-semibold">SQL Assistant</p>
        <nav className="space-y-2 text-sm">
          <a href="/dashboard" className="block rounded px-2 py-1 hover:bg-gray-200">
            Dashboard
          </a>
          <a href="/connections" className="block rounded px-2 py-1 hover:bg-gray-200">
            Connections
          </a>
          <a href="/query" className="block rounded px-2 py-1 hover:bg-gray-200">
            Query
          </a>
          <a href="/history" className="block rounded px-2 py-1 hover:bg-gray-200">
            History
          </a>
        </nav>
      </aside>
      <div className="flex-1">
        <header className="flex items-center justify-between border-b px-6 py-3">
          <span className="text-sm text-gray-600">{user ? user.email : "Loading..."}</span>
          <button onClick={handleLogout} className="text-sm underline">
            Log out
          </button>
        </header>
        <main className="p-6">{children}</main>
      </div>
    </div>
  );
}
