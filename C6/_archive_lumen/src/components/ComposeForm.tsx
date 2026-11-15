"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Markdown } from "./Markdown";

export interface ComposeInitial {
  title: string;
  summary: string;
  content: string;
  coverEmoji: string;
  tags: string[];
}

const EMOJIS = ["✨", "🚀", "💡", "🔥", "📚", "🛠️", "🧠", "🌱", "⚡", "🎯", "🐛", "🌐"];

export function ComposeForm({
  mode,
  postId,
  initial,
}: {
  mode: "create" | "edit";
  postId?: number;
  initial?: ComposeInitial;
}) {
  const [title, setTitle] = useState(initial?.title ?? "");
  const [summary, setSummary] = useState(initial?.summary ?? "");
  const [content, setContent] = useState(initial?.content ?? "");
  const [coverEmoji, setCoverEmoji] = useState(initial?.coverEmoji ?? "✨");
  const [tags, setTags] = useState((initial?.tags ?? []).join(", "));
  const [tab, setTab] = useState<"write" | "preview">("write");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const router = useRouter();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const payload = {
      title,
      summary,
      content,
      coverEmoji,
      tags: tags
        .split(/[,\s]+/)
        .map((s) => s.trim())
        .filter(Boolean),
    };
    const url = mode === "edit" ? `/api/posts/${postId}` : "/api/posts";
    const method = mode === "edit" ? "PUT" : "POST";
    const res = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    setBusy(false);
    const data = await res.json();
    if (!res.ok) {
      setError(data.error || "提交失败");
      return;
    }
    const id = mode === "edit" ? postId : data.post.id;
    router.push(`/p/${id}`);
    router.refresh();
  }

  const canSubmit = title.trim().length >= 3 && content.trim().length >= 10 && !busy;

  return (
    <form onSubmit={submit} className="space-y-4">
      <div className="flex items-center gap-3">
        <span className="text-3xl">{coverEmoji}</span>
        <div className="flex flex-wrap gap-1">
          {EMOJIS.map((e) => (
            <button
              key={e}
              type="button"
              onClick={() => setCoverEmoji(e)}
              className={`w-8 h-8 rounded-lg text-lg ${
                coverEmoji === e ? "bg-brand-100 ring-2 ring-brand-400" : "hover:bg-ink-50"
              }`}
            >
              {e}
            </button>
          ))}
        </div>
      </div>

      <input
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="文章标题"
        className="w-full text-2xl font-bold px-3 py-2 rounded-xl border border-ink-200 focus:outline-none focus:ring-2 focus:ring-brand-200"
      />

      <input
        value={tags}
        onChange={(e) => setTags(e.target.value)}
        placeholder="标签（逗号或空格分隔，最多 6 个）"
        className="w-full px-3 py-2 rounded-xl border border-ink-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-200"
      />

      <input
        value={summary}
        onChange={(e) => setSummary(e.target.value)}
        placeholder="一句话摘要（可选，展示在信息流）"
        className="w-full px-3 py-2 rounded-xl border border-ink-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-200"
      />

      <div className="rounded-xl border border-ink-200 overflow-hidden">
        <div className="flex border-b border-ink-100 bg-ink-50 text-sm">
          <button
            type="button"
            onClick={() => setTab("write")}
            className={`px-4 py-2 ${tab === "write" ? "font-semibold text-brand-600 border-b-2 border-brand-500" : "text-ink-500"}`}
          >
            编辑
          </button>
          <button
            type="button"
            onClick={() => setTab("preview")}
            className={`px-4 py-2 ${tab === "preview" ? "font-semibold text-brand-600 border-b-2 border-brand-500" : "text-ink-500"}`}
          >
            预览
          </button>
        </div>
        {tab === "write" ? (
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="使用 Markdown 撰写正文…"
            rows={18}
            className="w-full px-4 py-3 text-sm focus:outline-none resize-y font-mono leading-6"
          />
        ) : (
          <div className="px-4 py-3 min-h-[20rem]">
            {content.trim() ? (
              <Markdown content={content} />
            ) : (
              <p className="text-ink-400 text-sm">暂无内容可预览</p>
            )}
          </div>
        )}
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="flex items-center gap-3">
        <button
          type="submit"
          disabled={!canSubmit}
          className="px-5 py-2 rounded-lg bg-brand-500 text-white text-sm font-medium hover:bg-brand-600 disabled:opacity-50 transition"
        >
          {mode === "edit" ? "保存修改" : "发布文章"}
        </button>
        <button
          type="button"
          onClick={() => router.back()}
          className="px-4 py-2 rounded-lg text-sm text-ink-600 hover:bg-ink-50"
        >
          取消
        </button>
      </div>
    </form>
  );
}
