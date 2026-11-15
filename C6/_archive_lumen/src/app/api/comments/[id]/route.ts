import { NextRequest, NextResponse } from "next/server";
import { deleteComment } from "@/lib/models";
import { getSessionUser } from "@/lib/auth";

export const dynamic = "force-dynamic";

export async function DELETE(
  _req: NextRequest,
  { params }: { params: { id: string } }
) {
  const viewer = await getSessionUser();
  if (!viewer) return NextResponse.json({ error: "请先登录" }, { status: 401 });
  const ok = deleteComment(Number(params.id), viewer.id);
  if (!ok) return NextResponse.json({ error: "无权删除该评论" }, { status: 403 });
  return NextResponse.json({ ok: true });
}
