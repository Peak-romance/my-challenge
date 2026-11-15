"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export function AuthForm({ mode }: { mode: "login" | "register" }) {
  const [identifier, setIdentifier] = useState("");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const router = useRouter();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const payload =
      mode === "register"
        ? { username, email, displayName, password }
        : { identifier, password };
    const res = await fetch(`/api/auth/${mode}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    setBusy(false);
    const data = await res.json();
    if (!res.ok) {
      setError(data.error || "操作失败");
      return;
    }
    router.push("/");
    router.refresh();
  }

  return (
    <div className="max-w-sm mx-auto mt-10 bg-white rounded-2xl border border-ink-100 shadow-soft p-6">
      <h1 className="text-xl font-bold text-ink-900 mb-1">
        {mode === "register" ? "创建账号" : "欢迎回来"}
      </h1>
      <p className="text-sm text-ink-500 mb-5">
        {mode === "register" ? "加入聚光，分享你的技术见解" : "登录以发布和互动"}
      </p>
      <form onSubmit={submit} className="space-y-3">
        {mode === "login" ? (
          <input
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
            placeholder="邮箱或用户名"
            className="w-full px-3 py-2 rounded-xl border border-ink-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-200"
          />
        ) : (
          <>
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="用户名（3-20 位字母/数字/下划线）"
              className="w-full px-3 py-2 rounded-xl border border-ink-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-200"
            />
            <input
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="邮箱"
              className="w-full px-3 py-2 rounded-xl border border-ink-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-200"
            />
            <input
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="昵称（可选，默认同用户名）"
              className="w-full px-3 py-2 rounded-xl border border-ink-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-200"
            />
          </>
        )}
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="密码（至少 6 位）"
          className="w-full px-3 py-2 rounded-xl border border-ink-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-200"
        />
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button
          type="submit"
          disabled={busy}
          className="w-full px-4 py-2 rounded-lg bg-brand-500 text-white text-sm font-medium hover:bg-brand-600 disabled:opacity-50 transition"
        >
          {mode === "register" ? "注册" : "登录"}
        </button>
      </form>
      <p className="mt-4 text-center text-sm text-ink-500">
        {mode === "register" ? (
          <>
            已有账号？{" "}
            <Link href="/login" className="text-brand-600 font-medium">
              去登录
            </Link>
          </>
        ) : (
          <>
            还没有账号？{" "}
            <Link href="/register" className="text-brand-600 font-medium">
              去注册
            </Link>
          </>
        )}
      </p>
    </div>
  );
}
