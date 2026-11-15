import { NextResponse } from "next/server";
import { getSessionUser } from "@/lib/auth";
import { publicUser } from "@/lib/models";

export const dynamic = "force-dynamic";

export async function GET() {
  const user = await getSessionUser();
  if (!user) return NextResponse.json({ user: null });
  return NextResponse.json({ user: publicUser(user, true) });
}
