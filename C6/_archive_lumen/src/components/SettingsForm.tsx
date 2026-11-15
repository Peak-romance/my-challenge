"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import type { PublicUser } from "@/lib/types";

const COLORS = [
  "#fb8106",
  "#0ea5e9",
  "#22c55e",
  "#a855f7",
  "#ef4444",
  "#14b8a6",
  "#f59e0b",
  "#6366f1",
];

export function SettingsForm({ user }: { user: PublicUser }) {
  const [displayName, setDisplayName] = useState(user.display_name);
  const [bio, setBio] = useState(user.bio);
  const [avatarColor, setAvatarColor] = useState(user.avatar_color);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const router = useRouter();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    setMessage("");
    const res = await fetch("/api/settings", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ display_name: displayName, bio, avatar_color: avatarColor }),
    });
    setBusy(false);
    const data = await res.json();
    if (!res.ok) {
      setError(data.error || "保存失败");
      return;
    }
    setMessage("已保存");
    router.refresh();
  }

  return (
    <form onSubmit={submit} className="space-y-5 max-w-lg">
      <div>
        <label className="block text-sm font-medium text-ink-700 mb-1">昵称</label>
        <input
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
          className="w-full px-3 py-2 rounded-xl border border-ink-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-200"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-ink-700 mb-1">简介</label>
        <textarea
          value={bio}
          onChange={(e) => setBio(e.target.value)}
          rows={3}
          placeholder="介绍一下你自己…"
          className="w-full px-3 py-2 rounded-xl border border-ink-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-200 resize-y"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-ink-700 mb-1">头像颜色</label>
        <div className="flex gap-2">
          {COLORS.map((c) => (
            <button
              key={c}
              type="button"
              onClick={() => setAvatarColor(c)}
              className={`w-8 h-8 rounded-full ${avatarColor === c ? "ring-2 ring-offset-2 ring-ink-400" : ""}`}
              style={{ background: c }}
              aria-label={c}
            />
          ))}
        </div>
      </div>
      {message && <p className="text-sm text-green-600">{message}</p>}
      {error && <p className="text-sm text-red-600">{error}</p>}
      <button
        type="submit"
        disabled={busy}
        className="px-5 py-2 rounded-lg bg-brand-500 text-white text-sm font-medium hover:bg-brand-600 disabled:opacity-50 transition"
      >
        保存修改
      </button>
    </form>
  );
}
