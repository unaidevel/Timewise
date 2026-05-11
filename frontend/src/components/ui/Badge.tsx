import type { ReactNode } from "react";

const tones = {
  draft: "bg-slate-100 text-slate-700",
  pending: "bg-amber-100 text-amber-800",
  approved: "bg-green-100 text-green-800",
  rejected: "bg-red-100 text-red-800",
  locked: "bg-slate-200 text-slate-700",
  open: "bg-blue-100 text-blue-800",
  active: "bg-green-100 text-green-800",
  inactive: "bg-slate-100 text-slate-500",
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
