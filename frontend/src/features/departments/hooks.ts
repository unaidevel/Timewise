import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { DepartmentIn, DepartmentUpdate } from "@/client";
import {
  createDepartmentApiV1TenantsTenantIdDepartmentsPost,
  deactivateDepartmentApiV1TenantsTenantIdDepartmentsDepartmentIdDelete,
  listDepartmentsApiV1TenantsTenantIdDepartmentsGet,
  updateDepartmentApiV1TenantsTenantIdDepartmentsDepartmentIdPut,
} from "@/client";

export function useDepartments(tenantId: number | null) {
  return useQuery({
    queryKey: ["departments", tenantId],
    enabled: tenantId != null,
    queryFn: async () => {
      const { data, error } = await listDepartmentsApiV1TenantsTenantIdDepartmentsGet({
        path: { tenant_id: tenantId! },
      });
      if (error || !data) throw error;
      return data;
    },
  });
}

export function useCreateDepartment(tenantId: number | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: DepartmentIn) => {
      const { data, error } = await createDepartmentApiV1TenantsTenantIdDepartmentsPost({
        path: { tenant_id: tenantId! },
        body,
      });
      if (error || !data) throw error;
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["departments", tenantId] }),
  });
}

export function useUpdateDepartment(tenantId: number | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, body }: { id: number; body: DepartmentUpdate }) => {
      const { data, error } = await updateDepartmentApiV1TenantsTenantIdDepartmentsDepartmentIdPut({
        path: { tenant_id: tenantId!, department_id: id },
        body,
      });
      if (error || !data) throw error;
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["departments", tenantId] }),
  });
}

export function useDeactivateDepartment(tenantId: number | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      const { error } = await deactivateDepartmentApiV1TenantsTenantIdDepartmentsDepartmentIdDelete(
        {
          path: { tenant_id: tenantId!, department_id: id },
        },
      );
      if (error) throw error;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["departments", tenantId] }),
  });
}
