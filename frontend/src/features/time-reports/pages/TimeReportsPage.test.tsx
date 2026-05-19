import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { afterEach, describe, expect, it } from "vitest";
import { useTenantStore } from "@/features/tenants/store";
import { server } from "@/test/server";
import { createRouterWrapper } from "@/test/wrapper";
import TimeReportsPage from "./TimeReportsPage";

const BASE = "http://localhost:8000";
const TENANT_ID = 1;

const periods = [
  {
    id: 10,
    tenant_id: TENANT_ID,
    name: "Enero 2026",
    start_date: "2026-01-01",
    end_date: "2026-01-31",
    status: "open",
    closed_at: null,
    created_by_id: null,
    updated_by_id: null,
    created_at: "2026-01-01T00:00:00",
    updated_at: "2026-01-01T00:00:00",
  },
];

const reports = [
  {
    id: 100,
    tenant_id: TENANT_ID,
    period_id: 10,
    employee_id: 1,
    status: "submitted",
    version: 2,
    rejection_reason: "",
    submitted_at: "2026-01-31T18:00:00",
    approved_at: null,
    rejected_at: null,
    locked_at: null,
    created_by_id: null,
    updated_by_id: null,
    created_at: "2026-01-25T00:00:00",
    updated_at: "2026-01-31T18:00:00",
  },
  {
    id: 101,
    tenant_id: TENANT_ID,
    period_id: 10,
    employee_id: 2,
    status: "approved",
    version: 1,
    rejection_reason: "",
    submitted_at: "2026-01-30T10:00:00",
    approved_at: "2026-01-31T09:00:00",
    rejected_at: null,
    locked_at: null,
    created_by_id: null,
    updated_by_id: null,
    created_at: "2026-01-20T00:00:00",
    updated_at: "2026-01-31T09:00:00",
  },
];

afterEach(() => {
  useTenantStore.setState({ currentTenantId: null });
});

describe("TimeReportsPage", () => {
  it("renders the empty state when there are no reports", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    server.use(
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/periods`, () => HttpResponse.json(periods)),
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/periods/10/reports`, () =>
        HttpResponse.json([]),
      ),
    );

    render(<TimeReportsPage />, { wrapper: createRouterWrapper() });

    expect(await screen.findByRole("heading", { name: "No reports" })).toBeTruthy();
  });

  it("lists reports across periods with status badges", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    server.use(
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/periods`, () => HttpResponse.json(periods)),
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/periods/10/reports`, () =>
        HttpResponse.json(reports),
      ),
    );

    render(<TimeReportsPage />, { wrapper: createRouterWrapper() });

    expect(await screen.findByText("#100")).toBeTruthy();
    expect(screen.getByText("#101")).toBeTruthy();
    expect(screen.getAllByText("Enero 2026").length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText(/2 total · 1 awaiting review · 1 approved/)).toBeTruthy();
  });

  it("filters reports by status select", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    server.use(
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/periods`, () => HttpResponse.json(periods)),
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/periods/10/reports`, () =>
        HttpResponse.json(reports),
      ),
    );

    render(<TimeReportsPage />, { wrapper: createRouterWrapper() });

    await screen.findByText("#100");

    await userEvent.click(screen.getByRole("combobox"));
    await userEvent.click(await screen.findByRole("option", { name: "Approved" }));

    await waitFor(() => expect(screen.queryByText("#100")).toBeNull());
    expect(screen.getByText("#101")).toBeTruthy();
  });

  it("filters reports by free-text search on the period name", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    server.use(
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/periods`, () => HttpResponse.json(periods)),
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/periods/10/reports`, () =>
        HttpResponse.json(reports),
      ),
    );

    render(<TimeReportsPage />, { wrapper: createRouterWrapper() });

    await screen.findByText("#100");

    const search = screen.getByPlaceholderText(/Search by period, ID or employee/i);
    await userEvent.type(search, "no-such-period");

    expect(await screen.findByText("No report matches the filters.")).toBeTruthy();
  });
});
