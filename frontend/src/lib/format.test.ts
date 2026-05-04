import { describe, expect, it } from "vitest";
import { formatCurrency, formatDate, formatDateTime, formatHours } from "./format";

describe("formatDate", () => {
  it("formats a valid ISO date string", () => {
    expect(formatDate("2024-06-15")).toBe("15/06/2024");
  });

  it("returns — for null", () => {
    expect(formatDate(null)).toBe("—");
  });

  it("returns — for undefined", () => {
    expect(formatDate(undefined)).toBe("—");
  });

  it("returns — for empty string", () => {
    expect(formatDate("")).toBe("—");
  });

  it("returns raw value for non-parseable string", () => {
    expect(formatDate("not-a-date")).toBe("not-a-date");
  });
});

describe("formatDateTime", () => {
  it("formats a valid ISO datetime string", () => {
    const result = formatDateTime("2024-06-15T10:30:00");
    // The output is locale-dependent; assert it contains date parts
    expect(result).toMatch(/15/);
    expect(result).toMatch(/6|06/);
  });

  it("returns — for null", () => {
    expect(formatDateTime(null)).toBe("—");
  });

  it("returns — for undefined", () => {
    expect(formatDateTime(undefined)).toBe("—");
  });

  it("returns raw value for non-parseable string", () => {
    expect(formatDateTime("bad")).toBe("bad");
  });
});

describe("formatHours", () => {
  it("formats a numeric string", () => {
    expect(formatHours("8")).toBe("8.00 h");
  });

  it("formats a float string", () => {
    expect(formatHours("8.5")).toBe("8.50 h");
  });

  it("formats a number", () => {
    expect(formatHours(2.25)).toBe("2.25 h");
  });

  it("returns — for null", () => {
    expect(formatHours(null)).toBe("—");
  });

  it("returns — for undefined", () => {
    expect(formatHours(undefined)).toBe("—");
  });

  it("returns raw string for non-numeric", () => {
    expect(formatHours("abc")).toBe("abc");
  });

  it("formats zero", () => {
    expect(formatHours(0)).toBe("0.00 h");
  });
});

describe("formatCurrency", () => {
  it("formats a numeric string as EUR", () => {
    const result = formatCurrency("1234.56");
    // Locale-dependent thousands/decimal separators; just assert number and symbol present
    expect(result).toMatch(/1.?234/);
    expect(result).toContain("€");
  });

  it("formats a number as EUR", () => {
    const result = formatCurrency(0);
    expect(result).toContain("0");
    expect(result).toContain("€");
  });

  it("returns — for null", () => {
    expect(formatCurrency(null)).toBe("—");
  });

  it("returns — for undefined", () => {
    expect(formatCurrency(undefined)).toBe("—");
  });

  it("returns raw string for non-numeric", () => {
    expect(formatCurrency("abc")).toBe("abc");
  });
});
