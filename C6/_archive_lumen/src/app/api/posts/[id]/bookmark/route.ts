import { NextRequest, NextResponse } from "next/server";
import { toggleBookmark } from "@/lib/models";
import { getSessionUser } from "@/lib/auth";

export const dynamic = "force-dynamic";

export async function POST(
  _req: NextRequest,
  { params }: { params: { id: string } }
) {
  const viewer = await getSessionUser();
  if (!viewer) return NextResponse.json({ error: "请先登录" }, { status: 401 });
  const result = toggleBookmark(Number(params.id), viewer.id);
  return NextResponse.json(result);
}
