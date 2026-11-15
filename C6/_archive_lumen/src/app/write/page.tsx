import Link from "next/link";
import { getSessionUser } from "@/lib/auth";
import { ComposeForm } from "@/components/ComposeForm";

export const dynamic = "force-dynamic";

export default async function WritePage() {
  const user = await getSessionUser();
  if (!user) {
    return (
      <div className="max-w-lg mx-auto mt-16 text-center text-ink-600">
        <p>
          请先{" "}
          <Link href="/login" className="text-brand-600 font-medium">
            登录
          </Link>{" "}
          后再发布文章。
        </p>
      </div>
    );
  }
  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-xl font-bold text-ink-900 mb-4">撰写文章</h1>
      <ComposeForm mode="create" />
    </div>
  );
}
