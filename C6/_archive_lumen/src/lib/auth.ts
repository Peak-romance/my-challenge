import { cookies } from "next/headers";
import { SignJWT, jwtVerify } from "jose";
import crypto from "node:crypto";
import { getUserById } from "./models";
import type { User } from "./types";

const COOKIE_NAME = "lumen_session";
const SECRET = new TextEncoder().encode(
  process.env.APP_SECRET ||
    "lumen-dev-secret-change-me-0123456789abcdefghijklmnop"
);

// ---------------------------------------------------------------------------
// Password hashing (Node built-in scrypt, no external dependency)
// ---------------------------------------------------------------------------
export function hashPassword(password: string): string {
  const salt = crypto.randomBytes(16).toString("hex");
  const hash = crypto.scryptSync(password, salt, 64).toString("hex");
  return `${salt}:${hash}`;
}

export function verifyPassword(password: string, stored: string): boolean {
  const [salt, hash] = stored.split(":");
  if (!salt || !hash) return false;
  const candidate = crypto.scryptSync(password, salt, 64).toString("hex");
  const a = Buffer.from(hash, "hex");
  const b = Buffer.from(candidate, "hex");
  return a.length === b.length && crypto.timingSafeEqual(a, b);
}

// ---------------------------------------------------------------------------
// JWT session
// ---------------------------------------------------------------------------
export async function signToken(userId: number, username: string): Promise<string> {
  return await new SignJWT({ username })
    .setProtectedHeader({ alg: "HS256" })
    .setSubject(String(userId))
    .setIssuedAt()
    .setExpirationTime("7d")
    .sign(SECRET);
}

export async function verifyToken(token: string): Promise<{ sub?: string } | null> {
  try {
    const { payload } = await jwtVerify(token, SECRET);
    return payload as { sub?: string };
  } catch {
    return null;
  }
}

// cookies() in Next 14 route handlers / server components is synchronous.
export function getSessionToken(): string | undefined {
  return cookies().get(COOKIE_NAME)?.value;
}

export async function getSessionUser(): Promise<User | null> {
  const token = getSessionToken();
  if (!token) return null;
  const payload = await verifyToken(token);
  if (!payload?.sub) return null;
  return getUserById(Number(payload.sub));
}

export function setSessionCookie(token: string): void {
  cookies().set(COOKIE_NAME, token, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: 60 * 60 * 24 * 7,
  });
}

export function clearSessionCookie(): void {
  cookies().delete(COOKIE_NAME);
}
