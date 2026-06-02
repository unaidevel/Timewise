import { useQueries } from "@tanstack/react-query";
import { useMemo } from "react";
import {
  getActiveRoleApiV1TenantsTenantIdEmployeesEmployeeIdRolesCurrentGet,
  listTimeEntriesApiV1TenantsTenantIdReportsReportIdEntriesGet,
  listTimeReportsForPeriodApiV1TenantsTenantIdPeriodsPeriodIdReportsGet,
} from "@/client";
import { computeOvertime } from "@/features/costing/overtime";
import { usePeriods } from "@/features/periods/hooks";
import { useOvertimeConfig } from "@/features/settings/local-store";

export type CostTrendPoint = {
  periodId: number;
  label: string;
  startDate: string;
  cost: number;
};

export function useCostTrend(tenantId: number | null) {
  const periods = usePeriods(tenantId);
  const otCfg = useOvertimeConfig(tenantId);

  const sortedPeriods = useMemo(
    () => (periods.data ?? []).toSorted((a, b) => a.start_date.localeCompare(b.start_date)),
    [periods.data],
  );

  const reportsByPeriod = useQueries({
    queries: sortedPeriods.map((p) => ({
      queryKey: ["cost-trend", "reports", tenantId, p.id],
      enabled: tenantId != null,
      queryFn: async () => {
        const { data, error } =
          await listTimeReportsForPeriodApiV1TenantsTenantIdPeriodsPeriodIdReportsGet({
            path: { tenant_id: tenantId!, period_id: p.id },
          });
        if (error || !data) throw error;
        return { periodId: p.id, reports: data };
      },
    })),
  });

  const allReports = useMemo(
    () =>
      reportsByPeriod.flatMap(
        (q) => q.data?.reports.map((r) => ({ ...r, periodId: q.data!.periodId })) ?? [],
      ),
    [reportsByPeriod],
  );

  const entriesByReport = useQueries({
    queries: allReports.map((r) => ({
      queryKey: ["report-entries", tenantId, r.id],
      enabled: tenantId != null,
      queryFn: async () => {
        const { data, error } = await listTimeEntriesApiV1TenantsTenantIdReportsReportIdEntriesGet({
          path: { tenant_id: tenantId!, report_id: r.id },
        });
        if (error || !data) throw error;
        return { reportId: r.id, employeeId: r.employee_id, entries: data };
      },
    })),
  });

  const periodByReportId = useMemo(() => {
    const m = new Map<number, number>();
    for (const r of allReports) m.set(r.id, r.periodId);
    return m;
  }, [allReports]);

  const employeeIds = useMemo(() => {
    const set = new Set<number>();
    for (const r of allReports) set.add(r.employee_id);
    return [...set];
  }, [allReports]);

  const rolesByEmp = useQueries({
    queries: employeeIds.map((eid) => ({
      queryKey: ["active-role", tenantId, eid],
      enabled: tenantId != null,
      queryFn: async () => {
        const { data, error } =
          await getActiveRoleApiV1TenantsTenantIdEmployeesEmployeeIdRolesCurrentGet({
            path: { tenant_id: tenantId!, employee_id: eid },
          });
        if (error) return { employeeId: eid, hourly_rate: 0 };
        return { employeeId: eid, hourly_rate: Number(data?.hourly_rate ?? 0) };
      },
    })),
  });

  const rateByEmp = useMemo(() => {
    const m: Record<number, number> = {};
    for (const q of rolesByEmp) if (q.data) m[q.data.employeeId] = q.data.hourly_rate;
    return m;
  }, [rolesByEmp]);

  const isLoading =
    periods.isLoading ||
    reportsByPeriod.some((q) => q.isLoading) ||
    entriesByReport.some((q) => q.isLoading) ||
    rolesByEmp.some((q) => q.isLoading);

  const points = useMemo<CostTrendPoint[]>(() => {
    const costByPeriod = new Map<number, number>();
    for (const q of entriesByReport) {
      if (!q.data) continue;
      const { reportId, employeeId, entries } = q.data;
      const periodId = periodByReportId.get(reportId);
      if (periodId == null) continue;
      const rate = rateByEmp[employeeId] ?? 0;
      const { regHours, dailyOt, weeklyOt } = computeOvertime(
        entries.map((e) => ({ date: e.date, hours: Number(e.hours) })),
        otCfg,
      );
      const cost =
        regHours * rate +
        dailyOt * rate * otCfg.daily_multiplier +
        weeklyOt * rate * otCfg.multiplier;
      costByPeriod.set(periodId, (costByPeriod.get(periodId) ?? 0) + cost);
    }
    return sortedPeriods.map((p) => ({
      periodId: p.id,
      label: p.name,
      startDate: p.start_date,
      cost: costByPeriod.get(p.id) ?? 0,
    }));
  }, [entriesByReport, rateByEmp, otCfg, sortedPeriods, periodByReportId]);

  return { points, isLoading };
}
