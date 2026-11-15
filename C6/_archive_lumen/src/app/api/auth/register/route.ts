import { NextRequest, NextResponse } from "next/server";
import { createUser, getUserByUsername, getUserByEmail } from "@/lib/models";
import { hashPassword, signToken, setSessionCookie } from "@/lib/auth";

export const dynamic = "force-dynamic";

const AVATAR_COLORS = [
  "#fb8106",
  "#0ea5e9",
  "#22c55e",
  "#a855f7",
  "#ef4444",
  "#14b8a6",
  "#f59e0b",
  "#6366f1",
];

export async function POST(req: NextRequest) {
  const body = await req.json().catch(() => null);
  if (!body) return NextResponse.json({ error: "请求格式错误" }, { status: 400 });

  const username = String(body.username || "").trim();
  const email = String(body.email || "").trim();
  const password = String(body.password || "");
  const displayName = String(body.displayName || "").trim() || username;

  if (!/^[a-zA-Z0-9_]{3,20}$/.test(username))
    return NextResponse.json({ error: "用户名需为 3-20 位字母/数字/下划线" }, { status: 400 });
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email))
    return NextResponse.json({ error: "邮箱格式不正确" }, { status: 400 });
  if (password.length < 6)
    return NextResponse.json({ error: "密码至少 6 位" }, { status: 400 });
  if (getUserByUsername(username))
    return NextResponse.json({ error: "用户名已被占用" }, { status: 409 });
  if (getUserByEmail(email))
    return NextResponse.json({ error: "邮箱已被注册" }, { status: 409 });

  const avatarColor = AVATAR_COLORS[username.length % AVATAR_COLORS.length];
  const user = createUser({
    username,
    email,
    passwordHash: hashPassword(password),
    displayName,
    avatarColor,
  });

  const token = await signToken(user.id, user.username);
  setSessionCookie(token);
  const { email: _e, ...safe } = user;
  return NextResponse.json({ user: safe }, { status: 201 });
}
