import Link from "next/link";
import type { PublicUser } from "@/lib/types";
import { UserMenu } from "./UserMenu";

export function Header({ user }: { user: PublicUser | null }) {
  return (
    <header className="sticky top-0 z-30 border-b border-ink-100 bg-white/80 backdrop-blur">
      <div className="mx-auto max-w-5xl px-4 h-14 flex items-center gap-4">
        <Link href="/" className="flex items-center gap-1.5 font-extrabold text-lg shrink-0">
          <span className="text-brand-500">聚光</span>
          <span className="text-ink-400 font-medium text-sm hidden sm:inline">Lumen</span>
        </Link>
        <nav className="hidden sm:flex items-center gap-1 text-sm">
          <Link href="/?filter=latest" className="px-3 py-1.5 rounded-lg hover:bg-ink-50 text-ink-700">
            最新
          </Link>
          <Link href="/?filter=hot" className="px-3 py-1.5 rounded-lg hover:bg-ink-50 text-ink-700">
            热门
          </Link>
          <Link
            href="/?filter=following"
            className="px-3 py-1.5 rounded-lg hover:bg-ink-50 text-ink-700"
          >
            关注
          </Link>
        </nav>
        <form action="/search" method="get" className="flex-1 max-w-xs ml-auto hidden md:block">
          <input
            name="q"
            placeholder="搜索文章、标签…"
            className="w-full px-3 py-1.5 rounded-lg border border-ink-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-200"
          />
        </form>
        <div className="flex items-center gap-2 shrink-0">
          <Link
            href="/write"
            className="px-3 py-1.5 rounded-lg bg-brand-500 text-white text-sm font-medium hover:bg-brand-600 transition"
          >
            写文章
          </Link>
          <UserMenu user={user} />
        </div>
      </div>
    </header>
  );
}
