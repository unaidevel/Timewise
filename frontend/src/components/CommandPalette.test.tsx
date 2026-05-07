import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { afterEach, describe, expect, it } from "vitest";
import { useTenantStore } from "@/features/tenants/store";
import { server } from "@/test/server";
import { createRouterWrapper } from "@/test/wrapper";
import { CommandPalette } from "./CommandPalette";

const BASE = "http://localhost:8000";
const TENANT_ID = 1;

const mockEmployees = [
  {
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
  },
  {
    id: 2,
    tenant_id: TENANT_ID,
    user_id: null,
    manager_id: null,
    full_name: "James O'Connor",
    email: "james@acme.com",
    is_active: true,
    hired_at: "2024-02-10",
    created_by_id: null,
    updated_by_id: null,
    created_at: "2024-02-10T00:00:00",
    updated_at: "2024-02-10T00:00:00",
  },
];

afterEach(() => {
  useTenantStore.setState({ currentTenantId: null });
});

describe("CommandPalette", () => {
  it("does not render content when closed", () => {
    render(<CommandPalette open={false} onOpenChange={() => {}} />, {
      wrapper: createRouterWrapper(),
    });

    expect(screen.queryByPlaceholderText(/Busca personas/i)).toBeNull();
  });

  it("renders the navigation group when opened", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    server.use(
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/employees`, () => HttpResponse.json([])),
    );

    render(<CommandPalette open={true} onOpenChange={() => {}} />, {
      wrapper: createRouterWrapper(),
    });

    expect(await screen.findByText("Navegar")).toBeTruthy();
    expect(screen.getByText("Inicio")).toBeTruthy();
    expect(screen.getByText("Empleados")).toBeTruthy();
    expect(screen.getByText("Aprobaciones")).toBeTruthy();
  });

  it("lists employees when the tenant has any", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    server.use(
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/employees`, () =>
        HttpResponse.json(mockEmployees),
      ),
    );

    render(<CommandPalette open={true} onOpenChange={() => {}} />, {
      wrapper: createRouterWrapper(),
    });

    await waitFor(() => expect(screen.getByText("Maya Patel")).toBeTruthy());
    expect(screen.getByText("James O'Connor")).toBeTruthy();
    expect(screen.getByText("Empleados", { selector: "[cmdk-group-heading]" })).toBeTruthy();
  });

  it("does not render the employees group when none are returned", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    server.use(
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/employees`, () => HttpResponse.json([])),
    );

    render(<CommandPalette open={true} onOpenChange={() => {}} />, {
      wrapper: createRouterWrapper(),
    });

    await screen.findByText("Navegar");
    expect(screen.queryByText("Empleados", { selector: "[cmdk-group-heading]" })).toBeNull();
  });

  it("filters items as the user types", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    server.use(
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/employees`, () =>
        HttpResponse.json(mockEmployees),
      ),
    );

    render(<CommandPalette open={true} onOpenChange={() => {}} />, {
      wrapper: createRouterWrapper(),
    });

    await waitFor(() => expect(screen.getByText("Maya Patel")).toBeTruthy());

    const input = screen.getByPlaceholderText(/Busca personas/i);
    await userEvent.type(input, "James");

    await waitFor(() => expect(screen.queryByText("Maya Patel")).toBeNull());
    expect(screen.getByText("James O'Connor")).toBeTruthy();
  });

  it("does not fetch employees when no tenant is selected", async () => {
    useTenantStore.setState({ currentTenantId: null });

    render(<CommandPalette open={true} onOpenChange={() => {}} />, {
      wrapper: createRouterWrapper(),
    });

    await screen.findByText("Navegar");
    expect(screen.queryByText("Empleados", { selector: "[cmdk-group-heading]" })).toBeNull();
  });
});
