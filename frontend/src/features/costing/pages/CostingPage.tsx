import { useQueries } from "@tanstack/react-query";
import { AlertTriangle, Calculator, Clock, DollarSign, Download, TrendingUp } from "lucide-react";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  getActiveDepartmentApiV1TenantsTenantIdEmployeesEmployeeIdDepartmentsCurrentGet,
  getActiveRoleApiV1TenantsTenantIdEmployeesEmployeeIdRolesCurrentGet,
  listTimeEntriesApiV1TenantsTenantIdReportsReportIdEntriesGet,
} from "@/client";
import { EmptyState } from "@/components/EmptyState";
import { Badge } from "@/components/shadcn/badge";
import { Button } from "@/components/shadcn/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/shadcn/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/shadcn/select";
import { Skeleton } from "@/components/shadcn/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/shadcn/table";
import { useDepartments } from "@/features/departments/hooks";
import { useEmployees } from "@/features/employees/hooks";
import { usePeriodReports, usePeriods } from "@/features/periods/hooks";
import {
  colorForDepartment,
  useDepartmentColors,
  useOrgProfile,
  useOvertimeConfig,
} from "@/features/settings/local-store";
import { useCurrentTenantId } from "@/features/tenants/hooks";
import { downloadCsv } from "@/lib/csv";
import { cn } from "@/lib/utils";

const fmtCurrency = (n: number, currency = "EUR") =>
  new Intl.NumberFormat(undefined, {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(n);

export default function CostingPage() {
  const tenantId = useCurrentTenantId();
  if (tenantId == null) return <NoTenantState />;
  return <Costing tenantId={tenantId} />;
}

function NoTenantState() {
  const { t } = useTranslation();
  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("costing.noTenant.title")}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground mb-4">{t("costing.noTenant.description")}</p>
        <Link to="/onboarding" className="text-sm font-medium text-primary hover:underline">
          {t("costing.noTenant.cta")}
        </Link>
      </CardContent>
    </Card>
  );
}

