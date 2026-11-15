import Link from "next/link";

export function TagPill({
  name,
  active = false,
}: {
  name: string;
  active?: boolean;
}) {
  return (
    <Link
      href={`/?tag=${encodeURIComponent(name)}`}
      className={`inline-block px-2.5 py-1 rounded-full text-xs font-medium transition ${
        active
          ? "bg-brand-500 text-white"
          : "bg-brand-50 text-brand-700 hover:bg-brand-100"
      }`}
    >
      #{name}
    </Link>
  );
}
