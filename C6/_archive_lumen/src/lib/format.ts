/** Pure formatting helpers (no Node-only dependencies, safe for any component). */

export function timeAgo(iso: string): string {
  const then = new Date(iso.replace(" ", "T") + "Z").getTime();
  if (Number.isNaN(then)) return "";
  const diff = Date.now() - then;
  const sec = Math.floor(diff / 1000);
  if (sec < 60) return "刚刚";
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min} 分钟前`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr} 小时前`;
  const day = Math.floor(hr / 24);
  if (day < 30) return `${day} 天前`;
  const mon = Math.floor(day / 30);
  if (mon < 12) return `${mon} 个月前`;
  return `${Math.floor(mon / 12)} 年前`;
}

export function formatCount(n: number): string {
  if (n < 1000) return String(n);
  if (n < 10000) return (n / 1000).toFixed(1).replace(/\.0$/, "") + "k";
  return (n / 10000).toFixed(1).replace(/\.0$/, "") + "w";
}

export function initials(name: string): string {
  const trimmed = name.trim();
  if (!trimmed) return "?";
  return trimmed[0].toUpperCase();
}
