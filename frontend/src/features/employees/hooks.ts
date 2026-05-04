import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { EmployeeIn } from "@/client";
import {
  createEmployeeApiV1TenantsTenantIdEmployeesPost,
  deactivateEmployeeApiV1TenantsTenantIdEmployeesEmployeeIdDelete,
  getEmployeeApiV1TenantsTenantIdEmployeesEmployeeIdGet,
  listEmployeesApiV1TenantsTenantIdEmployeesGet,
} from "@/client";

export function useEmployees(tenantId: number | null) {
  return useQuery({
    queryKey: ["employees", tenantId],
    enabled: tenantId != null,
    queryFn: async () => {
      const { data, error } = await listEmployeesApiV1TenantsTenantIdEmployeesGet({
        path: { tenant_id: tenantId! },
      });
      if (error || !data) throw error;
      return data;
    },
  });
}

export function useEmployee(tenantId: number | null, employeeId: number | null) {
  return useQuery({
    queryKey: ["employees", tenantId, employeeId],
    enabled: tenantId != null && employeeId != null,
    queryFn: async () => {
      const { data, error } = await getEmployeeApiV1TenantsTenantIdEmployeesEmployeeIdGet({
        path: { tenant_id: tenantId!, employee_id: employeeId! },
      });
      if (error || !data) throw error;
      return data;
    },
  });
}

export function useCreateEmployee(tenantId: number | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: EmployeeIn) => {
      const { data, error } = await createEmployeeApiV1TenantsTenantIdEmployeesPost({
        path: { tenant_id: tenantId! },
        body,
      });
      if (error || !data) throw error;
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["employees", tenantId] }),
  });
}

export function useDeactivateEmployee(tenantId: number | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      const { error } = await deactivateEmployeeApiV1TenantsTenantIdEmployeesEmployeeIdDelete({
        path: { tenant_id: tenantId!, employee_id: id },
      });
      if (error) throw error;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["employees", tenantId] }),
  });
}
