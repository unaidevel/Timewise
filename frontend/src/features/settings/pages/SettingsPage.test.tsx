import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { afterEach, describe, expect, it } from "vitest";
import { useTenantStore } from "@/features/tenants/store";
import { server } from "@/test/server";
import { createRouterWrapper } from "@/test/wrapper";
import SettingsPage from "./SettingsPage";

const BASE = "http://localhost:8000";
const TENANT_ID = 1;

function mockBaseEndpoints() {
  server.use(
    http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/departments`, () => HttpResponse.json([])),
    http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/employees`, () => HttpResponse.json([])),
    http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/members`, () => HttpResponse.json([])),
  );
}

afterEach(() => {
  useTenantStore.setState({ currentTenantId: null });
  window.localStorage.clear();
});

describe("SettingsPage", () => {
  it("shows the 'no tenant' state when no workspace is selected", () => {
    render(<SettingsPage />, { wrapper: createRouterWrapper() });
    expect(screen.getByText("Selecciona un workspace")).toBeTruthy();
    expect(screen.getByRole("link", { name: /Crear primera organización/ })).toBeTruthy();
  });

  it("renders the four tabs and lands on the organization form by default", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    mockBaseEndpoints();

    render(<SettingsPage />, { wrapper: createRouterWrapper() });

    const orgTab = await screen.findByRole("tab", { name: /Organización/ });
    expect(screen.getByRole("tab", { name: /Departamentos/ })).toBeTruthy();
    expect(screen.getByRole("tab", { name: /Horas extra/ })).toBeTruthy();
    expect(screen.getByRole("tab", { name: /Miembros/ })).toBeTruthy();

    expect(orgTab.getAttribute("aria-selected")).toBe("true");
    expect(screen.getByText("Perfil de organización")).toBeTruthy();
  });

  it("persists the organization profile to localStorage when saved", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    mockBaseEndpoints();

    render(<SettingsPage />, { wrapper: createRouterWrapper() });

    // Find the input under the "Nombre del workspace" label.
    await screen.findByText("Nombre del workspace");
    const workspaceLabel = screen.getByText("Nombre del workspace");
    const workspaceInput = workspaceLabel.parentElement?.querySelector("input") as HTMLInputElement;
    expect(workspaceInput).toBeTruthy();

    await userEvent.clear(workspaceInput);
    await userEvent.type(workspaceInput, "Acme Corp");

    await userEvent.click(screen.getByRole("button", { name: /Guardar cambios/ }));

    await waitFor(() => {
      const raw = window.localStorage.getItem(`timewise:settings:org:${TENANT_ID}`);
      expect(raw).toBeTruthy();
      const parsed = JSON.parse(raw ?? "{}");
      expect(parsed.name).toBe("Acme Corp");
    });
  });

  it("updates the overtime preview when the daily multiplier changes", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    mockBaseEndpoints();

    render(<SettingsPage />, { wrapper: createRouterWrapper() });

    await userEvent.click(await screen.findByRole("tab", { name: /Horas extra/ }));

    // With defaults (weekly=40, daily=8, weekly_mult=1.5, daily_mult=1.25):
    // dailyOt=2, weeklyOt=8, reg=40 → 40*50 + 2*50*1.25 + 8*50*1.5 = 2725
    expect(await screen.findByText(/2725/)).toBeTruthy();

    const dailyMultiplierLabel = screen.getByText("Multiplicador diario");
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

    await userEvent.click(await screen.findByRole("tab", { name: /Miembros/ }));

    expect(await screen.findByText("Usuario #42")).toBeTruthy();
    expect(screen.getByText("owner")).toBeTruthy();
  });

  it("shows an empty state in the departments tab when there are none", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    mockBaseEndpoints();

    render(<SettingsPage />, { wrapper: createRouterWrapper() });

    await userEvent.click(await screen.findByRole("tab", { name: /Departamentos/ }));

    expect(await screen.findByText(/Aún no hay departamentos. Crea el primero/)).toBeTruthy();
  });
});
