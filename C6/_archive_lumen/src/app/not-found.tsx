import Link from "next/link";

export default function NotFound() {
  return (
    <div className="max-w-lg mx-auto mt-20 text-center">
      <p className="text-5xl mb-4">🔍</p>
      <h1 className="text-xl font-bold text-ink-900 mb-2">页面不存在</h1>
      <p className="text-sm text-ink-500 mb-6">你访问的内容可能已被删除或链接有误。</p>
      <Link
        href="/"
        className="inline-block px-4 py-2 rounded-lg bg-brand-500 text-white text-sm font-medium hover:bg-brand-600"
      >
        返回首页
      </Link>
    </div>
  );
}
