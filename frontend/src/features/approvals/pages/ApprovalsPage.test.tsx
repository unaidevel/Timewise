import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useTenantStore } from "@/features/tenants/store";
import { server } from "@/test/server";
import { createRouterWrapper } from "@/test/wrapper";
import ApprovalsPage from "./ApprovalsPage";

vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

const BASE = "http://localhost:8000";
const TENANT_ID = 1;

const approvals = [
  {
    id: 1,
    tenant_id: TENANT_ID,
    report_id: 100,
    status: "pending",
    reviewer_id: null,
    reviewed_at: null,
    rejection_reason: null,
    created_by_id: null,
    updated_by_id: null,
    created_at: "2026-01-30T10:00:00",
    updated_at: "2026-01-30T10:00:00",
  },
  {
    id: 2,
    tenant_id: TENANT_ID,
    report_id: 101,
    status: "approved",
    reviewer_id: 5,
    reviewed_at: "2026-01-31T09:00:00",
    rejection_reason: null,
    created_by_id: null,
    updated_by_id: null,
    created_at: "2026-01-29T08:00:00",
    updated_at: "2026-01-31T09:00:00",
  },
  {
    id: 3,
    tenant_id: TENANT_ID,
    report_id: 102,
    status: "rejected",
    reviewer_id: 5,
    reviewed_at: "2026-01-31T11:00:00",
    rejection_reason: "Faltan horas el viernes",
    created_by_id: null,
    updated_by_id: null,
    created_at: "2026-01-28T08:00:00",
    updated_at: "2026-01-31T11:00:00",
  },
];

afterEach(() => {
  useTenantStore.setState({ currentTenantId: null });
  vi.clearAllMocks();
});

describe("ApprovalsPage", () => {
  it("renders the empty state when there are no approvals", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    server.use(
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/approvals`, () => HttpResponse.json([])),
    );

    render(<ApprovalsPage />, { wrapper: createRouterWrapper() });

    expect(await screen.findByRole("heading", { name: "Bandeja vacía" })).toBeTruthy();
  });

  it("shows pending approvals by default with action buttons", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    server.use(
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/approvals`, () => HttpResponse.json(approvals)),
    );

    render(<ApprovalsPage />, { wrapper: createRouterWrapper() });

    expect(await screen.findByText("Reporte #100")).toBeTruthy();
    expect(screen.queryByText("Reporte #101")).toBeNull();
    expect(screen.queryByText("Reporte #102")).toBeNull();
    expect(screen.getByRole("button", { name: "Aprobar" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Rechazar" })).toBeTruthy();
  });

  it("switches to approved tab and lists approved items", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    server.use(
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/approvals`, () => HttpResponse.json(approvals)),
    );

    render(<ApprovalsPage />, { wrapper: createRouterWrapper() });

    await screen.findByText("Reporte #100");

    await userEvent.click(screen.getByRole("tab", { name: /Aprobadas/ }));

    await waitFor(() => expect(screen.queryByText("Reporte #100")).toBeNull());
    expect(screen.getByText("Reporte #101")).toBeTruthy();
  });

  it("renders tab counts from the data", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    server.use(
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/approvals`, () => HttpResponse.json(approvals)),
    );

    render(<ApprovalsPage />, { wrapper: createRouterWrapper() });

    await screen.findByText("Reporte #100");

    const pendingTab = screen.getByRole("tab", { name: /Pendientes/ });
    expect(within(pendingTab).getByText("1")).toBeTruthy();
    const approvedTab = screen.getByRole("tab", { name: /Aprobadas/ });
    expect(within(approvedTab).getByText("1")).toBeTruthy();
    const rejectedTab = screen.getByRole("tab", { name: /Rechazadas/ });
    expect(within(rejectedTab).getByText("1")).toBeTruthy();
  });

  it("approves a pending item via the inline action", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    let approveCalls = 0;
    server.use(
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/approvals`, () => HttpResponse.json(approvals)),
      http.post(`${BASE}/api/v1/tenants/${TENANT_ID}/approvals/1/approve`, () => {
        approveCalls += 1;
        return HttpResponse.json({ ...approvals[0], status: "approved" });
      }),
    );

    const { toast } = await import("sonner");
    render(<ApprovalsPage />, { wrapper: createRouterWrapper() });

    await screen.findByText("Reporte #100");
    await userEvent.click(screen.getByRole("button", { name: "Aprobar" }));

    await waitFor(() => expect(approveCalls).toBe(1));
    expect(toast.success).toHaveBeenCalledWith("Reporte aprobado");
  });

  it("opens the reject sheet, submits with a reason, and posts to the API", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    let rejectBody: { reason?: string } | null = null;
    server.use(
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/approvals`, () => HttpResponse.json(approvals)),
      http.post(`${BASE}/api/v1/tenants/${TENANT_ID}/approvals/1/reject`, async ({ request }) => {
        rejectBody = (await request.json()) as { reason?: string };
        return HttpResponse.json({ ...approvals[0], status: "rejected" });
      }),
    );

    const { toast } = await import("sonner");
    render(<ApprovalsPage />, { wrapper: createRouterWrapper() });

    await screen.findByText("Reporte #100");
    await userEvent.click(screen.getByRole("button", { name: "Rechazar" }));

    const textarea = await screen.findByLabelText("Motivo (opcional)");
    await userEvent.type(textarea, "Faltan horas");

    await userEvent.click(screen.getByRole("button", { name: "Rechazar", hidden: false }));

    await waitFor(() => expect(rejectBody).not.toBeNull());
    expect(rejectBody).toEqual({ reason: "Faltan horas" });
    expect(toast.success).toHaveBeenCalledWith("Reporte rechazado");
  });

  it("shows an inbox-zero card on a tab with no items", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    server.use(
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/approvals`, () =>
        HttpResponse.json([approvals[1]]),
      ),
    );

    render(<ApprovalsPage />, { wrapper: createRouterWrapper() });

    await screen.findByRole("tab", { name: /Pendientes/ });
    expect(await screen.findByText("Nada por aquí ahora mismo.")).toBeTruthy();
  });
});
