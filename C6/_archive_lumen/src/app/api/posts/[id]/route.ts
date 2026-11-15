import { NextRequest, NextResponse } from "next/server";
import { getPostById, updatePost, deletePost } from "@/lib/models";
import { getSessionUser } from "@/lib/auth";

export const dynamic = "force-dynamic";

export async function GET(
  _req: NextRequest,
  { params }: { params: { id: string } }
) {
  const viewer = await getSessionUser();
  const post = getPostById(Number(params.id), viewer?.id ?? 0);
  if (!post) return NextResponse.json({ error: "文章不存在" }, { status: 404 });
  return NextResponse.json({ post });
}

export async function PUT(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  const viewer = await getSessionUser();
  if (!viewer) return NextResponse.json({ error: "请先登录" }, { status: 401 });

  const post = getPostById(Number(params.id));
  if (!post) return NextResponse.json({ error: "文章不存在" }, { status: 404 });
  if (post.author_id !== viewer.id)
    return NextResponse.json({ error: "无权编辑该文章" }, { status: 403 });

  const body = await req.json().catch(() => ({}));
  let tags: string[] | undefined;
  if (Array.isArray(body.tags)) tags = body.tags.map(String);
  else if (typeof body.tags === "string")
    tags = body.tags.split(/[,\s]+/).map((s: string) => s.trim()).filter(Boolean);

  const updated = updatePost(Number(params.id), {
    title: body.title,
    summary: body.summary,
    content: body.content,
    coverEmoji: body.coverEmoji,
    tags,
  });
  return NextResponse.json({ post: updated });
}

export async function DELETE(
  _req: NextRequest,
  { params }: { params: { id: string } }
) {
  const viewer = await getSessionUser();
  if (!viewer) return NextResponse.json({ error: "请先登录" }, { status: 401 });

  const post = getPostById(Number(params.id));
  if (!post) return NextResponse.json({ error: "文章不存在" }, { status: 404 });
  if (post.author_id !== viewer.id)
    return NextResponse.json({ error: "无权删除该文章" }, { status: 403 });

  deletePost(Number(params.id));
  return NextResponse.json({ ok: true });
}
