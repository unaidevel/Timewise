import { renderHook, waitFor } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import { describe, expect, it } from "vitest";
import { server } from "@/test/server";
import { createWrapper } from "@/test/wrapper";

const BASE = "http://localhost:8000";
const TENANT_ID = 1;
const EVENT_ID = 99;

const mockEvent = {
  id: EVENT_ID,
  tenant_id: TENANT_ID,
  actor_id: 7,
  action: "time_report.submitted",
  outcome: "success",
  resource_type: "TimeReport",
  resource_id: 42,
  metadata: { ip: "127.0.0.1" },
  notes: "",
  occurred_at: "2026-05-15T12:00:00Z",
};

describe("useAuditEvents", () => {
  it("fetches events for the tenant", async () => {
    server.use(
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/audit-events`, () =>
        HttpResponse.json([mockEvent]),
      ),
    );

    const { useAuditEvents } = await import("./hooks");
    const { result } = renderHook(() => useAuditEvents(TENANT_ID), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toHaveLength(1);
    expect(result.current.data?.[0].action).toBe("time_report.submitted");
  });

  it("does not fetch when tenantId is null", async () => {
    const { useAuditEvents } = await import("./hooks");
    const { result } = renderHook(() => useAuditEvents(null), {
      wrapper: createWrapper(),
    });

    await new Promise((r) => setTimeout(r, 50));
    expect(result.current.data).toBeUndefined();
    expect(result.current.fetchStatus).toBe("idle");
  });

  it("forwards filter params to the request", async () => {
    let receivedQuery: URLSearchParams | null = null;
    server.use(
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/audit-events`, ({ request }) => {
        receivedQuery = new URL(request.url).searchParams;
        return HttpResponse.json([]);
      }),
    );

    const { useAuditEvents } = await import("./hooks");
    const { result } = renderHook(
      () =>
        useAuditEvents(TENANT_ID, {
          action: "user.login",
          outcome: "failure",
          actor_id: 5,
        }),
      { wrapper: createWrapper() },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(receivedQuery!.get("action")).toBe("user.login");
    expect(receivedQuery!.get("outcome")).toBe("failure");
    expect(receivedQuery!.get("actor_id")).toBe("5");
  });
});

describe("useUpdateAuditEventNotes", () => {
  it("sends notes to the update endpoint and returns the event", async () => {
    let receivedBody: { notes?: string } | null = null;
    server.use(
      http.put(
        `${BASE}/api/v1/tenants/${TENANT_ID}/audit-events/${EVENT_ID}`,
        async ({ request }) => {
          receivedBody = (await request.json()) as { notes?: string };
          return HttpResponse.json({ ...mockEvent, notes: "investigated" });
        },
      ),
    );

    const { useUpdateAuditEventNotes } = await import("./hooks");
    const { result } = renderHook(() => useUpdateAuditEventNotes(TENANT_ID), {
      wrapper: createWrapper(),
    });

    result.current.mutate({ eventId: EVENT_ID, notes: "investigated" });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(receivedBody!.notes).toBe("investigated");
    expect(result.current.data?.notes).toBe("investigated");
  });

  it("surfaces backend errors on failure", async () => {
    server.use(
      http.put(`${BASE}/api/v1/tenants/${TENANT_ID}/audit-events/${EVENT_ID}`, () =>
        HttpResponse.json({ detail: "Forbidden" }, { status: 403 }),
      ),
    );

    const { useUpdateAuditEventNotes } = await import("./hooks");
    const { result } = renderHook(() => useUpdateAuditEventNotes(TENANT_ID), {
      wrapper: createWrapper(),
    });

    result.current.mutate({ eventId: EVENT_ID, notes: "x" });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});
