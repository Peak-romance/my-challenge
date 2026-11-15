import type { Metadata } from "next";
import { AuthForm } from "@/components/AuthForm";

export const metadata: Metadata = { title: "登录 · 聚光 Lumen" };

export default function LoginPage() {
  return <AuthForm mode="login" />;
}