function Costing({ tenantId }: { tenantId: number }) {
  const otCfg = useOvertimeConfig(tenantId);
  const org = useOrgProfile(tenantId);
  const colors = useDepartmentColors(tenantId);
  const { t } = useTranslation();

  const periods = usePeriods(tenantId);
  const employees = useEmployees(tenantId);
  const departments = useDepartments(tenantId);

  const sortedPeriods = useMemo(
    () => [...(periods.data ?? [])].sort((a, b) => b.start_date.localeCompare(a.start_date)),
    [periods.data],
  );

  const [selectedPeriodId, setSelectedPeriodId] = useState<number | "latest">("latest");
  const activePeriodId =
    selectedPeriodId === "latest" ? (sortedPeriods[0]?.id ?? null) : selectedPeriodId;
  const activePeriod = sortedPeriods.find((p) => p.id === activePeriodId) ?? null;

  const reports = usePeriodReports(tenantId, activePeriodId);

  const entriesByReport = useQueries({
    queries: (reports.data ?? []).map((r) => ({
      queryKey: ["report-entries", tenantId, r.id],
      enabled: tenantId != null,
      queryFn: async () => {
        const { data, error } = await listTimeEntriesApiV1TenantsTenantIdReportsReportIdEntriesGet({
          path: { tenant_id: tenantId, report_id: r.id },
        });
        if (error || !data) throw error;
        return { reportId: r.id, employeeId: r.employee_id, entries: data };
      },
    })),
  });

  const employeeIds = useMemo(() => {
    const set = new Set<number>();
    for (const r of reports.data ?? []) set.add(r.employee_id);
    return [...set];
  }, [reports.data]);

  const rolesByEmp = useQueries({
    queries: employeeIds.map((eid) => ({
      queryKey: ["active-role", tenantId, eid],
      enabled: tenantId != null,
      queryFn: async () => {
        const { data, error } =
          await getActiveRoleApiV1TenantsTenantIdEmployeesEmployeeIdRolesCurrentGet({
            path: { tenant_id: tenantId, employee_id: eid },
          });
        if (error) return { employeeId: eid, hourly_rate: 0 };
        return { employeeId: eid, hourly_rate: Number(data?.hourly_rate ?? 0) };
      },
    })),
  });

  const deptsByEmp = useQueries({
    queries: employeeIds.map((eid) => ({
      queryKey: ["active-department", tenantId, eid],
      enabled: tenantId != null,
      queryFn: async () => {
        const { data, error } =
          await getActiveDepartmentApiV1TenantsTenantIdEmployeesEmployeeIdDepartmentsCurrentGet({
            path: { tenant_id: tenantId, employee_id: eid },
          });
        if (error) return { employeeId: eid, departmentId: null as number | null };
        return { employeeId: eid, departmentId: data?.department_id ?? null };
      },
    })),
  });

  const empById = useMemo(
    () => Object.fromEntries((employees.data ?? []).map((e) => [e.id, e] as const)),
    [employees.data],
  );
  const deptById = useMemo(
    () => Object.fromEntries((departments.data ?? []).map((d) => [d.id, d] as const)),
    [departments.data],
  );
  const rateByEmp = useMemo(() => {
    const m: Record<number, number> = {};
    for (const q of rolesByEmp) if (q.data) m[q.data.employeeId] = q.data.hourly_rate;
    return m;
  }, [rolesByEmp]);
  const deptIdByEmp = useMemo(() => {
    const m: Record<number, number | null> = {};
    for (const q of deptsByEmp) if (q.data) m[q.data.employeeId] = q.data.departmentId;
    return m;
  }, [deptsByEmp]);

  const isLoading =
    periods.isLoading ||
    reports.isLoading ||
    entriesByReport.some((q) => q.isLoading) ||
    rolesByEmp.some((q) => q.isLoading) ||
    deptsByEmp.some((q) => q.isLoading);

  const computed = useMemo(() => {
    const rows: ComputedRow[] = [];
    for (const q of entriesByReport) {
      if (!q.data) continue;
      const { employeeId, entries } = q.data;
      const rate = rateByEmp[employeeId] ?? 0;
      const { regHours, dailyOt, weeklyOt } = computeOvertime(
        entries.map((e) => ({ date: e.date, hours: Number(e.hours) })),
        otCfg,
      );
      const totalHours = regHours + dailyOt + weeklyOt;
      const regCost = regHours * rate;
      const otCost = dailyOt * rate * otCfg.daily_multiplier + weeklyOt * rate * otCfg.multiplier;
      rows.push({
        employeeId,
        rate,
        totalHours,
        otHours: dailyOt + weeklyOt,
        regCost,
        otCost,
        totalCost: regCost + otCost,
      });
    }
    return rows;
  }, [entriesByReport, rateByEmp, otCfg]);

  const totals = useMemo(
    () =>
      computed.reduce(
        (acc, r) => {
          acc.hours += r.totalHours;
          acc.otHours += r.otHours;
          acc.regCost += r.regCost;
          acc.otCost += r.otCost;
          acc.total += r.totalCost;
          return acc;
        },
        { hours: 0, otHours: 0, regCost: 0, otCost: 0, total: 0 },
      ),
    [computed],
  );

  const byDept = useMemo(() => {
    const map = new Map<
      number,
      { id: number; name: string; color: string; cost: number; hours: number }
    >();
    for (const r of computed) {
      const deptId = deptIdByEmp[r.employeeId];
      const dept = deptId != null ? deptById[deptId] : null;
      if (!dept) continue;
      const cur = map.get(dept.id) ?? {
        id: dept.id,
        name: dept.name,
        color: colorForDepartment(colors, dept.id),
        cost: 0,
        hours: 0,
      };
      cur.cost += r.totalCost;
      cur.hours += r.totalHours;
      map.set(dept.id, cur);
    }
    return [...map.values()].sort((a, b) => b.cost - a.cost);
  }, [computed, deptIdByEmp, deptById, colors]);

  const byEmployee = useMemo(() => {
    const map = new Map<number, ComputedRow>();
    for (const r of computed) {
      const cur = map.get(r.employeeId);
      if (!cur) {
        map.set(r.employeeId, { ...r });
      } else {
        cur.totalHours += r.totalHours;
        cur.otHours += r.otHours;
        cur.regCost += r.regCost;
        cur.otCost += r.otCost;
        cur.totalCost += r.totalCost;
      }
    }
    return [...map.values()].sort((a, b) => b.totalCost - a.totalCost);
  }, [computed]);

  function exportCsv() {
    const rows = byEmployee.map((r) => {
      const emp = empById[r.employeeId];
      const deptId = deptIdByEmp[r.employeeId];
      const dept = deptId != null ? deptById[deptId] : null;
      return {
        [t("costing.csvHeaders.employee")]: emp?.full_name ?? `#${r.employeeId}`,
        [t("costing.csvHeaders.department")]: dept?.name ?? "—",
        [t("costing.csvHeaders.hourlyRate")]: r.rate,
        [t("costing.csvHeaders.hours")]: Number(r.totalHours.toFixed(2)),
        [t("costing.csvHeaders.overtime")]: Number(r.otHours.toFixed(2)),
        [t("costing.csvHeaders.totalCost")]: r.totalCost.toFixed(2),
      };
    });
    const label = activePeriod?.name ?? "period";
    downloadCsv(t("costing.csvFilename", { label }), rows);
  }

  const noData = !isLoading && (sortedPeriods.length === 0 || (reports.data?.length ?? 0) === 0);

  if (noData) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-semibold tracking-tight">{t("costing.title")}</h1>
        <EmptyState
          icon={Calculator}
          title={t("costing.empty.title")}
          description={t("costing.empty.description")}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">{t("costing.title")}</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {t("costing.subtitle", {
              weekly: otCfg.weekly_threshold,
              daily: otCfg.daily_threshold,
            })}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Select
            value={String(selectedPeriodId)}
            onValueChange={(v) => setSelectedPeriodId(v === "latest" ? "latest" : Number(v))}
          >
            <SelectTrigger className="w-[220px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="latest">{t("costing.latestPeriod")}</SelectItem>
              {sortedPeriods.map((p) => (
                <SelectItem key={p.id} value={String(p.id)}>
                  {p.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button variant="outline" onClick={exportCsv} disabled={byEmployee.length === 0}>
            <Download className="size-4 mr-2" />
            {t("costing.exportCsv")}
          </Button>
        </div>
      </header>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Kpi
          icon={DollarSign}
          label={t("costing.kpi.total")}
          value={fmtCurrency(totals.total, org.currency)}
          hint={t("costing.kpi.totalHint", { hours: totals.hours.toFixed(0) })}
          loading={isLoading}
        />
        <Kpi
          icon={TrendingUp}
          label={t("costing.kpi.regular")}
          value={fmtCurrency(totals.regCost, org.currency)}
          hint={t("costing.kpi.regularHint", {
            hours: (totals.hours - totals.otHours).toFixed(0),
          })}
          loading={isLoading}
        />
        <Kpi
          icon={AlertTriangle}
          label={t("costing.kpi.overtime")}
          value={fmtCurrency(totals.otCost, org.currency)}
          hint={t("costing.kpi.overtimeHint", { hours: totals.otHours.toFixed(0) })}
          accent
          loading={isLoading}
        />
        <Kpi
          icon={Clock}
          label={t("costing.kpi.avgRate")}
          value={
            totals.hours > 0 ? `${fmtCurrency(totals.total / totals.hours, org.currency)}/h` : "—"
          }
          hint={t("costing.kpi.avgRateHint")}
          loading={isLoading}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle className="text-base">{t("costing.byDept.title")}</CardTitle>
          </CardHeader>
          <CardContent>
            {byDept.length === 0 ? (
              <div className="h-[280px] grid place-items-center text-sm text-muted-foreground">
                {isLoading ? t("costing.byDept.calculating") : t("costing.byDept.noData")}
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={byDept} margin={{ left: -10, right: 8, top: 8 }}>
                  <CartesianGrid
                    stroke="var(--color-border)"
                    strokeDasharray="3 3"
                    vertical={false}
                  />
                  <XAxis dataKey="name" tickLine={false} axisLine={false} fontSize={12} />
                  <YAxis
                    tickLine={false}
                    axisLine={false}
                    fontSize={12}
                    tickFormatter={(v) => fmtCurrency(v as number, org.currency)}
                  />
                  <Tooltip
                    cursor={{ fill: "var(--color-muted)" }}
                    contentStyle={{
                      background: "var(--color-popover)",
                      border: "1px solid var(--color-border)",
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                    formatter={(v: number) => fmtCurrency(v, org.currency)}
                  />
                  <Bar dataKey="cost" radius={[6, 6, 0, 0]}>
                    {byDept.map((d) => (
                      <Cell key={d.id} fill={d.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">{t("costing.byDept.breakdown")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {byDept.map((d) => {
              const pct = totals.total > 0 ? (d.cost / totals.total) * 100 : 0;
              return (
                <div key={d.id}>
                  <div className="flex justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <span className="size-2 rounded-full" style={{ background: d.color }} />
                      <span className="font-medium">{d.name}</span>
                    </div>
                    <span className="font-mono text-xs text-muted-foreground">
                      {fmtCurrency(d.cost, org.currency)}
                    </span>
                  </div>
                  <div className="mt-1.5 h-1.5 rounded-full bg-muted overflow-hidden">
                    <div
                      className="h-full rounded-full"
                      style={{ width: `${pct}%`, background: d.color }}
                    />
                  </div>
                </div>
              );
            })}
            {byDept.length === 0 && (
              <p className="text-sm text-muted-foreground text-center py-8">
                {t("costing.byDept.empty")}
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <CardTitle className="text-base">{t("costing.byEmployee.title")}</CardTitle>
          <Badge variant="secondary">
            {t("costing.byEmployee.countBadge", { count: byEmployee.length })}
          </Badge>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t("costing.byEmployee.columns.employee")}</TableHead>
                <TableHead>{t("costing.byEmployee.columns.department")}</TableHead>
                <TableHead className="text-right">{t("costing.byEmployee.columns.rate")}</TableHead>
                <TableHead className="text-right">
                  {t("costing.byEmployee.columns.hours")}
                </TableHead>
                <TableHead className="text-right">
                  {t("costing.byEmployee.columns.overtime")}
                </TableHead>
                <TableHead className="text-right">{t("costing.byEmployee.columns.cost")}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading &&
                byEmployee.length === 0 &&
                ["a", "b", "c"].map((row) => (
                  <TableRow key={row}>
                    {["emp", "dept", "rate", "h", "ot", "cost"].map((col) => (
                      <TableCell key={col}>
                        <Skeleton className="h-5 w-20" />
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              {byEmployee.map((r) => {
                const emp = empById[r.employeeId];
                const deptId = deptIdByEmp[r.employeeId];
                const dept = deptId != null ? deptById[deptId] : null;
                const deptColor = dept ? colorForDepartment(colors, dept.id) : undefined;
                return (
                  <TableRow key={r.employeeId}>
                    <TableCell className="font-medium">
                      {emp?.full_name ?? `#${r.employeeId}`}
                    </TableCell>
                    <TableCell>
                      <span className="inline-flex items-center gap-1.5 text-xs">
                        <span className="size-2 rounded-full" style={{ background: deptColor }} />
                        {dept?.name ?? "—"}
                      </span>
                    </TableCell>
                    <TableCell className="text-right font-mono text-sm">
                      {fmtCurrency(r.rate, org.currency)}/h
                    </TableCell>
                    <TableCell className="text-right font-mono text-sm">
                      {r.totalHours.toFixed(1)}
                    </TableCell>
                    <TableCell
                      className={cn(
                        "text-right font-mono text-sm",
                        r.otHours > 0 && "text-warning-foreground",
                      )}
                    >
                      {r.otHours > 0 ? `+${r.otHours.toFixed(1)}` : "—"}
                    </TableCell>
                    <TableCell className="text-right font-mono font-semibold">
                      {fmtCurrency(r.totalCost, org.currency)}
                    </TableCell>
                  </TableRow>
                );
              })}
              {!isLoading && byEmployee.length === 0 && (
                <TableRow>
                  <TableCell
                    colSpan={6}
                    className="text-center text-sm text-muted-foreground py-12"
                  >
                    {t("costing.byEmployee.empty")}
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

type ComputedRow = {
  employeeId: number;
  rate: number;
  totalHours: number;
  otHours: number;
  regCost: number;
  otCost: number;
  totalCost: number;
};

type OvertimeCfg = {
  weekly_threshold: number;
  multiplier: number;
  daily_threshold: number;
  daily_multiplier: number;
};

// Group entries by ISO week (Mon-Sun) and compute daily + weekly OT.
// Daily OT counts first; weekly OT applies to the remainder above the weekly threshold
// after daily OT has already been subtracted.
function computeOvertime(
  entries: { date: string; hours: number }[],
  cfg: OvertimeCfg,
): { regHours: number; dailyOt: number; weeklyOt: number } {
  // Sum hours per date first (in case multiple entries on same day).
  const perDay = new Map<string, number>();
  for (const e of entries) {
    perDay.set(e.date, (perDay.get(e.date) ?? 0) + e.hours);
  }
  const perWeek = new Map<string, number[]>();
  for (const [date, hours] of perDay) {
    const key = isoWeekKey(date);
    const arr = perWeek.get(key) ?? [];
    arr.push(hours);
    perWeek.set(key, arr);
  }
  let regHours = 0;
  let dailyOt = 0;
  let weeklyOt = 0;
  for (const days of perWeek.values()) {
    let weekDailyOt = 0;
    let weekDailyReg = 0;
    for (const h of days) {
      if (h > cfg.daily_threshold) {
        weekDailyOt += h - cfg.daily_threshold;
        weekDailyReg += cfg.daily_threshold;
      } else {
        weekDailyReg += h;
      }
    }
    const overWeekly = Math.max(0, weekDailyReg - cfg.weekly_threshold);
    regHours += weekDailyReg - overWeekly;
    weeklyOt += overWeekly;
    dailyOt += weekDailyOt;
  }
  return { regHours, dailyOt, weeklyOt };
}

function isoWeekKey(dateStr: string): string {
  // dateStr is YYYY-MM-DD.
  const d = new Date(`${dateStr}T00:00:00Z`);
  const day = d.getUTCDay() || 7;
  d.setUTCDate(d.getUTCDate() + 4 - day);
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
  const week = Math.ceil(((d.getTime() - yearStart.getTime()) / 86400000 + 1) / 7);
  return `${d.getUTCFullYear()}-W${String(week).padStart(2, "0")}`;
}

function Kpi({
  icon: Icon,
  label,
  value,
  hint,
  accent,
  loading,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
  hint: string;
  accent?: boolean;
  loading?: boolean;
}) {
  return (
    <Card>
      <CardContent className="p-5">
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">{label}</span>
          <div
            className={cn(
              "size-8 rounded-lg grid place-items-center",
              accent ? "bg-warning/15 text-warning-foreground" : "bg-primary/10 text-primary",
            )}
          >
            <Icon className="size-4" />
          </div>
        </div>
        {loading ? (
          <Skeleton className="h-8 w-28 mt-2" />
        ) : (
          <div className="mt-2 text-2xl font-semibold tracking-tight font-mono">{value}</div>
        )}
        <div className="text-xs text-muted-foreground mt-1">{hint}</div>
      </CardContent>
    </Card>
  );
}
