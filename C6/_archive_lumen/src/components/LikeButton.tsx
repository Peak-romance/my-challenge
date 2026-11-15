"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export function LikeButton({
  postId,
  initialLiked,
  initialCount,
}: {
  postId: number;
  initialLiked: boolean;
  initialCount: number;
}) {
  const [liked, setLiked] = useState(initialLiked);
  const [count, setCount] = useState(initialCount);
  const [busy, setBusy] = useState(false);
  const router = useRouter();

  async function toggle(e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    if (busy) return;
    setBusy(true);
    try {
      const res = await fetch(`/api/posts/${postId}/like`, { method: "POST" });
      if (res.status === 401) {
        router.push("/login");
        return;
      }
      const data = await res.json();
      setLiked(data.liked);
      setCount(data.count);
    } finally {
      setBusy(false);
    }
  }

  return (
    <button
      onClick={toggle}
      disabled={busy}
      className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition ${
        liked ? "text-brand-600 bg-brand-50" : "text-ink-600 hover:bg-ink-50"
      }`}
    >
      <span className="text-base leading-none">{liked ? "♥" : "♡"}</span>
      <span>{count}</span>
    </button>
  );
}
