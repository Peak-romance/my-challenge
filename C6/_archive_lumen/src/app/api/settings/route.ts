import { NextRequest, NextResponse } from "next/server";
import { updateUser, publicUser } from "@/lib/models";
import { getSessionUser } from "@/lib/auth";

export const dynamic = "force-dynamic";

export async function PUT(req: NextRequest) {
  const viewer = await getSessionUser();
  if (!viewer) return NextResponse.json({ error: "请先登录" }, { status: 401 });

  const body = await req.json().catch(() => ({}));
  const display_name = typeof body.display_name === "string" ? body.display_name.trim().slice(0, 40) : undefined;
  const bio = typeof body.bio === "string" ? body.bio.trim().slice(0, 200) : undefined;
  const avatar_color = typeof body.avatar_color === "string" ? body.avatar_color : undefined;

  const user = updateUser(viewer.id, { display_name, bio, avatar_color });
  if (!user) return NextResponse.json({ error: "更新失败" }, { status: 400 });
  return NextResponse.json({ user: publicUser(user, true) });
}
