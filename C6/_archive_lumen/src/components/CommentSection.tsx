"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import type { CommentWithUser, PublicUser } from "@/lib/types";
import { Avatar } from "./Avatar";
import { timeAgo } from "@/lib/format";

export function CommentSection({
  postId,
  currentUser,
}: {
  postId: number;
  currentUser: PublicUser | null;
}) {
  const [comments, setComments] = useState<CommentWithUser[]>([]);
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  async function load() {
    const res = await fetch(`/api/posts/${postId}/comments`);
    const data = await res.json();
    setComments(data.comments || []);
    setLoading(false);
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [postId]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!currentUser) {
      router.push("/login");
      return;
    }
    if (!text.trim()) return;
    const res = await fetch(`/api/posts/${postId}/comments`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content: text.trim() }),
    });
    if (res.status === 401) {
      router.push("/login");
      return;
    }
    setText("");
    load();
  }

  async function remove(id: number) {
    await fetch(`/api/comments/${id}`, { method: "DELETE" });
    load();
  }

  return (
    <section className="mt-10">
      <h3 className="text-base font-bold text-ink-900 mb-4">
        评论 {comments.length > 0 && `(${comments.length})`}
      </h3>

      <form onSubmit={submit} className="mb-6">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={currentUser ? "友善地发表你的看法…" : "登录后参与评论"}
          rows={3}
          className="w-full px-3 py-2 rounded-xl border border-ink-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-200 resize-y"
        />
        <div className="mt-2 flex justify-end">
          <button
            type="submit"
            disabled={!text.trim()}
            className="px-4 py-1.5 rounded-lg bg-brand-500 text-white text-sm font-medium hover:bg-brand-600 disabled:opacity-50 transition"
          >
            发表评论
          </button>
        </div>
      </form>

      {loading ? (
        <p className="text-sm text-ink-400">加载中…</p>
      ) : comments.length === 0 ? (
        <p className="text-sm text-ink-400">还没有评论，来抢沙发吧。</p>
      ) : (
        <ul className="space-y-4">
          {comments.map((c) => (
            <li key={c.id} className="flex gap-3">
              <Avatar user={c.user} size={32} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 text-sm">
                  <span className="font-medium text-ink-800">{c.user.display_name}</span>
                  <span className="text-ink-400 text-xs">{timeAgo(c.created_at)}</span>
                  {currentUser && currentUser.username === c.user.username && (
                    <button
                      onClick={() => remove(c.id)}
                      className="ml-auto text-xs text-ink-400 hover:text-red-500"
                    >
                      删除
                    </button>
                  )}
                </div>
                <p className="mt-1 text-sm text-ink-700 whitespace-pre-wrap break-words">
                  {c.content}
                </p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
