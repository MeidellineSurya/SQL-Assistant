"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { clearTokens } from "@/lib/auth";

export default function SettingsPage() {
  const router = useRouter();
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (newPassword !== confirmPassword) {
      setError("Passwords don't match");
      return;
    }

    setLoading(true);
    try {
      await api.changePassword(newPassword);
      // Changing the password revokes every session server-side (including
      // this one), so there's nothing valid left to stay logged in with —
      // send the user to log back in with the new password.
      clearTokens();
      router.push("/login");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-lg font-semibold">Settings</h1>

      <form onSubmit={handleSubmit} className="max-w-sm space-y-3 rounded-lg border p-4">
        <h2 className="text-sm font-semibold">Change password</h2>

        <label className="block space-y-1 text-sm">
          <span className="font-medium">New password</span>
          <input
            type="password"
            required
            minLength={8}
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            className="input"
          />
        </label>

        <label className="block space-y-1 text-sm">
          <span className="font-medium">Confirm new password</span>
          <input
            type="password"
            required
            minLength={8}
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            className="input"
          />
        </label>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="rounded bg-black px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {loading ? "Updating..." : "Update password"}
        </button>

        <p className="text-xs text-gray-500">You&apos;ll be signed out everywhere and need to log in again.</p>
      </form>
    </div>
  );
}
