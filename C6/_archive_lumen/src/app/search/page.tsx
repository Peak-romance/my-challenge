import Link from "next/link";
import { listPosts } from "@/lib/models";
import { getSessionUser } from "@/lib/auth";
import { PostCard } from "@/components/PostCard";

export const dynamic = "force-dynamic";

export default async function SearchPage({
  searchParams,
}: {
  searchParams: { q?: string };
}) {
  const q = (searchParams.q || "").trim();
  const viewer = await getSessionUser();
  const posts = q ? listPosts({ viewerId: viewer?.id ?? 0, q, limit: 30 }) : [];

  return (
    <div className="max-w-3xl mx-auto">
      <form action="/search" method="get" className="mb-6">
        <input
          name="q"
          defaultValue={q}
          placeholder="搜索文章标题、正文或标签…"
          className="w-full px-4 py-2.5 rounded-xl border border-ink-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-200"
        />
      </form>

      <h1 className="text-xl font-bold text-ink-900 mb-4">
        {q ? `搜索：“${q}”` : "搜索"}
      </h1>

      {!q ? (
        <p className="text-sm text-ink-400">输入关键词开始搜索。</p>
      ) : posts.length === 0 ? (
        <p className="text-sm text-ink-400">没有找到与“{q}”相关的文章。</p>
      ) : (
        <div className="space-y-4">
          {posts.map((p) => (
            <PostCard key={p.id} post={p} />
          ))}
        </div>
      )}
    </div>
  );
}
