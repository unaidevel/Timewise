import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { AddMemberRequest, LinkEmployeeUserRequest, TenantIn } from "@/client";
import {
  addMemberApiV1TenantsTenantIdMembersPost,
  createApiV1TenantsPost,
  getByIdApiV1TenantsTenantIdGet,
  linkEmployeeUserApiV1TenantsTenantIdEmployeesEmployeeIdUserPut,
  listForUserApiV1TenantsGet,
  listMembersApiV1TenantsTenantIdMembersGet,
  seedDemoDataApiV1TenantsTenantIdDemoDataPost,
} from "@/client";
import { useAuthStore } from "@/features/auth/store";
import { useDepartments } from "@/features/departments/hooks";
import { useEmployees } from "@/features/employees/hooks";
import { useTenantStore } from "./store";

const ELEVATED_ROLES = new Set(["owner", "admin"]);

export function useTenants() {
  return useQuery({
    queryKey: ["tenants"],
    queryFn: async () => {
      const { data, error } = await listForUserApiV1TenantsGet({});
      if (error || !data) throw error;
      return data;
    },
  });
}

export function useTenant(tenantId: number | null) {
  return useQuery({
    queryKey: ["tenants", tenantId],
    enabled: tenantId != null,
    queryFn: async () => {
      const { data, error } = await getByIdApiV1TenantsTenantIdGet({
        path: { tenant_id: tenantId! },
      });
      if (error || !data) throw error;
      return data;
    },
  });
}

export function useCreateTenant() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: TenantIn) => {
      const { data, error } = await createApiV1TenantsPost({ body });
      if (error || !data) throw error;
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tenants"] }),
  });
}

export function useMembers(tenantId: number | null) {
  return useQuery({
    queryKey: ["tenants", tenantId, "members"],
    enabled: tenantId != null,
    queryFn: async () => {
      const { data, error } = await listMembersApiV1TenantsTenantIdMembersGet({
        path: { tenant_id: tenantId! },
      });
      if (error || !data) throw error;
      return data;
    },
  });
}

export function useAddMember(tenantId: number | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: AddMemberRequest) => {
      const { data, error } = await addMemberApiV1TenantsTenantIdMembersPost({
        path: { tenant_id: tenantId! },
        body,
      });
      if (error || !data) throw error;
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tenants", tenantId, "members"] }),
  });
}

export function useLinkEmployeeUser(tenantId: number | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      employeeId,
      body,
    }: { employeeId: number; body: LinkEmployeeUserRequest }) => {
      const { data, error } = await linkEmployeeUserApiV1TenantsTenantIdEmployeesEmployeeIdUserPut(
        {
          path: { tenant_id: tenantId!, employee_id: employeeId },
          body,
        },
      );
      if (error || !data) throw error;
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["employees", tenantId] }),
  });
}

export function useCurrentTenantId(): number | null {
  return useTenantStore((s) => s.currentTenantId);
}

export function useSeedDemoData(tenantId: number | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      if (tenantId == null) throw new Error("No tenant selected");
      const { data, error } = await seedDemoDataApiV1TenantsTenantIdDemoDataPost({
        path: { tenant_id: tenantId },
      });
      if (error || !data) throw error;
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["departments", tenantId] });
      qc.invalidateQueries({ queryKey: ["employees", tenantId] });
      qc.invalidateQueries({ queryKey: ["periods", tenantId] });
      qc.invalidateQueries({ queryKey: ["reports", tenantId] });
      qc.invalidateQueries({ queryKey: ["costing-rules", tenantId] });
      qc.invalidateQueries({ queryKey: ["audit", tenantId] });
    },
  });
}

export function useCurrentMembershipRole(tenantId: number | null): string | null {
  const user = useAuthStore((s) => s.user);
  const members = useMembers(tenantId);
  if (!user || !members.data) return null;
  const mine = members.data.find((m) => m.user_id === user.id && m.left_at == null);
  return mine?.role ?? null;
}

export function useIsTenantAdmin(tenantId: number | null): boolean {
  const role = useCurrentMembershipRole(tenantId);
  return role != null && ELEVATED_ROLES.has(role);
}

export function useTenantIsEmpty(tenantId: number | null): boolean {
  const { data: departments, isPending: deptsPending } = useDepartments(tenantId);
  const { data: employees, isPending: empsPending } = useEmployees(tenantId);
  if (tenantId == null || deptsPending || empsPending) return false;
  return (departments?.length ?? 0) === 0 && (employees?.length ?? 0) === 0;
}
