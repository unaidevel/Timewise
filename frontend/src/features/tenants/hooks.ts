import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { TenantIn } from "@/client";
import {
  createApiV1TenantsPost,
  getByIdApiV1TenantsTenantIdGet,
  listForUserApiV1TenantsGet,
  listMembersApiV1TenantsTenantIdMembersGet,
  seedDemoDataApiV1TenantsTenantIdDemoDataPost,
} from "@/client";
import { useDepartments } from "@/features/departments/hooks";
import { useEmployees } from "@/features/employees/hooks";
import { useTenantStore } from "./store";

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

export function useTenantIsEmpty(tenantId: number | null): boolean {
  const { data: departments, isPending: deptsPending } = useDepartments(tenantId);
  const { data: employees, isPending: empsPending } = useEmployees(tenantId);
  if (tenantId == null || deptsPending || empsPending) return false;
  return (departments?.length ?? 0) === 0 && (employees?.length ?? 0) === 0;
}
