"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export function FollowButton({
  username,
  initialFollowing,
}: {
  username: string;
  initialFollowing: boolean;
}) {
  const [following, setFollowing] = useState(initialFollowing);
  const [busy, setBusy] = useState(false);
  const router = useRouter();

  async function toggle(e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    if (busy) return;
    setBusy(true);
    try {
      const res = await fetch(`/api/users/${encodeURIComponent(username)}/follow`, {
        method: "POST",
      });
      if (res.status === 401) {
        router.push("/login");
        return;
      }
      const data = await res.json();
      setFollowing(data.following);
    } finally {
      setBusy(false);
    }
  }

  return (
    <button
      onClick={toggle}
      disabled={busy}
      className={`px-4 py-1.5 rounded-lg text-sm font-medium transition ${
        following
          ? "border border-ink-200 text-ink-600 hover:bg-ink-50"
          : "bg-brand-500 text-white hover:bg-brand-600"
      }`}
    >
      {following ? "已关注" : "+ 关注"}
    </button>
  );
}
