import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { beforeEach, describe, expect, it } from "vitest";
import { useTenantStore } from "@/features/tenants/store";
import { server } from "@/test/server";
import { createRouterWrapper } from "@/test/wrapper";
import { DemoDataBanner } from "./DemoDataBanner";

const BASE = "http://localhost:8000";
const TENANT_ID = 1;

function mockEmpty() {
  server.use(
    http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/departments`, () => HttpResponse.json([])),
    http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/employees`, () => HttpResponse.json([])),
  );
}

function mockNonEmpty() {
  server.use(
    http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/departments`, () =>
      HttpResponse.json([{ id: 1, name: "Engineering" }]),
    ),
    http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/employees`, () => HttpResponse.json([])),
  );
}

describe("DemoDataBanner", () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  it("does not show the modal when no tenant is selected", () => {
    useTenantStore.setState({ currentTenantId: null });

    render(<DemoDataBanner />, { wrapper: createRouterWrapper("/") });

    expect(screen.queryByText("Carga datos para ver el flujo de la app")).toBeNull();
  });

  it("does not show the modal when the tenant has data", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    mockNonEmpty();

    render(<DemoDataBanner />, { wrapper: createRouterWrapper("/") });

    await waitFor(() =>
      expect(screen.queryByText("Carga datos para ver el flujo de la app")).toBeNull(),
    );
  });

  it("shows the modal when the tenant is empty and triggers the seed on click", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    mockEmpty();
    let seedCalled = false;
    server.use(
      http.post(`${BASE}/api/v1/tenants/${TENANT_ID}/demo-data`, () => {
        seedCalled = true;
        return HttpResponse.json(
          {
            departments: 5,
            employees: 20,
            periods: 4,
            reports: 12,
            time_entries: 80,
            overtime_rules: 2,
          },
          { status: 201 },
        );
      }),
    );

    render(<DemoDataBanner />, { wrapper: createRouterWrapper("/") });

    const btn = await screen.findByRole("button", { name: "Cargar demo" });
    await userEvent.click(btn);

    await waitFor(() => expect(seedCalled).toBe(true));
  });

  it("closes the modal when the user chooses to start empty", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    mockEmpty();

    render(<DemoDataBanner />, { wrapper: createRouterWrapper("/") });

    const skip = await screen.findByRole("button", { name: "Empezar de cero" });
    await userEvent.click(skip);

    await waitFor(() =>
      expect(screen.queryByText("Carga datos para ver el flujo de la app")).toBeNull(),
    );
  });
});
