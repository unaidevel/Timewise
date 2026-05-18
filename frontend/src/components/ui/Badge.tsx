import type { ReactNode } from "react";

const tones = {
  draft: "bg-muted text-muted-foreground",
  pending: "bg-amber-500/15 text-amber-700 dark:text-amber-400",
  approved: "bg-green-500/15 text-green-700 dark:text-green-400",
  rejected: "bg-red-500/15 text-red-700 dark:text-red-400",
  locked: "bg-muted text-foreground",
  open: "bg-blue-500/15 text-blue-700 dark:text-blue-400",
  active: "bg-green-500/15 text-green-700 dark:text-green-400",
  inactive: "bg-muted text-muted-foreground",
} as const;

type Tone = keyof typeof tones;

export function Badge({ children, status }: { children: ReactNode; status?: string }) {
  const tone: Tone =
    (status?.toLowerCase() as Tone) in tones ? (status?.toLowerCase() as Tone) : "draft";
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${tones[tone]}`}
    >
      {children ?? status}
    </span>
  );
}
