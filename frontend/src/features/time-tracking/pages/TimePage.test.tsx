import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { afterEach, describe, expect, it } from "vitest";
import { useAuthStore } from "@/features/auth/store";
import { useTenantStore } from "@/features/tenants/store";
import { server } from "@/test/server";
import { createRouterWrapper } from "@/test/wrapper";
import TimePage from "./TimePage";

const BASE = "http://localhost:8000";
const TENANT_ID = 1;

const period = {
  id: 10,
  tenant_id: TENANT_ID,
  name: "Enero 2026",
  start_date: "2026-01-05",
  end_date: "2026-01-09",
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

const report = {
  id: 100,
  tenant_id: TENANT_ID,
  period_id: 10,
  employee_id: 1,
  status: "draft",
  version: 1,
  rejection_reason: "",
  submitted_at: null,
  approved_at: null,
  rejected_at: null,
  locked_at: null,
  created_by_id: null,
  updated_by_id: null,
  created_at: "2026-01-05T00:00:00",
  updated_at: "2026-01-05T00:00:00",
};

const entries = [
  {
    id: 1,
    report_id: 100,
    date: "2026-01-05",
    hours: "8",
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
    hours: "8",
    start_time: null,
    end_time: null,
    description: "",
    created_by_id: null,
    updated_by_id: null,
    created_at: "",
    updated_at: "",
  },
];

afterEach(() => {
  useTenantStore.setState({ currentTenantId: null });
  useAuthStore.setState({ accessToken: null, refreshToken: null, user: null });
  window.localStorage.clear();
});

describe("TimePage", () => {
  it("shows the 'no tenant' state when no workspace is selected", () => {
    render(<TimePage />, { wrapper: createRouterWrapper() });
    expect(screen.getByText("Selecciona un workspace")).toBeTruthy();
  });

  it("shows the 'no periods' empty state", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    server.use(
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/periods`, () => HttpResponse.json([])),
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/employees`, () =>
        HttpResponse.json([employee]),
      ),
    );

    render(<TimePage />, { wrapper: createRouterWrapper() });

    expect(await screen.findByRole("heading", { name: "No hay periodos abiertos" })).toBeTruthy();
  });

  it("shows the 'no employees' empty state", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    server.use(
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/periods`, () => HttpResponse.json([period])),
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/employees`, () => HttpResponse.json([])),
    );

    render(<TimePage />, { wrapper: createRouterWrapper() });

    expect(await screen.findByRole("heading", { name: "No hay empleados" })).toBeTruthy();
  });

  it("offers to create a report when the employee has none for the period", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    server.use(
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/periods`, () => HttpResponse.json([period])),
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/employees`, () =>
        HttpResponse.json([employee]),
      ),
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/periods/${period.id}/reports`, () =>
        HttpResponse.json([]),
      ),
    );

    render(<TimePage />, { wrapper: createRouterWrapper() });

    expect(await screen.findByText(/Aún no tienes un reporte para este periodo/)).toBeTruthy();
    expect(screen.getByRole("button", { name: /Crear reporte/ })).toBeTruthy();
  });

  it("renders the weekly grid with existing entries and the period total", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    server.use(
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/periods`, () => HttpResponse.json([period])),
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/employees`, () =>
        HttpResponse.json([employee]),
      ),
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/periods/${period.id}/reports`, () =>
        HttpResponse.json([report]),
      ),
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/reports/${report.id}/entries`, () =>
        HttpResponse.json(entries),
      ),
    );

    render(<TimePage />, { wrapper: createRouterWrapper() });

    expect(await screen.findByText(/Imputando horas como/)).toBeTruthy();
    expect(screen.getByText("Maya Patel")).toBeTruthy();

    // Period total reflects 8 + 8 = 16 hours (the editor has rendered by now).
    await waitFor(() => {
      expect(screen.getByText("16.00 h")).toBeTruthy();
    });

    // Status badge.
    expect(screen.getByText("draft")).toBeTruthy();
  });

  it("commits a new entry POST when an empty day cell loses focus with a value", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });

    let posted: { date: string; hours: number } | null = null;
    server.use(
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/periods`, () => HttpResponse.json([period])),
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/employees`, () =>
        HttpResponse.json([employee]),
      ),
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/periods/${period.id}/reports`, () =>
        HttpResponse.json([report]),
      ),
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/reports/${report.id}/entries`, () =>
        HttpResponse.json([]),
      ),
      http.post(
        `${BASE}/api/v1/tenants/${TENANT_ID}/reports/${report.id}/entries`,
        async ({ request }) => {
          posted = (await request.json()) as { date: string; hours: number };
          return HttpResponse.json({
            id: 99,
            report_id: report.id,
            date: posted.date,
            hours: String(posted.hours),
            start_time: null,
            end_time: null,
            description: "",
            created_by_id: null,
            updated_by_id: null,
            created_at: "",
            updated_at: "",
          });
        },
      ),
    );

    render(<TimePage />, { wrapper: createRouterWrapper() });

    // Wait for the grid to render (period total at 0).
    await screen.findByText("0.00 h");
    await waitFor(() => {
      expect(document.querySelectorAll('input[type="number"]').length).toBeGreaterThan(0);
    });

    const inputs = document.querySelectorAll<HTMLInputElement>('input[type="number"]');
    // First input corresponds to 2026-01-05 (start of the period).
    const firstDay = inputs[0];
    await userEvent.type(firstDay, "6");
    firstDay.blur();

    await waitFor(() => expect(posted).not.toBeNull());
    const body = posted as unknown as { date: string; hours: number };
    expect(body.hours).toBe(6);
    expect(body.date).toBe("2026-01-05");
  });

  it("disables the submit button when the report is not draft/rejected", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    const submittedReport = { ...report, status: "submitted" };
    server.use(
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/periods`, () => HttpResponse.json([period])),
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/employees`, () =>
        HttpResponse.json([employee]),
      ),
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/periods/${period.id}/reports`, () =>
        HttpResponse.json([submittedReport]),
      ),
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/reports/${report.id}/entries`, () =>
        HttpResponse.json(entries),
      ),
    );

    render(<TimePage />, { wrapper: createRouterWrapper() });

    const submit = await screen.findByRole("button", { name: /Enviar para aprobación/ });
    expect(submit.hasAttribute("disabled")).toBe(true);
  });
});
