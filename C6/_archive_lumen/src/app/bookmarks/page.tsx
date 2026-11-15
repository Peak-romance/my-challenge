import Link from "next/link";
import { listBookmarks } from "@/lib/models";
import { getSessionUser } from "@/lib/auth";
import { PostCard } from "@/components/PostCard";

export const dynamic = "force-dynamic";

export default async function BookmarksPage() {
  const viewer = await getSessionUser();
  if (!viewer) {
    return (
      <div className="max-w-lg mx-auto mt-16 text-center text-ink-600">
        <p>
          请先{" "}
          <Link href="/login" className="text-brand-600 font-medium">
            登录
          </Link>{" "}
          后查看收藏。
        </p>
      </div>
    );
  }
  const posts = listBookmarks(viewer.id);

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-xl font-bold text-ink-900 mb-4">我的收藏</h1>
      {posts.length === 0 ? (
        <p className="text-sm text-ink-400">你还没有收藏任何文章。</p>
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
