import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { PeriodIn, TimeReportIn } from "@/client";
import {
  createPeriodApiV1TenantsTenantIdPeriodsPost,
  createTimeReportApiV1TenantsTenantIdPeriodsPeriodIdReportsPost,
  getPeriodApiV1TenantsTenantIdPeriodsPeriodIdGet,
  listPeriodsApiV1TenantsTenantIdPeriodsGet,
  listTimeReportsForPeriodApiV1TenantsTenantIdPeriodsPeriodIdReportsGet,
  lockPeriodApiV1TenantsTenantIdPeriodsPeriodIdLockPost,
} from "@/client";

export function usePeriods(tenantId: number | null) {
  return useQuery({
    queryKey: ["periods", tenantId],
    enabled: tenantId != null,
    queryFn: async () => {
      const { data, error } = await listPeriodsApiV1TenantsTenantIdPeriodsGet({
        path: { tenant_id: tenantId! },
      });
      if (error || !data) throw error;
      return data;
    },
  });
}

export function usePeriod(tenantId: number | null, periodId: number | null) {
  return useQuery({
    queryKey: ["periods", tenantId, periodId],
    enabled: tenantId != null && periodId != null,
    queryFn: async () => {
      const { data, error } = await getPeriodApiV1TenantsTenantIdPeriodsPeriodIdGet({
        path: { tenant_id: tenantId!, period_id: periodId! },
      });
      if (error || !data) throw error;
      return data;
    },
  });
}

export function useCreatePeriod(tenantId: number | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: PeriodIn) => {
      const { data, error } = await createPeriodApiV1TenantsTenantIdPeriodsPost({
        path: { tenant_id: tenantId! },
        body,
      });
      if (error || !data) throw error;
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["periods", tenantId] }),
  });
}

export function useLockPeriod(tenantId: number | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      const { data, error } = await lockPeriodApiV1TenantsTenantIdPeriodsPeriodIdLockPost({
        path: { tenant_id: tenantId!, period_id: id },
      });
      if (error || !data) throw error;
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["periods", tenantId] }),
  });
}

export function usePeriodReports(tenantId: number | null, periodId: number | null) {
  return useQuery({
    queryKey: ["periods", tenantId, periodId, "reports"],
    enabled: tenantId != null && periodId != null,
    queryFn: async () => {
      const { data, error } =
        await listTimeReportsForPeriodApiV1TenantsTenantIdPeriodsPeriodIdReportsGet({
          path: { tenant_id: tenantId!, period_id: periodId! },
        });
      if (error || !data) throw error;
      return data;
    },
  });
}

export function useCreateTimeReport(tenantId: number | null, periodId: number | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: TimeReportIn) => {
      const { data, error } = await createTimeReportApiV1TenantsTenantIdPeriodsPeriodIdReportsPost({
        path: { tenant_id: tenantId!, period_id: periodId! },
        body,
      });
      if (error || !data) throw error;
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["periods", tenantId, periodId, "reports"] });
      qc.invalidateQueries({ queryKey: ["reports", tenantId] });
    },
  });
}
