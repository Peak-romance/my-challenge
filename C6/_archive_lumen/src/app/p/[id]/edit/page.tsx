import { notFound } from "next/navigation";
import Link from "next/link";
import { getPostById } from "@/lib/models";
import { getSessionUser } from "@/lib/auth";
import { ComposeForm, type ComposeInitial } from "@/components/ComposeForm";

export const dynamic = "force-dynamic";

export default async function EditPage({ params }: { params: { id: string } }) {
  const viewer = await getSessionUser();
  if (!viewer) {
    return (
      <div className="max-w-lg mx-auto mt-16 text-center text-ink-600">
        <p>
          请先{" "}
          <Link href="/login" className="text-brand-600 font-medium">
            登录
          </Link>{" "}
          后编辑文章。
        </p>
      </div>
    );
  }

  const post = getPostById(Number(params.id));
  if (!post) notFound();
  if (post.author_id !== viewer.id) {
    return (
      <div className="max-w-lg mx-auto mt-16 text-center text-ink-600">
        无权编辑该文章。
      </div>
    );
  }

  const initial: ComposeInitial = {
    title: post.title,
    summary: post.summary,
    content: post.content,
    coverEmoji: post.cover_emoji,
    tags: post.tags,
  };

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-xl font-bold text-ink-900 mb-4">编辑文章</h1>
      <ComposeForm mode="edit" postId={post.id} initial={initial} />
    </div>
  );
}
