import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { TenantIn } from "@/client";
import {
  createApiV1TenantsPost,
  getByIdApiV1TenantsTenantIdGet,
  listForUserApiV1TenantsGet,
  listMembersApiV1TenantsTenantIdMembersGet,
} from "@/client";
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
