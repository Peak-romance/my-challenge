import Link from "next/link";
import { getSessionUser } from "@/lib/auth";
import { publicUser } from "@/lib/models";
import { SettingsForm } from "@/components/SettingsForm";

export const dynamic = "force-dynamic";

export default async function SettingsPage() {
  const user = await getSessionUser();
  if (!user) {
    return (
      <div className="max-w-lg mx-auto mt-16 text-center text-ink-600">
        <p>
          请先{" "}
          <Link href="/login" className="text-brand-600 font-medium">
            登录
          </Link>{" "}
          后管理账号。
        </p>
      </div>
    );
  }
  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-xl font-bold text-ink-900 mb-1">账号设置</h1>
      <p className="text-sm text-ink-500 mb-6">用户名：@{user.username}</p>
      <SettingsForm user={publicUser(user)} />
    </div>
  );
}
