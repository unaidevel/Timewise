import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { afterEach, describe, expect, it } from "vitest";
import { useTenantStore } from "@/features/tenants/store";
import { server } from "@/test/server";
import { createRouterWrapper } from "@/test/wrapper";
import EmployeesPage from "./EmployeesPage";

const BASE = "http://localhost:8000";
const TENANT_ID = 1;

const employees = [
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
    is_active: false,
    hired_at: "2023-09-01",
    created_by_id: null,
    updated_by_id: null,
    created_at: "2023-09-01T00:00:00",
    updated_at: "2023-09-01T00:00:00",
  },
];

afterEach(() => {
  useTenantStore.setState({ currentTenantId: null });
});

describe("EmployeesPage", () => {
  it("renders the empty state when there are no employees", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    server.use(
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/employees`, () => HttpResponse.json([])),
    );

    render(<EmployeesPage />, { wrapper: createRouterWrapper() });

    expect(await screen.findByRole("heading", { name: "No employees" })).toBeTruthy();
    expect(screen.getByText(/Add the first employee/i)).toBeTruthy();
  });

  it("lists employees with their status badges", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    server.use(
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/employees`, () => HttpResponse.json(employees)),
    );

    render(<EmployeesPage />, { wrapper: createRouterWrapper() });

    expect(await screen.findByRole("link", { name: "Maya Patel" })).toBeTruthy();
    expect(screen.getByRole("link", { name: "James O'Connor" })).toBeTruthy();
    expect(screen.getByText(/2 on staff · 1 active/)).toBeTruthy();
    expect(screen.getByText("Active")).toBeTruthy();
    expect(screen.getByText("Inactive")).toBeTruthy();
  });

  it("filters employees by search input", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    server.use(
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/employees`, () => HttpResponse.json(employees)),
    );

    render(<EmployeesPage />, { wrapper: createRouterWrapper() });

    await screen.findByRole("link", { name: "Maya Patel" });

    const search = screen.getByPlaceholderText(/Search by name or email/i);
    await userEvent.type(search, "james");

    await waitFor(() => expect(screen.queryByRole("link", { name: "Maya Patel" })).toBeNull());
    expect(screen.getByRole("link", { name: "James O'Connor" })).toBeTruthy();
  });

  it("filters employees by inactive status", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    server.use(
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/employees`, () => HttpResponse.json(employees)),
    );

    render(<EmployeesPage />, { wrapper: createRouterWrapper() });

    await screen.findByRole("link", { name: "Maya Patel" });

    await userEvent.click(screen.getByRole("combobox"));
    await userEvent.click(await screen.findByRole("option", { name: "Inactive" }));

    await waitFor(() => expect(screen.queryByRole("link", { name: "Maya Patel" })).toBeNull());
    expect(screen.getByRole("link", { name: "James O'Connor" })).toBeTruthy();
  });

  it("opens the detail sheet when a row is clicked", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    server.use(
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/employees`, () => HttpResponse.json(employees)),
    );

    render(<EmployeesPage />, { wrapper: createRouterWrapper() });

    const row = (await screen.findByRole("link", { name: "Maya Patel" })).closest("tr")!;
    await userEvent.click(row);

    expect(await screen.findByRole("heading", { name: "Maya Patel", level: 2 })).toBeTruthy();
    expect(screen.getByRole("link", { name: /View detail/ })).toBeTruthy();
  });

  it("shows a 'no match' row when filters exclude everyone", async () => {
    useTenantStore.setState({ currentTenantId: TENANT_ID });
    server.use(
      http.get(`${BASE}/api/v1/tenants/${TENANT_ID}/employees`, () => HttpResponse.json(employees)),
    );

    render(<EmployeesPage />, { wrapper: createRouterWrapper() });

    await screen.findByRole("link", { name: "Maya Patel" });

    const search = screen.getByPlaceholderText(/Search by name or email/i);
    await userEvent.type(search, "zzz-no-match");

    expect(await screen.findByText("No employee matches the filters.")).toBeTruthy();
  });
});
