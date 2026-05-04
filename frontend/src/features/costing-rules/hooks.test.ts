import { renderHook, waitFor } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import { describe, expect, it } from "vitest";
import { server } from "@/test/server";
import { createWrapper } from "@/test/wrapper";

const BASE = "http://localhost:8000";
const TENANT_ID = 1;

const mockRule = {
  id: 10,
  tenant_id: TENANT_ID,
  name: "Overtime weekday",
  multiplier: "1.50",
  priority: 1,
  is_active: true,
  conditions: [{ id: 1, condition_type: "hours_per_day", value: "8" }],
  created_by_id: null,
  updated_by_id: null,
  created_at: "2024-01-01T00:00:00",
  updated_at: "2024-01-01T00:00:00",
};

describe("useOvertimeRules", () => {
  it("fetches and returns the list of rules", async () => {
    server.use(
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/costing/rules`, () =>
        HttpResponse.json([mockRule]),
      ),
    );

    const { useOvertimeRules } = await import("./hooks");
    const { result } = renderHook(() => useOvertimeRules(TENANT_ID), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toHaveLength(1);
    expect(result.current.data?.[0].name).toBe("Overtime weekday");
  });

  it("does not fetch when tenantId is null", async () => {
    const { useOvertimeRules } = await import("./hooks");
    const { result } = renderHook(() => useOvertimeRules(null), {
      wrapper: createWrapper(),
    });

    await new Promise((r) => setTimeout(r, 50));
    expect(result.current.isLoading).toBe(false);
    expect(result.current.data).toBeUndefined();
  });
});

describe("useOvertimeRule", () => {
  it("fetches a single rule by id", async () => {
    server.use(
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/costing/rules/${mockRule.id}`, () =>
        HttpResponse.json(mockRule),
      ),
    );

    const { useOvertimeRule } = await import("./hooks");
    const { result } = renderHook(() => useOvertimeRule(TENANT_ID, mockRule.id), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.id).toBe(10);
    expect(result.current.data?.multiplier).toBe("1.50");
  });

  it("does not fetch when ruleId is null", async () => {
    const { useOvertimeRule } = await import("./hooks");
    const { result } = renderHook(() => useOvertimeRule(TENANT_ID, null), {
      wrapper: createWrapper(),
    });

    await new Promise((r) => setTimeout(r, 50));
    expect(result.current.data).toBeUndefined();
  });
});

describe("useCreateOvertimeRule", () => {
  it("posts a new rule and returns it", async () => {
    server.use(
      http.post(`${BASE}/api/v1/tenants/${TENANT_ID}/costing/rules`, () =>
        HttpResponse.json(mockRule, { status: 201 }),
      ),
    );

    const { useCreateOvertimeRule } = await import("./hooks");
    const { result } = renderHook(() => useCreateOvertimeRule(TENANT_ID), {
      wrapper: createWrapper(),
    });

    result.current.mutate({
      name: "Overtime weekday",
      multiplier: "1.5",
      priority: 1,
      conditions: [{ condition_type: "hours_per_day", value: "8" }],
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.name).toBe("Overtime weekday");
  });
});

describe("useDeactivateOvertimeRule", () => {
  it("calls DELETE and returns the deactivated rule", async () => {
    const deactivated = { ...mockRule, is_active: false };
    server.use(
      http.delete(`${BASE}/api/v1/tenants/${TENANT_ID}/costing/rules/${mockRule.id}`, () =>
        HttpResponse.json(deactivated),
      ),
    );

    const { useDeactivateOvertimeRule } = await import("./hooks");
    const { result } = renderHook(() => useDeactivateOvertimeRule(TENANT_ID), {
      wrapper: createWrapper(),
    });

    result.current.mutate(mockRule.id);

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.is_active).toBe(false);
  });
});

describe("useUpdateOvertimeRule", () => {
  it("puts updated fields and returns the rule", async () => {
    const updated = { ...mockRule, name: "Updated name", multiplier: "2.00" };
    server.use(
      http.put(`${BASE}/api/v1/tenants/${TENANT_ID}/costing/rules/${mockRule.id}`, () =>
        HttpResponse.json(updated),
      ),
    );

    const { useUpdateOvertimeRule } = await import("./hooks");
    const { result } = renderHook(() => useUpdateOvertimeRule(TENANT_ID), {
      wrapper: createWrapper(),
    });

    result.current.mutate({ id: mockRule.id, body: { name: "Updated name", multiplier: "2.00" } });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.name).toBe("Updated name");
    expect(result.current.data?.multiplier).toBe("2.00");
  });
});
