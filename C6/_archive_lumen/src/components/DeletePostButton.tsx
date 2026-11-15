"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export function DeletePostButton({ postId }: { postId: number }) {
  const [busy, setBusy] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const router = useRouter();

  async function remove() {
    if (busy) return;
    setBusy(true);
    const res = await fetch(`/api/posts/${postId}`, { method: "DELETE" });
    if (res.ok) {
      router.push("/");
      router.refresh();
    } else {
      setBusy(false);
      setConfirming(false);
      alert("删除失败");
    }
  }

  if (confirming) {
    return (
      <span className="flex items-center gap-2 text-sm">
        <button
          onClick={remove}
          disabled={busy}
          className="px-3 py-1.5 rounded-lg bg-red-500 text-white text-sm font-medium hover:bg-red-600"
        >
          确认删除
        </button>
        <button
          onClick={() => setConfirming(false)}
          className="px-3 py-1.5 rounded-lg text-sm text-ink-500 hover:bg-ink-50"
        >
          取消
        </button>
      </span>
    );
  }

  return (
    <button
      onClick={() => setConfirming(true)}
      className="px-3 py-1.5 rounded-lg text-sm text-ink-500 hover:bg-ink-50"
    >
      删除
    </button>
  );
}
