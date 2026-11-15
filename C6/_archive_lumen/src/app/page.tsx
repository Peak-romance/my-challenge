import Link from "next/link";
import { listPosts, getAllTags, publicUser } from "@/lib/models";
import { getSessionUser } from "@/lib/auth";
import { PostCard } from "@/components/PostCard";
import { TagPill } from "@/components/TagPill";

export const dynamic = "force-dynamic";

export default async function Home({
  searchParams,
}: {
  searchParams: { filter?: string; tag?: string; q?: string };
}) {
  const viewer = await getSessionUser();
  const viewerId = viewer?.id ?? 0;
  const filter: "latest" | "hot" | "following" =
    searchParams.filter === "hot"
      ? "hot"
      : searchParams.filter === "following"
        ? "following"
        : "latest";
  const tag = searchParams.tag;
  const q = searchParams.q;

  const posts = listPosts({ viewerId, filter, tag, q, limit: 30 });
  const tags = getAllTags();

  const params = new URLSearchParams();
  if (tag) params.set("tag", tag);
  if (q) params.set("q", q);
  const tabHref = (f: string) => {
    const p = new URLSearchParams(params.toString());
    if (f !== "latest") p.set("filter", f);
    else p.delete("filter");
    const s = p.toString();
    return s ? `/?${s}` : "/";
  };

  const heading = q
    ? `搜索：“${q}”`
    : tag
      ? `标签 #${tag}`
      : filter === "hot"
        ? "热门文章"
        : filter === "following"
          ? "关注动态"
          : "最新文章";

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_260px] gap-6">
      <div>
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-xl font-bold text-ink-900">{heading}</h1>
          <div className="flex items-center gap-1 text-sm bg-ink-50 rounded-lg p-1">
            <Link href={tabHref("latest")} className={`px-3 py-1 rounded-md ${filter === "latest" ? "bg-white shadow-soft text-ink-900 font-medium" : "text-ink-500"}`}>最新</Link>
            <Link href={tabHref("hot")} className={`px-3 py-1 rounded-md ${filter === "hot" ? "bg-white shadow-soft text-ink-900 font-medium" : "text-ink-500"}`}>热门</Link>
            <Link href={tabHref("following")} className={`px-3 py-1 rounded-md ${filter === "following" ? "bg-white shadow-soft text-ink-900 font-medium" : "text-ink-500"}`}>关注</Link>
          </div>
        </div>

        {filter === "following" && !viewer && (
          <div className="bg-brand-50 border border-brand-100 rounded-xl p-4 text-sm text-brand-800 mb-4">
            关注流展示你关注的用户发布的文章。请先 <Link href="/login" className="font-semibold underline">登录</Link>。
          </div>
        )}

        {posts.length === 0 ? (
          <div className="bg-white rounded-2xl border border-ink-100 p-10 text-center text-ink-400">
            {q || tag ? "没有找到相关文章。" : "还没有文章，"} 
            {!viewer ? (
              <Link href="/register" className="text-brand-600 font-medium"> 注册并写下第一篇</Link>
            ) : (
              <Link href="/write" className="text-brand-600 font-medium"> 去写第一篇</Link>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {posts.map((p) => (
              <PostCard key={p.id} post={p} />
            ))}
          </div>
        )}
      </div>

      <aside className="hidden lg:block">
        <div className="bg-white rounded-2xl border border-ink-100 p-4 sticky top-20">
          <h2 className="text-sm font-bold text-ink-800 mb-3">热门标签</h2>
          {tags.length === 0 ? (
            <p className="text-xs text-ink-400">暂无标签</p>
          ) : (
            <div className="flex flex-wrap gap-1.5">
              {tags.map((t) => (
                <TagPill key={t.name} name={t.name} />
              ))}
            </div>
          )}
          <div className="mt-4 pt-4 border-t border-ink-100 text-xs text-ink-400 leading-5">
            聚光 Lumen 是一个使用 Next.js App Router 与 Node 内置 SQLite 构建的全栈社区，支持发布、点赞、收藏、评论与关注。
          </div>
        </div>
      </aside>
    </div>
  );
}
