import { notFound } from "next/navigation";
import Link from "next/link";
import {
  getPostById,
  incrementViews,
  getRelatedPosts,
  publicUser,
} from "@/lib/models";
import { getSessionUser } from "@/lib/auth";
import { Markdown } from "@/components/Markdown";
import { Avatar } from "@/components/Avatar";
import { PostCard } from "@/components/PostCard";
import { TagPill } from "@/components/TagPill";
import { LikeButton } from "@/components/LikeButton";
import { BookmarkButton } from "@/components/BookmarkButton";
import { CommentSection } from "@/components/CommentSection";
import { DeletePostButton } from "@/components/DeletePostButton";
import { timeAgo, formatCount } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function PostPage({ params }: { params: { id: string } }) {
  const viewer = await getSessionUser();
  const id = Number(params.id);
  const post = getPostById(id, viewer?.id ?? 0);
  if (!post) notFound();

  incrementViews(id);
  const isAuthor = viewer ? viewer.id === post.author_id : false;
  const displayViews = post.views + (isAuthor ? 0 : 1);
  const related = getRelatedPosts(id, post.tags);
  const viewerPublic = viewer ? publicUser(viewer) : null;

  return (
    <article className="max-w-3xl mx-auto animate-fade-in">
      <Link href="/" className="text-sm text-ink-400 hover:text-ink-600">
        ← 返回
      </Link>

      <div className="mt-4 flex items-start gap-3">
        <span className="text-4xl leading-none mt-1 select-none">{post.cover_emoji}</span>
        <h1 className="text-2xl font-bold text-ink-900 leading-snug">{post.title}</h1>
      </div>

      <div className="mt-4 flex items-center gap-3 text-sm text-ink-500">
        <Link
          href={`/u/${post.author.username}`}
          className="flex items-center gap-2 hover:text-ink-800"
        >
          <Avatar user={post.author} size={28} />
          <span className="font-medium text-ink-700">{post.author.display_name}</span>
        </Link>
        <span>·</span>
        <span>{timeAgo(post.created_at)}</span>
        <span>·</span>
        <span>{formatCount(displayViews)} 阅读</span>
        {isAuthor && (
          <span className="ml-auto flex items-center gap-1">
            <Link
              href={`/p/${post.id}/edit`}
              className="px-3 py-1.5 rounded-lg text-sm text-ink-500 hover:bg-ink-50"
            >
              编辑
            </Link>
            <DeletePostButton postId={post.id} />
          </span>
        )}
      </div>

      <div className="mt-6">
        <Markdown content={post.content} />
      </div>

      {post.tags.length > 0 && (
        <div className="mt-6 flex flex-wrap gap-1.5">
          {post.tags.map((t) => (
            <TagPill key={t} name={t} />
          ))}
        </div>
      )}

      <div className="mt-6 flex items-center gap-2 border-y border-ink-100 py-3">
        <LikeButton
          postId={post.id}
          initialLiked={post.liked_by_viewer}
          initialCount={post.like_count}
        />
        <BookmarkButton
          postId={post.id}
          initialBookmarked={post.bookmarked_by_viewer}
          initialCount={post.bookmark_count}
        />
      </div>

      <CommentSection postId={post.id} currentUser={viewerPublic} />

      {related.length > 0 && (
        <section className="mt-10">
          <h3 className="text-base font-bold text-ink-900 mb-4">相关文章</h3>
          <div className="space-y-4">
            {related.map((r) => (
              <PostCard key={r.id} post={r} showAuthor={false} />
            ))}
          </div>
        </section>
      )}
    </article>
  );
}
