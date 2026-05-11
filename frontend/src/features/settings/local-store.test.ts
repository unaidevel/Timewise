import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import {
  COLOR_PALETTE,
  colorForDepartment,
  DEFAULT_ORG,
  DEFAULT_OT,
  getDepartmentColors,
  getOrgProfile,
  getOvertimeConfig,
  setDepartmentColor,
  setOrgProfile,
  setOvertimeConfig,
  useDepartmentColors,
  useOrgProfile,
  useOvertimeConfig,
} from "./local-store";

const TENANT = 7;

afterEach(() => {
  window.localStorage.clear();
});

describe("local-store getters", () => {
  it("returns defaults when nothing is stored", () => {
    expect(getOrgProfile(TENANT)).toEqual(DEFAULT_ORG);
    expect(getOvertimeConfig(TENANT)).toEqual(DEFAULT_OT);
    expect(getDepartmentColors(TENANT)).toEqual({});
  });

  it("merges stored partials over defaults", () => {
    window.localStorage.setItem(
      `timewise:settings:org:${TENANT}`,
      JSON.stringify({ name: "Acme", currency: "USD" }),
    );
    const org = getOrgProfile(TENANT);
    expect(org.name).toBe("Acme");
    expect(org.currency).toBe("USD");
    expect(org.country).toBe(DEFAULT_ORG.country);
  });

  it("falls back to defaults when stored JSON is malformed", () => {
    window.localStorage.setItem(`timewise:settings:ot:${TENANT}`, "{not json");
    expect(getOvertimeConfig(TENANT)).toEqual(DEFAULT_OT);
  });

  it("returns referentially-stable snapshots for unchanged keys", () => {
    const first = getOrgProfile(TENANT);
    const second = getOrgProfile(TENANT);
    expect(first).toBe(second);
  });

  it("returns a fresh reference after a write", () => {
    const first = getOrgProfile(TENANT);
    setOrgProfile(TENANT, { ...first, name: "Beta" });
    const after = getOrgProfile(TENANT);
    expect(after).not.toBe(first);
    expect(after.name).toBe("Beta");
  });

  it("isolates state across tenants", () => {
    setOrgProfile(TENANT, { ...DEFAULT_ORG, name: "Tenant 7" });
    setOrgProfile(99, { ...DEFAULT_ORG, name: "Tenant 99" });
    expect(getOrgProfile(TENANT).name).toBe("Tenant 7");
    expect(getOrgProfile(99).name).toBe("Tenant 99");
  });
});

describe("setters persist to localStorage", () => {
  it("setOrgProfile writes a JSON blob keyed by tenant", () => {
    setOrgProfile(TENANT, { ...DEFAULT_ORG, name: "Persisted" });
    const raw = window.localStorage.getItem(`timewise:settings:org:${TENANT}`);
    expect(raw && JSON.parse(raw).name).toBe("Persisted");
  });

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
  it("useOrgProfile returns the current value and updates on write", () => {
    const { result } = renderHook(() => useOrgProfile(TENANT));
    expect(result.current).toEqual(DEFAULT_ORG);

    act(() => {
      setOrgProfile(TENANT, { ...DEFAULT_ORG, name: "Updated" });
    });

    expect(result.current.name).toBe("Updated");
  });

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
