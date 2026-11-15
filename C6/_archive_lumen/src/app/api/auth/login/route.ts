import { NextRequest, NextResponse } from "next/server";
import { getUserCredential, getUserById } from "@/lib/models";
import { verifyPassword, signToken, setSessionCookie } from "@/lib/auth";

export const dynamic = "force-dynamic";

export async function POST(req: NextRequest) {
  const body = await req.json().catch(() => null);
  if (!body) return NextResponse.json({ error: "请求格式错误" }, { status: 400 });

  const identifier = String(body.identifier || "").trim();
  const password = String(body.password || "");

  const cred = getUserCredential(identifier);
  if (!cred || !verifyPassword(password, cred.password_hash))
    return NextResponse.json({ error: "用户名或密码错误" }, { status: 401 });

  const token = await signToken(cred.id, cred.username);
  setSessionCookie(token);
  const user = getUserById(cred.id);
  return NextResponse.json({ user }, { status: 200 });
}
