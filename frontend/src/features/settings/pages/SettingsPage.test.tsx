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
    workspace_name: "",
    country: "",
    timezone: "UTC",
    currency: "EUR",
    fiscal_year_start: "01-01",
    vat_number: "",
    default_locale: "",
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
    expect(screen.getByRole("tab", { name: /Overtime/ })).toBeTruthy();
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
        return HttpResponse.json(makeOrgProfile({ workspace_name: "Acme Corp" }));
      }),
    );

    render(<SettingsPage />, { wrapper: createRouterWrapper() });

    const workspaceLabel = await screen.findByText("Workspace name");
    const workspaceInput = workspaceLabel.parentElement?.querySelector("input") as HTMLInputElement;
    expect(workspaceInput).toBeTruthy();

    await userEvent.clear(workspaceInput);
    await userEvent.type(workspaceInput, "Acme Corp");

    await userEvent.click(screen.getByRole("button", { name: /Save changes/ }));

    await waitFor(() => {
      expect(putBody).not.toBeNull();
      expect(putBody?.workspace_name).toBe("Acme Corp");
    });
  });

  it("updates the overtime preview when the daily multiplier changes", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    mockBaseEndpoints();

    render(<SettingsPage />, { wrapper: createRouterWrapper() });

    await userEvent.click(await screen.findByRole("tab", { name: /Overtime/ }));

    // With defaults (weekly=40, daily=8, weekly_mult=1.5, daily_mult=1.25):
    // dailyOt=2, weeklyOt=8, reg=40 → 40*50 + 2*50*1.25 + 8*50*1.5 = 2725
    expect(await screen.findByText(/2725/)).toBeTruthy();

    const dailyMultiplierLabel = screen.getByText("Daily multiplier");
    const dailyMultiplier = dailyMultiplierLabel.parentElement?.querySelector(
      "input",
    ) as HTMLInputElement;
    expect(dailyMultiplier).toBeTruthy();
    await userEvent.clear(dailyMultiplier);
    await userEvent.type(dailyMultiplier, "2");

    // Now daily_mult=2: 40*50 + 2*50*2 + 8*50*1.5 = 2800
    expect(await screen.findByText(/2800/)).toBeTruthy();
  });

  it("renders members from the API on the members tab", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    server.use(
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/departments`, () => HttpResponse.json([])),
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/employees`, () => HttpResponse.json([])),
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
        ]),
      ),
    );

    render(<SettingsPage />, { wrapper: createRouterWrapper() });

    await userEvent.click(await screen.findByRole("tab", { name: /Members/ }));

    expect(await screen.findByText("User #42")).toBeTruthy();
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
