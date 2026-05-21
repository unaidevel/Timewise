import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import {
  COLOR_PALETTE,
  colorForDepartment,
  DEFAULT_OT,
  getDepartmentColors,
  getOvertimeConfig,
  setDepartmentColor,
  setOvertimeConfig,
  useDepartmentColors,
  useOvertimeConfig,
} from "./local-store";

const TENANT = 7;

afterEach(() => {
  window.localStorage.clear();
});

describe("local-store getters", () => {
  it("returns defaults when nothing is stored", () => {
    expect(getOvertimeConfig(TENANT)).toEqual(DEFAULT_OT);
    expect(getDepartmentColors(TENANT)).toEqual({});
  });

  it("falls back to defaults when stored JSON is malformed", () => {
    window.localStorage.setItem(`timewise:settings:ot:${TENANT}`, "{not json");
    expect(getOvertimeConfig(TENANT)).toEqual(DEFAULT_OT);
  });

  it("returns referentially-stable snapshots for unchanged keys", () => {
    const first = getOvertimeConfig(TENANT);
    const second = getOvertimeConfig(TENANT);
    expect(first).toBe(second);
  });

  it("returns a fresh reference after a write", () => {
    const first = getOvertimeConfig(TENANT);
    setOvertimeConfig(TENANT, { ...first, weekly_threshold: 50 });
    const after = getOvertimeConfig(TENANT);
    expect(after).not.toBe(first);
    expect(after.weekly_threshold).toBe(50);
  });
});

describe("setters persist to localStorage", () => {
  it("setOvertimeConfig writes the numeric fields", () => {
    setOvertimeConfig(TENANT, {
      weekly_threshold: 35,
      multiplier: 2,
      daily_threshold: 7,
      daily_multiplier: 1.4,
    });
    expect(getOvertimeConfig(TENANT)).toEqual({
      weekly_threshold: 35,
      multiplier: 2,
      daily_threshold: 7,
      daily_multiplier: 1.4,
    });
  });

  it("setDepartmentColor merges into the existing color map", () => {
    setDepartmentColor(TENANT, 1, "red");
    setDepartmentColor(TENANT, 2, "blue");
    expect(getDepartmentColors(TENANT)).toEqual({ 1: "red", 2: "blue" });
  });
});

describe("colorForDepartment", () => {
  it("returns the stored color when one exists", () => {
    expect(colorForDepartment({ 5: "magenta" }, 5)).toBe("magenta");
  });

  it("falls back to the palette by id when not stored", () => {
    const palette = COLOR_PALETTE;
    expect(colorForDepartment({}, 0)).toBe(palette[0]);
    expect(colorForDepartment({}, palette.length)).toBe(palette[0]);
    expect(colorForDepartment({}, palette.length + 3)).toBe(palette[3]);
  });
});

describe("hooks", () => {
  it("useOvertimeConfig returns defaults for an unknown tenant", () => {
    const { result } = renderHook(() => useOvertimeConfig(null));
    expect(result.current).toEqual(DEFAULT_OT);
  });

  it("useDepartmentColors reflects writes via setDepartmentColor", () => {
    const { result } = renderHook(() => useDepartmentColors(TENANT));
    expect(result.current).toEqual({});

    act(() => {
      setDepartmentColor(TENANT, 3, "teal");
    });

    expect(result.current).toEqual({ 3: "teal" });
  });
});
