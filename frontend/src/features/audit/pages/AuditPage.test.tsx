import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { afterEach, describe, expect, it } from "vitest";
import { useAuthStore } from "@/features/auth/store";
import { useTenantStore } from "@/features/tenants/store";
import { server } from "@/test/server";
import { createRouterWrapper } from "@/test/wrapper";
import AuditPage from "./AuditPage";

const BASE = "http://localhost:8000";
const TENANT_ID = 1;
const USER_ID = 50;

const adminUser = {
  id: USER_ID,
  email: "owner@acme.test",
  full_name: "Owner User",
  is_active: true,
  created_at: "2024-01-01T00:00:00Z",
};

const adminMembership = {
  id: 1,
  tenant_id: TENANT_ID,
  user_id: USER_ID,
  role: "owner",
  joined_at: "2024-01-01T00:00:00Z",
  invited_by_id: null,
  left_at: null,
  left_reason: "",
};

const employeeMembership = {
  ...adminMembership,
  role: "employee",
};

const employee = {
  id: 7,
  tenant_id: TENANT_ID,
  user_id: USER_ID,
  manager_id: null,
  full_name: "Maya Patel",
  email: "maya@acme.test",
  is_active: true,
  hired_at: "2024-01-01",
  created_by_id: null,
  updated_by_id: null,
  created_at: "",
  updated_at: "",
};

const event = {
  id: 100,
  tenant_id: TENANT_ID,
  actor_id: 7,
  action: "time_report.submitted",
  outcome: "success",
  resource_type: "TimeReport",
  resource_id: 42,
  metadata: { ip: "127.0.0.1" },
  notes: "",
  occurred_at: "2026-05-15T10:00:00Z",
};

function mockBase({
  events = [event],
  members = [adminMembership],
  employees = [employee],
}: {
  events?: (typeof event)[];
  members?: (typeof adminMembership)[];
  employees?: (typeof employee)[];
} = {}) {
  server.use(
    http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/audit-events`, () => HttpResponse.json(events)),
    http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/members`, () => HttpResponse.json(members)),
    http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/employees`, () => HttpResponse.json(employees)),
  );
}

afterEach(() => {
  useTenantStore.setState({ currentTenantId: null });
  useAuthStore.setState({ accessToken: null, refreshToken: null, user: null });
});

describe("AuditPage", () => {
  it("shows the 'no workspace' empty state when no tenant is selected", () => {
    render(<AuditPage />, { wrapper: createRouterWrapper("/audit") });
    expect(screen.getByText("No workspace selected")).toBeTruthy();
  });

  it("lists audit events with actor name and action code", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    useAuthStore.setState({ user: adminUser, accessToken: "t", refreshToken: "r" });
    mockBase();

    render(<AuditPage />, { wrapper: createRouterWrapper("/audit") });

    expect(await screen.findByText("time_report.submitted")).toBeTruthy();
    expect(screen.getByText("Maya Patel")).toBeTruthy();
    expect(screen.getByText("1 eventos")).toBeTruthy();
  });

  it("shows a fallback label when the actor is not in the employees list", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    useAuthStore.setState({ user: adminUser, accessToken: "t", refreshToken: "r" });
    mockBase({ employees: [] });

    render(<AuditPage />, { wrapper: createRouterWrapper("/audit") });

    expect(await screen.findByText("Usuario #7")).toBeTruthy();
  });

  it("shows an empty message when no events match the filters", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    useAuthStore.setState({ user: adminUser, accessToken: "t", refreshToken: "r" });
    mockBase({ events: [] });

    render(<AuditPage />, { wrapper: createRouterWrapper("/audit") });

    expect(await screen.findByText("Ningún evento coincide con los filtros.")).toBeTruthy();
  });

  it("renders the edit-notes button for admins", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    useAuthStore.setState({ user: adminUser, accessToken: "t", refreshToken: "r" });
    mockBase();

    render(<AuditPage />, { wrapper: createRouterWrapper("/audit") });

    expect(await screen.findByRole("button", { name: "Editar notas" })).toBeTruthy();
  });

  it("hides the edit-notes button for non-admin members", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    useAuthStore.setState({ user: adminUser, accessToken: "t", refreshToken: "r" });
    mockBase({ members: [employeeMembership] });

    render(<AuditPage />, { wrapper: createRouterWrapper("/audit") });

    await screen.findByText("time_report.submitted");
    expect(screen.queryByRole("button", { name: "Editar notas" })).toBeNull();
  });

  it("forwards the action filter as a query param", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    useAuthStore.setState({ user: adminUser, accessToken: "t", refreshToken: "r" });

    let receivedAction: string | null = null;
    server.use(
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/audit-events`, ({ request }) => {
        receivedAction = new URL(request.url).searchParams.get("action");
        return HttpResponse.json([event]);
      }),
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/members`, () =>
        HttpResponse.json([adminMembership]),
      ),
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/employees`, () =>
        HttpResponse.json([employee]),
      ),
    );

    render(<AuditPage />, {
      wrapper: createRouterWrapper("/audit?action=time_report.submitted"),
    });

    await waitFor(() => expect(receivedAction).toBe("time_report.submitted"));
  });

  it("opens the edit-notes dialog when an admin clicks the pencil", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    useAuthStore.setState({ user: adminUser, accessToken: "t", refreshToken: "r" });
    mockBase();

    render(<AuditPage />, { wrapper: createRouterWrapper("/audit") });

    const btn = await screen.findByRole("button", { name: "Editar notas" });
    await userEvent.click(btn);

    expect(await screen.findByRole("heading", { name: "Editar notas" })).toBeTruthy();
  });
});
