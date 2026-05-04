import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { RoleIn, RoleUpdate } from "@/client";
import {
  createRoleApiV1TenantsTenantIdRolesPost,
  deactivateRoleApiV1TenantsTenantIdRolesRoleIdDelete,
  listRolesApiV1TenantsTenantIdRolesGet,
  updateRoleApiV1TenantsTenantIdRolesRoleIdPut,
} from "@/client";

export function useRoles(tenantId: number | null) {
  return useQuery({
    queryKey: ["roles", tenantId],
    enabled: tenantId != null,
    queryFn: async () => {
      const { data, error } = await listRolesApiV1TenantsTenantIdRolesGet({
        path: { tenant_id: tenantId! },
      });
      if (error || !data) throw error;
      return data;
    },
  });
}

export function useCreateRole(tenantId: number | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: RoleIn) => {
      const { data, error } = await createRoleApiV1TenantsTenantIdRolesPost({
        path: { tenant_id: tenantId! },
        body,
      });
      if (error || !data) throw error;
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["roles", tenantId] }),
  });
}

export function useUpdateRole(tenantId: number | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, body }: { id: number; body: RoleUpdate }) => {
      const { data, error } = await updateRoleApiV1TenantsTenantIdRolesRoleIdPut({
        path: { tenant_id: tenantId!, role_id: id },
        body,
      });
      if (error || !data) throw error;
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["roles", tenantId] }),
  });
}

export function useDeactivateRole(tenantId: number | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      const { error } = await deactivateRoleApiV1TenantsTenantIdRolesRoleIdDelete({
        path: { tenant_id: tenantId!, role_id: id },
      });
      if (error) throw error;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["roles", tenantId] }),
  });
}
