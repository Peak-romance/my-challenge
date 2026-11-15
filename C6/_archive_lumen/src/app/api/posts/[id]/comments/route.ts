import { NextRequest, NextResponse } from "next/server";
import { listComments, addComment, getPostById } from "@/lib/models";
import { getSessionUser } from "@/lib/auth";

export const dynamic = "force-dynamic";

export async function GET(
  _req: NextRequest,
  { params }: { params: { id: string } }
) {
  const comments = listComments(Number(params.id));
  return NextResponse.json({ comments });
}

export async function POST(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  const viewer = await getSessionUser();
  if (!viewer) return NextResponse.json({ error: "请先登录" }, { status: 401 });

  const post = getPostById(Number(params.id));
  if (!post) return NextResponse.json({ error: "文章不存在" }, { status: 404 });

  const body = await req.json().catch(() => ({}));
  const content = String(body.content || "").trim();
  const parentId = body.parentId ? Number(body.parentId) : null;
  if (content.length < 1) return NextResponse.json({ error: "评论不能为空" }, { status: 400 });
  if (content.length > 1000) return NextResponse.json({ error: "评论过长" }, { status: 400 });

  const comment = addComment({
    postId: Number(params.id),
    userId: viewer.id,
    content,
    parentId,
  });
  return NextResponse.json({ comment }, { status: 201 });
}
