import "./globals.css";
import type { Metadata } from "next";
import { Header } from "@/components/Header";
import { getSessionUser } from "@/lib/auth";
import { publicUser } from "@/lib/models";

export const metadata: Metadata = {
  title: "聚光 Lumen · 技术内容社区",
  description: "基于 Next.js + node:sqlite 构建的真实可运行技术内容社区：发布、发现、交流技术文章。",
};

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const user = await getSessionUser();
  return (
    <html lang="zh-CN">
      <body className="min-h-screen flex flex-col">
        <Header user={user ? publicUser(user) : null} />
        <main className="mx-auto w-full max-w-5xl px-4 py-6 flex-1">{children}</main>
        <footer className="mx-auto w-full max-w-5xl px-4 py-10 text-center text-xs text-ink-400">
          聚光 Lumen · Next.js + node:sqlite 全栈内容社区
        </footer>
      </body>
    </html>
  );
}
