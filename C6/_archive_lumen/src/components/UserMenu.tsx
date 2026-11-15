"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import type { PublicUser } from "@/lib/types";
import { Avatar } from "./Avatar";

export function UserMenu({ user }: { user: PublicUser | null }) {
  const [open, setOpen] = useState(false);
  const router = useRouter();

  if (!user) {
    return (
      <div className="flex items-center gap-1">
        <Link
          href="/login"
          className="px-3 py-1.5 rounded-lg text-sm text-ink-700 hover:bg-ink-50"
        >
          登录
        </Link>
        <Link
          href="/register"
          className="px-3 py-1.5 rounded-lg border border-ink-200 text-sm hover:bg-ink-50"
        >
          注册
        </Link>
      </div>
    );
  }

  async function logout() {
    await fetch("/api/auth/logout", { method: "POST" });
    setOpen(false);
    router.push("/");
    router.refresh();
  }

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center"
        aria-label="用户菜单"
      >
        <Avatar user={user} size={32} />
      </button>
      {open && (
        <div
          className="absolute right-0 mt-2 w-44 bg-white border border-ink-100 rounded-xl shadow-card py-1 text-sm animate-fade-in"
          onMouseLeave={() => setOpen(false)}
        >
          <Link
            href={`/u/${user.username}`}
            onClick={() => setOpen(false)}
            className="block px-4 py-2 hover:bg-ink-50"
          >
            我的主页
          </Link>
          <Link
            href="/bookmarks"
            onClick={() => setOpen(false)}
            className="block px-4 py-2 hover:bg-ink-50"
          >
            我的收藏
          </Link>
          <Link
            href="/settings"
            onClick={() => setOpen(false)}
            className="block px-4 py-2 hover:bg-ink-50"
          >
            账号设置
          </Link>
          <button
            onClick={logout}
            className="block w-full text-left px-4 py-2 hover:bg-ink-50 text-red-600"
          >
            退出登录
          </button>
        </div>
      )}
    </div>
  );
}
