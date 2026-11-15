import { NextRequest, NextResponse } from "next/server";
import {
  listPosts,
  createPost,
  getUserByUsername,
} from "@/lib/models";
import { getSessionUser } from "@/lib/auth";

export const dynamic = "force-dynamic";

export async function GET(req: NextRequest) {
  const sp = req.nextUrl.searchParams;
  const viewer = await getSessionUser();
  const filterParam = sp.get("filter");
  const filter = filterParam === "hot" || filterParam === "following" ? filterParam : "latest";
  const tag = sp.get("tag") || undefined;
  const q = sp.get("q") || undefined;

  let authorId: number | undefined;
  const authorName = sp.get("author");
  if (authorName) authorId = getUserByUsername(authorName)?.id;

  const posts = listPosts({
    viewerId: viewer?.id ?? 0,
    filter,
    tag,
    q,
    authorId,
    limit: Math.min(Number(sp.get("limit") || 20), 50),
    offset: Number(sp.get("offset") || 0),
  });
  return NextResponse.json({ posts });
}

export async function POST(req: NextRequest) {
  const viewer = await getSessionUser();
  if (!viewer) return NextResponse.json({ error: "请先登录" }, { status: 401 });

  const body = await req.json().catch(() => ({}));
  const title = String(body.title || "").trim();
  const content = String(body.content || "").trim();
  const summary = String(body.summary || "").trim();
  const coverEmoji = String(body.coverEmoji || "✨").trim() || "✨";

  let tags: string[] = [];
  if (Array.isArray(body.tags)) tags = body.tags.map(String);
  else if (typeof body.tags === "string")
    tags = body.tags.split(/[,\s]+/).map((s: string) => s.trim()).filter(Boolean);

  if (title.length < 3) return NextResponse.json({ error: "标题至少 3 个字符" }, { status: 400 });
  if (content.length < 10) return NextResponse.json({ error: "正文至少 10 个字符" }, { status: 400 });

  const post = createPost({
    authorId: viewer.id,
    title,
    summary: summary.slice(0, 200),
    content,
    coverEmoji,
    tags: tags.slice(0, 6),
  });
  return NextResponse.json({ post }, { status: 201 });
}
