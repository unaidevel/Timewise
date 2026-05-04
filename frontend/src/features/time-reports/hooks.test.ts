import { renderHook, waitFor } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import { describe, expect, it } from "vitest";
import { server } from "@/test/server";
import { createWrapper } from "@/test/wrapper";

const BASE = "http://localhost:8000";
const TENANT_ID = 1;
const REPORT_ID = 42;

const mockBreakdown = {
  id: 1,
  time_entry_id: 7,
  applied_rule_name: "Overtime weekday",
  multiplier: "1.50",
  base_hours: "8.00",
  overtime_hours: "2.00",
  base_cost: "160.00",
  total_cost: "220.00",
};

const mockSummary = {
  time_report_id: REPORT_ID,
  employee_id: 3,
  total_base_hours: "8.00",
  total_overtime_hours: "2.00",
  total_base_cost: "160.00",
  total_cost: "220.00",
  breakdowns: [mockBreakdown],
};

describe("useReportCostBreakdown", () => {
  it("fetches and returns breakdown list", async () => {
    server.use(
      http.get(
        `${BASE}/api/v1/tenants/${TENANT_ID}/costing/reports/${REPORT_ID}/calculations`,
        () => HttpResponse.json([mockBreakdown]),
      ),
    );

    const { useReportCostBreakdown } = await import("./hooks");
    const { result } = renderHook(() => useReportCostBreakdown(TENANT_ID, REPORT_ID), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toHaveLength(1);
    expect(result.current.data?.[0].applied_rule_name).toBe("Overtime weekday");
    expect(result.current.data?.[0].total_cost).toBe("220.00");
  });

  it("does not fetch when tenantId is null", async () => {
    const { useReportCostBreakdown } = await import("./hooks");
    const { result } = renderHook(() => useReportCostBreakdown(null, REPORT_ID), {
      wrapper: createWrapper(),
    });

    await new Promise((r) => setTimeout(r, 50));
    expect(result.current.data).toBeUndefined();
  });

  it("does not fetch when reportId is null", async () => {
    const { useReportCostBreakdown } = await import("./hooks");
    const { result } = renderHook(() => useReportCostBreakdown(TENANT_ID, null), {
      wrapper: createWrapper(),
    });

    await new Promise((r) => setTimeout(r, 50));
    expect(result.current.data).toBeUndefined();
  });

  it("returns empty array when no calculations exist", async () => {
    server.use(
      http.get(
        `${BASE}/api/v1/tenants/${TENANT_ID}/costing/reports/${REPORT_ID}/calculations`,
        () => HttpResponse.json([]),
      ),
    );

    const { useReportCostBreakdown } = await import("./hooks");
    const { result } = renderHook(() => useReportCostBreakdown(TENANT_ID, REPORT_ID), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toHaveLength(0);
  });
});

describe("useCalculateReportCost", () => {
  it("posts to calculate endpoint and returns summary", async () => {
    server.use(
      http.post(`${BASE}/api/v1/tenants/${TENANT_ID}/costing/reports/${REPORT_ID}/calculate`, () =>
        HttpResponse.json(mockSummary),
      ),
    );

    const { useCalculateReportCost } = await import("./hooks");
    const { result } = renderHook(() => useCalculateReportCost(TENANT_ID, REPORT_ID), {
      wrapper: createWrapper(),
    });

    result.current.mutate();

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.total_cost).toBe("220.00");
    expect(result.current.data?.breakdowns).toHaveLength(1);
  });

  it("exposes isPending while the request is in flight", async () => {
    let resolve: (v: unknown) => void;
    const pending = new Promise((r) => {
      resolve = r;
    });

    server.use(
      http.post(
        `${BASE}/api/v1/tenants/${TENANT_ID}/costing/reports/${REPORT_ID}/calculate`,
        async () => {
          await pending;
          return HttpResponse.json(mockSummary);
        },
      ),
    );

    const { useCalculateReportCost } = await import("./hooks");
    const { result } = renderHook(() => useCalculateReportCost(TENANT_ID, REPORT_ID), {
      wrapper: createWrapper(),
    });

    result.current.mutate();
    await waitFor(() => expect(result.current.isPending).toBe(true));
    resolve!(undefined);
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});
