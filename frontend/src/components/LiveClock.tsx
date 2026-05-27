import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

export function useNow(intervalMs = 1000): Date {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const id = window.setInterval(() => setNow(new Date()), intervalMs);
    return () => window.clearInterval(id);
  }, [intervalMs]);
  return now;
}

export function getHourInTimezone(date: Date, timezone?: string): number {
  const hour = new Intl.DateTimeFormat("en-US", {
    hour: "numeric",
    hour12: false,
    timeZone: timezone,
  }).format(date);
  return Number.parseInt(hour, 10);
}

interface LiveClockProps {
  className?: string;
  showSeconds?: boolean;
  showDate?: boolean;
  timezone?: string;
  locale?: string;
}

export function LiveClock({
  className,
  showSeconds = true,
  showDate = true,
  timezone,
  locale,
}: LiveClockProps) {
  const now = useNow(1000);
  const parts = new Intl.DateTimeFormat(locale, {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
    timeZone: timezone,
  }).formatToParts(now);
  const get = (type: string) => parts.find((p) => p.type === type)?.value ?? "";
  const hh = get("hour");
  const mm = get("minute");
  const ss = get("second");

  const dateStr = new Intl.DateTimeFormat(locale, {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
    timeZone: timezone,
  }).format(now);

  return (
    <div className={className}>
      <div className="font-semibold tracking-tight tabular-nums leading-none flex items-baseline gap-1">
        <span>{hh}</span>
        <span className="opacity-60">:</span>
        <span>{mm}</span>
        {showSeconds && (
          <>
            <span className="opacity-60 text-[0.6em]">:</span>
            <span className="text-[0.6em] opacity-70">{ss}</span>
          </>
        )}
      </div>
      {showDate && (
        <div className={cn("text-sm text-muted-foreground mt-2 capitalize")}>{dateStr}</div>
      )}
    </div>
  );
}
