export type OvertimeCfg = {
  weekly_threshold: number;
  multiplier: number;
  daily_threshold: number;
  daily_multiplier: number;
};

// Group entries by ISO week (Mon-Sun) and compute daily + weekly OT.
// Daily OT counts first; weekly OT applies to the remainder above the weekly threshold
// after daily OT has already been subtracted.
export function computeOvertime(
  entries: { date: string; hours: number }[],
  cfg: OvertimeCfg,
): { regHours: number; dailyOt: number; weeklyOt: number } {
  const perDay = new Map<string, number>();
  for (const e of entries) {
    perDay.set(e.date, (perDay.get(e.date) ?? 0) + e.hours);
  }
  const perWeek = new Map<string, number[]>();
  for (const [date, hours] of perDay) {
    const key = isoWeekKey(date);
    const arr = perWeek.get(key) ?? [];
    arr.push(hours);
    perWeek.set(key, arr);
  }
  let regHours = 0;
  let dailyOt = 0;
  let weeklyOt = 0;
  for (const days of perWeek.values()) {
    let weekDailyOt = 0;
    let weekDailyReg = 0;
    for (const h of days) {
      if (h > cfg.daily_threshold) {
        weekDailyOt += h - cfg.daily_threshold;
        weekDailyReg += cfg.daily_threshold;
      } else {
        weekDailyReg += h;
      }
    }
    const overWeekly = Math.max(0, weekDailyReg - cfg.weekly_threshold);
    regHours += weekDailyReg - overWeekly;
    weeklyOt += overWeekly;
    dailyOt += weekDailyOt;
  }
  return { regHours, dailyOt, weeklyOt };
}

export function isoWeekKey(dateStr: string): string {
  const d = new Date(`${dateStr}T00:00:00Z`);
  const day = d.getUTCDay() || 7;
  d.setUTCDate(d.getUTCDate() + 4 - day);
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
  const week = Math.ceil(((d.getTime() - yearStart.getTime()) / 86400000 + 1) / 7);
  return `${d.getUTCFullYear()}-W${String(week).padStart(2, "0")}`;
}
