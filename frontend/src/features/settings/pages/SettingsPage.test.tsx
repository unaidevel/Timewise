import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { afterEach, describe, expect, it } from "vitest";
import { useAuthStore } from "@/features/auth/store";
import { useTenantStore } from "@/features/tenants/store";
import { server } from "@/test/server";
import { createRouterWrapper } from "@/test/wrapper";
import SettingsPage from "./SettingsPage";

const BASE = "http://localhost:8000";
const TENANT_ID = 1;
const USER_ID = 42;

function signInAsOwner() {
  useAuthStore.setState({
    accessToken: "token",
    refreshToken: "refresh",
    user: {
      id: USER_ID,
      email: "owner@example.com",
      full_name: "Owner",
    } as never,
  });
}

const OWNER_MEMBER = {
  id: 1,
  tenant_id: TENANT_ID,
  user_id: USER_ID,
  role: "owner",
  joined_at: "2026-01-10T00:00:00",
  invited_by_id: null,
  left_at: null,
  left_reason: null,
};

function makeOrgProfile(overrides: Record<string, unknown> = {}) {
  return {
    id: 1,
    tenant_id: TENANT_ID,
    public_name: "",
    legal_name: "",
    country: "",
    timezone: "UTC",
    currency: "EUR",
    vat_number: "",
    created_at: "2026-01-01T00:00:00",
    updated_at: "2026-01-01T00:00:00",
    ...overrides,
  };
}

function mockBaseEndpoints() {
  server.use(
    http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/departments`, () => HttpResponse.json([])),
    http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/employees`, () => HttpResponse.json([])),
    http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/members`, () => HttpResponse.json([])),
    http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/organization-profile`, () =>
      HttpResponse.json(makeOrgProfile()),
    ),
    http.get(`${BASE}/api/v1/tenants/timezones`, () =>
      HttpResponse.json([
        { value: "UTC", label: "(UTC+00:00) UTC" },
        { value: "Europe/Madrid", label: "(UTC+02:00) Europe/Madrid" },
      ]),
    ),
  );
}

afterEach(() => {
  useTenantStore.setState({ currentTenantId: null });
  useAuthStore.setState({ accessToken: null, refreshToken: null, user: null });
  window.localStorage.clear();
});

describe("SettingsPage", () => {
  it("shows the 'no tenant' state when no workspace is selected", () => {
    render(<SettingsPage />, { wrapper: createRouterWrapper() });
    expect(screen.getByText("Select a workspace")).toBeTruthy();
    expect(screen.getByRole("link", { name: /Create first organization/ })).toBeTruthy();
  });

  it("renders the four tabs and lands on the organization form by default", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    mockBaseEndpoints();

    render(<SettingsPage />, { wrapper: createRouterWrapper() });

    const orgTab = await screen.findByRole("tab", { name: /Organization/ });
    expect(screen.getByRole("tab", { name: /Departments/ })).toBeTruthy();
    expect(screen.getByRole("tab", { name: /Cost rules/ })).toBeTruthy();
    expect(screen.getByRole("tab", { name: /Members/ })).toBeTruthy();

    expect(orgTab.getAttribute("aria-selected")).toBe("true");
    expect(screen.getByText("Organization profile")).toBeTruthy();
  });

  it("sends the organization profile to the API when saved", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    signInAsOwner();
    let putBody: Record<string, unknown> | null = null;
    server.use(
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/departments`, () => HttpResponse.json([])),
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/employees`, () => HttpResponse.json([])),
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/members`, () =>
        HttpResponse.json([OWNER_MEMBER]),
      ),
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/organization-profile`, () =>
        HttpResponse.json(makeOrgProfile()),
      ),
      http.get(`${BASE}/api/v1/tenants/timezones`, () =>
        HttpResponse.json([{ value: "UTC", label: "(UTC+00:00) UTC" }]),
      ),
      http.put(`${BASE}/api/v1/tenants/${TENANT_ID}/organization-profile`, async ({ request }) => {
        putBody = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json(makeOrgProfile({ public_name: "Acme Corp" }));
      }),
    );

    render(<SettingsPage />, { wrapper: createRouterWrapper() });

    const publicNameLabel = await screen.findByText("Public name");
    const publicNameInput = publicNameLabel.parentElement?.querySelector(
      "input",
    ) as HTMLInputElement;
    expect(publicNameInput).toBeTruthy();

    await userEvent.clear(publicNameInput);
    await userEvent.type(publicNameInput, "Acme Corp");

    await userEvent.click(screen.getByRole("button", { name: /Save changes/ }));

    await waitFor(() => {
      expect(putBody).not.toBeNull();
      expect(putBody?.public_name).toBe("Acme Corp");
    });
  });

  it("shows the cost-rules empty state when there are none", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    mockBaseEndpoints();
    server.use(
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/costing/rules`, () => HttpResponse.json([])),
    );

    render(<SettingsPage />, { wrapper: createRouterWrapper() });

    await userEvent.click(await screen.findByRole("tab", { name: /Cost rules/ }));

    expect(await screen.findByText(/No cost rules/)).toBeTruthy();
  });

  it("renders members from the API on the members tab", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    server.use(
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/departments`, () => HttpResponse.json([])),
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/employees`, () =>
        HttpResponse.json([
          {
            id: 7,
            tenant_id: TENANT_ID,
            user_id: 42,
            manager_id: null,
            full_name: "Alice Liddell",
            email: "alice@example.com",
            is_active: true,
            hired_at: "2026-01-01",
            current_department_id: null,
            current_department_name: null,
            current_role_name: null,
            created_by_id: null,
            updated_by_id: null,
            created_at: "2026-01-01T00:00:00",
            updated_at: "2026-01-01T00:00:00",
          },
        ]),
      ),
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/members`, () =>
        HttpResponse.json([
          {
            id: 1,
            tenant_id: TENANT_ID,
            user_id: 42,
            role: "owner",
            joined_at: "2026-01-10T00:00:00",
            invited_by_id: null,
            left_at: null,
            left_reason: null,
          },
          {
            id: 2,
            tenant_id: TENANT_ID,
            user_id: 99,
            role: "employee",
            joined_at: "2026-01-15T00:00:00",
            invited_by_id: null,
            left_at: null,
            left_reason: null,
          },
        ]),
      ),
    );

    render(<SettingsPage />, { wrapper: createRouterWrapper() });

    await userEvent.click(await screen.findByRole("tab", { name: /Members/ }));

    expect(await screen.findByText("Alice Liddell")).toBeTruthy();
    expect(screen.getByText(/alice@example\.com/)).toBeTruthy();
    expect(screen.getByText("User #99")).toBeTruthy();
    expect(screen.getByText("owner")).toBeTruthy();
  });

  it("shows an empty state in the departments tab when there are none", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    mockBaseEndpoints();

    render(<SettingsPage />, { wrapper: createRouterWrapper() });

    await userEvent.click(await screen.findByRole("tab", { name: /Departments/ }));

    expect(await screen.findByText(/No departments yet. Create the first/)).toBeTruthy();
  });
});
