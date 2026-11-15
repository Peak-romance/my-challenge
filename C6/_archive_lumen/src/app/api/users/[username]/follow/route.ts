import { NextRequest, NextResponse } from "next/server";
import { toggleFollow, getUserByUsername } from "@/lib/models";
import { getSessionUser } from "@/lib/auth";

export const dynamic = "force-dynamic";

export async function POST(
  _req: NextRequest,
  { params }: { params: { username: string } }
) {
  const viewer = await getSessionUser();
  if (!viewer) return NextResponse.json({ error: "请先登录" }, { status: 401 });

  const target = getUserByUsername(params.username);
  if (!target) return NextResponse.json({ error: "用户不存在" }, { status: 404 });
  if (target.id === viewer.id)
    return NextResponse.json({ error: "不能关注自己" }, { status: 400 });

  const result = toggleFollow(viewer.id, target.id);
  return NextResponse.json(result);
}
