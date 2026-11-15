import type { PublicUser } from "@/lib/types";
import { initials } from "@/lib/format";

export function Avatar({
  user,
  size = 36,
  className = "",
}: {
  user: PublicUser;
  size?: number;
  className?: string;
}) {
  return (
    <span
      className={`inline-flex items-center justify-center rounded-full text-white font-semibold shrink-0 select-none ${className}`}
      style={{
        background: user.avatar_color || "#fb8106",
        width: size,
        height: size,
        fontSize: size * 0.42,
      }}
      aria-hidden
    >
      {initials(user.display_name || user.username)}
    </span>
  );
}
