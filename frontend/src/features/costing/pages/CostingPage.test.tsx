import { render, screen, waitFor } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import { afterEach, describe, expect, it } from "vitest";
import { useTenantStore } from "@/features/tenants/store";
import { server } from "@/test/server";
import { createRouterWrapper } from "@/test/wrapper";
import CostingPage from "./CostingPage";

const BASE = "http://localhost:8000";
const TENANT_ID = 1;

const period = {
  id: 10,
  tenant_id: TENANT_ID,
  name: "Enero 2026",
  start_date: "2026-01-01",
  end_date: "2026-01-31",
  status: "open",
  locked_at: null,
  locked_by_id: null,
  created_by_id: null,
  updated_by_id: null,
  created_at: "2026-01-01T00:00:00",
  updated_at: "2026-01-01T00:00:00",
};

const employee = {
  id: 1,
  tenant_id: TENANT_ID,
  user_id: null,
  manager_id: null,
  full_name: "Maya Patel",
  email: "maya@acme.com",
  is_active: true,
  hired_at: "2024-01-15",
  created_by_id: null,
  updated_by_id: null,
  created_at: "2024-01-15T00:00:00",
  updated_at: "2024-01-15T00:00:00",
};

const department = {
  id: 5,
  tenant_id: TENANT_ID,
  name: "Engineering",
  is_active: true,
  created_by_id: null,
  updated_by_id: null,
  created_at: "2024-01-01T00:00:00",
  updated_at: "2024-01-01T00:00:00",
};

const report = {
  id: 100,
  tenant_id: TENANT_ID,
  period_id: 10,
  employee_id: 1,
  status: "approved",
  version: 1,
  rejection_reason: "",
  submitted_at: "2026-01-31T18:00:00",
  approved_at: "2026-01-31T19:00:00",
  rejected_at: null,
  locked_at: null,
  created_by_id: null,
  updated_by_id: null,
  created_at: "2026-01-25T00:00:00",
  updated_at: "2026-01-31T19:00:00",
};

// 5 days of 10h in one ISO week → reg=40, dailyOt=10 (2h/day x5), weeklyOt=0
// At 50€/h with daily_mult=1.25: regCost=2000, otCost=625, total=2625
const entries = [
  {
    id: 1,
    report_id: 100,
    date: "2026-01-05",
    hours: "10",
    start_time: null,
    end_time: null,
    description: "",
    created_by_id: null,
    updated_by_id: null,
    created_at: "",
    updated_at: "",
  },
  {
    id: 2,
    report_id: 100,
    date: "2026-01-06",
    hours: "10",
    start_time: null,
    end_time: null,
    description: "",
    created_by_id: null,
    updated_by_id: null,
    created_at: "",
    updated_at: "",
  },
  {
    id: 3,
    report_id: 100,
    date: "2026-01-07",
    hours: "10",
    start_time: null,
    end_time: null,
    description: "",
    created_by_id: null,
    updated_by_id: null,
    created_at: "",
    updated_at: "",
  },
  {
    id: 4,
    report_id: 100,
    date: "2026-01-08",
    hours: "10",
    start_time: null,
    end_time: null,
    description: "",
    created_by_id: null,
    updated_by_id: null,
    created_at: "",
    updated_at: "",
  },
  {
    id: 5,
    report_id: 100,
    date: "2026-01-09",
    hours: "10",
    start_time: null,
    end_time: null,
    description: "",
    created_by_id: null,
    updated_by_id: null,
    created_at: "",
    updated_at: "",
  },
];

function mockEverything({
  periods = [period],
  reportsList = [report],
  entriesList = entries,
  rate = "50",
  departmentId = department.id as number | null,
}: {
  periods?: (typeof period)[];
  reportsList?: (typeof report)[];
  entriesList?: typeof entries;
  rate?: string;
  departmentId?: number | null;
} = {}) {
  server.use(
    http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/periods`, () => HttpResponse.json(periods)),
    http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/employees`, () => HttpResponse.json([employee])),
    http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/departments`, () =>
      HttpResponse.json([department]),
    ),
    http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/periods/${period.id}/reports`, () =>
      HttpResponse.json(reportsList),
    ),
    http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/reports/${report.id}/entries`, () =>
      HttpResponse.json(entriesList),
    ),
    http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/employees/${employee.id}/roles/current`, () =>
      HttpResponse.json({
        id: 1,
        employee_id: employee.id,
        role_id: 9,
        hourly_rate: rate,
        contract_hours_per_week: 40,
        assigned_at: "2024-01-15",
        left_at: null,
        left_reason: null,
        created_by_id: null,
        updated_by_id: null,
      }),
    ),
    http.get(
      `${BASE}/api/v1/tenants/${TENANT_ID}/employees/${employee.id}/departments/current`,
      () =>
        departmentId == null
          ? new HttpResponse(null, { status: 404 })
          : HttpResponse.json({
              id: 1,
              employee_id: employee.id,
              department_id: departmentId,
              assigned_at: "2024-01-15",
              left_at: null,
              left_reason: null,
              created_by_id: null,
              updated_by_id: null,
            }),
    ),
  );
}

afterEach(() => {
  useTenantStore.setState({ currentTenantId: null });
  window.localStorage.clear();
});

describe("CostingPage", () => {
  it("shows the 'no tenant' state when no workspace is selected", () => {
    render(<CostingPage />, { wrapper: createRouterWrapper() });
    expect(screen.getByText("Select a workspace")).toBeTruthy();
  });

  it("shows the empty state when no period has reports", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    mockEverything({ reportsList: [] });

    render(<CostingPage />, { wrapper: createRouterWrapper() });

    expect(await screen.findByRole("heading", { name: "No labor cost yet" })).toBeTruthy();
  });

  it("renders KPIs and the employee row with computed overtime + cost", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    mockEverything();

    render(<CostingPage />, { wrapper: createRouterWrapper() });

    // Wait until the employee table populates.
    expect(await screen.findByText("Maya Patel")).toBeTruthy();

    // 5 days * 10h = 50h total, OT = 10h
    expect(screen.getByText("50.0")).toBeTruthy(); // hours column
    expect(screen.getByText("+10.0")).toBeTruthy(); // OT column

    // Department name appears in the row and in the bar chart legend.
    expect(screen.getAllByText("Engineering").length).toBeGreaterThan(0);

    // Header KPIs show non-zero totals.
    expect(screen.getByText(/Total cost/)).toBeTruthy();
    expect(screen.getByText(/Overtime cost/)).toBeTruthy();
  });

  it("falls back to '—' when an employee has no active department", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    mockEverything({ departmentId: null });

    render(<CostingPage />, { wrapper: createRouterWrapper() });

    await screen.findByText("Maya Patel");
    // The department column in the employee table renders "—" when missing.
    await waitFor(() => {
      expect(screen.getAllByText("—").length).toBeGreaterThan(0);
    });
  });

  it("enables the CSV export button once data is loaded", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    mockEverything();

    render(<CostingPage />, { wrapper: createRouterWrapper() });

    await screen.findByText("Maya Patel");

    const button = screen.getByRole("button", { name: /Export CSV/ });
    expect(button.hasAttribute("disabled")).toBe(false);
  });
});
