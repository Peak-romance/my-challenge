import Link from "next/link";
import type { PostWithMeta } from "@/lib/types";
import { Avatar } from "./Avatar";
import { TagPill } from "./TagPill";
import { timeAgo, formatCount } from "@/lib/format";

export function PostCard({
  post,
  showAuthor = true,
}: {
  post: PostWithMeta;
  showAuthor?: boolean;
}) {
  return (
    <article className="bg-white rounded-2xl border border-ink-100 p-5 hover:shadow-card transition shadow-soft animate-fade-in">
      <div className="flex items-start gap-4">
        <div className="text-3xl leading-none mt-1 select-none">{post.cover_emoji}</div>
        <div className="flex-1 min-w-0">
          <Link href={`/p/${post.id}`} className="block">
            <h2 className="text-lg font-bold text-ink-900 line-clamp-2 hover:text-brand-600 transition">
              {post.title}
            </h2>
          </Link>
          {post.summary && (
            <p className="mt-1 text-sm text-ink-600 line-clamp-2">{post.summary}</p>
          )}
          <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-2 text-xs text-ink-500">
            {showAuthor && (
              <Link
                href={`/u/${post.author.username}`}
                className="flex items-center gap-1.5 hover:text-ink-800"
              >
                <Avatar user={post.author} size={20} />
                <span className="font-medium text-ink-700">
                  {post.author.display_name}
                </span>
              </Link>
            )}
            <span>{timeAgo(post.created_at)}</span>
            <span>·</span>
            <span>{formatCount(post.views)} 阅读</span>
            <span>·</span>
            <span>{formatCount(post.like_count)} 赞</span>
          </div>
          {post.tags.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {post.tags.map((t) => (
                <TagPill key={t} name={t} />
              ))}
            </div>
          )}
        </div>
      </div>
    </article>
  );
}
