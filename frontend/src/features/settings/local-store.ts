import { useCallback, useSyncExternalStore } from "react";

export type OvertimeConfig = {
  weekly_threshold: number;
  multiplier: number;
  daily_threshold: number;
  daily_multiplier: number;
};

export const DEFAULT_OT: OvertimeConfig = {
  weekly_threshold: 40,
  multiplier: 1.5,
  daily_threshold: 8,
  daily_multiplier: 1.25,
};

const PREFIX = "timewise:settings";
const KEY_OT = (tenantId: number) => `${PREFIX}:ot:${tenantId}`;
const KEY_DEPT_COLOR = (tenantId: number) => `${PREFIX}:dept-colors:${tenantId}`;

const listeners = new Set<() => void>();
function emit() {
  for (const l of listeners) l();
}
function subscribe(l: () => void) {
  listeners.add(l);
  return () => listeners.delete(l);
}

// Cache parsed values per key so reads return a stable reference when the
// underlying JSON has not changed. Without this, useSyncExternalStore sees a
// new object every render and triggers an infinite update loop.
const snapshotCache = new Map<string, { raw: string | null; value: unknown }>();

function readJson<T>(key: string, fallback: T): T {
  if (typeof window === "undefined") return fallback;
  const raw = (() => {
    try {
      return window.localStorage.getItem(key);
    } catch {
      return null;
    }
  })();
  const cached = snapshotCache.get(key);
  if (cached && cached.raw === raw) return cached.value as T;
  let value: T;
  if (raw == null) {
    value = fallback;
  } else {
    try {
      value = { ...fallback, ...(JSON.parse(raw) as Partial<T>) };
    } catch {
      value = fallback;
    }
  }
  snapshotCache.set(key, { raw, value });
  return value;
}

function writeJson<T>(key: string, value: T) {
  const raw = JSON.stringify(value);
  window.localStorage.setItem(key, raw);
  snapshotCache.set(key, { raw, value });
  emit();
}

export function getOvertimeConfig(tenantId: number): OvertimeConfig {
  return readJson<OvertimeConfig>(KEY_OT(tenantId), DEFAULT_OT);
}
export function setOvertimeConfig(tenantId: number, cfg: OvertimeConfig) {
  writeJson(KEY_OT(tenantId), cfg);
}

export function getDepartmentColors(tenantId: number): Record<number, string> {
  return readJson<Record<number, string>>(KEY_DEPT_COLOR(tenantId), {});
}
export function setDepartmentColor(tenantId: number, departmentId: number, color: string) {
  const current = getDepartmentColors(tenantId);
  writeJson(KEY_DEPT_COLOR(tenantId), { ...current, [departmentId]: color });
}

const EMPTY_COLORS: Record<number, string> = {};
const getServerOt = () => DEFAULT_OT;
const getServerColors = () => EMPTY_COLORS;

export function useOvertimeConfig(tenantId: number | null): OvertimeConfig {
  const getSnapshot = useCallback(
    () => (tenantId == null ? DEFAULT_OT : getOvertimeConfig(tenantId)),
    [tenantId],
  );
  return useSyncExternalStore(subscribe, getSnapshot, getServerOt);
}

export function useDepartmentColors(tenantId: number | null): Record<number, string> {
  const getSnapshot = useCallback(
    () => (tenantId == null ? EMPTY_COLORS : getDepartmentColors(tenantId)),
    [tenantId],
  );
  return useSyncExternalStore(subscribe, getSnapshot, getServerColors);
}

export const COLOR_PALETTE = [
  "oklch(0.65 0.13 165)",
  "oklch(0.65 0.15 250)",
  "oklch(0.7 0.15 30)",
  "oklch(0.65 0.1 80)",
  "oklch(0.6 0.18 350)",
  "oklch(0.6 0.12 210)",
  "oklch(0.55 0.16 290)",
  "oklch(0.7 0.14 130)",
];

export function colorForDepartment(colors: Record<number, string>, departmentId: number): string {
  return colors[departmentId] ?? COLOR_PALETTE[departmentId % COLOR_PALETTE.length];
}
