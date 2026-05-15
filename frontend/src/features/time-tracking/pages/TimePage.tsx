import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, ChevronLeft, ChevronRight, Clock, Send } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router";
import { toast } from "sonner";
import type { TimeEntryOut, TimeReportOut } from "@/client";
import {
  createTimeEntryApiV1TenantsTenantIdReportsReportIdEntriesPost,
  createTimeReportApiV1TenantsTenantIdPeriodsPeriodIdReportsPost,
  deleteTimeEntryApiV1TenantsTenantIdReportsReportIdEntriesEntryIdDelete,
  listTimeEntriesApiV1TenantsTenantIdReportsReportIdEntriesGet,
  listTimeReportsForPeriodApiV1TenantsTenantIdPeriodsPeriodIdReportsGet,
  submitTimeReportApiV1TenantsTenantIdReportsReportIdSubmitPost,
  updateTimeEntryApiV1TenantsTenantIdReportsReportIdEntriesEntryIdPut,
} from "@/client";
import { EmptyState } from "@/components/EmptyState";
import { Badge } from "@/components/shadcn/badge";
import { Button } from "@/components/shadcn/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/shadcn/card";
import { Input } from "@/components/shadcn/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/shadcn/select";
import { Skeleton } from "@/components/shadcn/skeleton";
import { useAuthStore } from "@/features/auth/store";
import { useEmployees } from "@/features/employees/hooks";
import { usePeriods } from "@/features/periods/hooks";
import { useOvertimeConfig } from "@/features/settings/local-store";
import { useCurrentTenantId } from "@/features/tenants/hooks";
import { cn } from "@/lib/utils";

const EMPLOYEE_KEY = (tenantId: number) => `timewise:time-tracking:employee:${tenantId}`;

const statusStyle: Record<string, string> = {
  draft: "bg-muted text-muted-foreground border-border",
  submitted: "bg-warning/20 text-warning-foreground border-warning/30",
  approved: "bg-success/15 text-success border-success/20",
  rejected: "bg-destructive/15 text-destructive border-destructive/20",
};

function fmtDate(iso: string) {
  return new Date(`${iso}T00:00:00`).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
}
function dayLabel(iso: string) {
  return new Date(`${iso}T00:00:00`).toLocaleDateString(undefined, { weekday: "short" });
}

function eachDay(startIso: string, endIso: string): string[] {
  // Iterate in UTC so that converting back to a YYYY-MM-DD string is
  // independent of the runtime timezone. Using local-time arithmetic would
  // shift the date by ±1 day in some timezones when calling toISOString().
  const days: string[] = [];
  const start = new Date(`${startIso}T00:00:00Z`);
  const end = new Date(`${endIso}T00:00:00Z`);
  for (let d = start; d <= end; d.setUTCDate(d.getUTCDate() + 1)) {
    days.push(d.toISOString().slice(0, 10));
  }
  return days;
}

export default function TimePage() {
  const tenantId = useCurrentTenantId();
  if (tenantId == null) return <NoTenantState />;
  return <TimeTracking tenantId={tenantId} />;
}

function NoTenantState() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Selecciona un workspace</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground mb-4">
          Necesitas crear o seleccionar una organización para fichar horas.
        </p>
        <Link to="/onboarding" className="text-sm font-medium text-primary hover:underline">
          Crear primera organización →
        </Link>
      </CardContent>
    </Card>
  );
}

function TimeTracking({ tenantId }: { tenantId: number }) {
  const user = useAuthStore((s) => s.user);
  const otCfg = useOvertimeConfig(tenantId);
  const employees = useEmployees(tenantId);
  const periods = usePeriods(tenantId);

  const sortedPeriods = useMemo(
    () => [...(periods.data ?? [])].sort((a, b) => b.start_date.localeCompare(a.start_date)),
    [periods.data],
  );

  const [employeeId, setEmployeeIdState] = useState<number | null>(null);

  // Resolve "me": prefer matching auth user, else saved choice, else first active.
  useEffect(() => {
    if (employeeId != null || !employees.data || employees.data.length === 0) return;
    const matchByUser =
      user != null ? employees.data.find((e) => e.user_id === user.id) : undefined;
    const saved = (() => {
      try {
        const raw = window.localStorage.getItem(EMPLOYEE_KEY(tenantId));
        return raw ? Number(raw) : null;
      } catch {
        return null;
      }
    })();
    const savedMatch = saved != null ? employees.data.find((e) => e.id === saved) : undefined;
    const fallback = employees.data.find((e) => e.is_active) ?? employees.data[0];
    setEmployeeIdState(matchByUser?.id ?? savedMatch?.id ?? fallback?.id ?? null);
  }, [employees.data, user, tenantId, employeeId]);

  function setEmployeeId(id: number) {
    setEmployeeIdState(id);
    try {
      window.localStorage.setItem(EMPLOYEE_KEY(tenantId), String(id));
    } catch {
      // ignore
    }
  }

  const [periodIdx, setPeriodIdx] = useState(0);
  const activePeriod = sortedPeriods[periodIdx] ?? null;

  if (!periods.isLoading && sortedPeriods.length === 0) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-semibold tracking-tight">Fichaje de horas</h1>
        <EmptyState
          icon={Clock}
          title="No hay periodos abiertos"
          description="Crea un periodo desde la sección de Periodos para empezar a imputar horas."
        />
      </div>
    );
  }

  if (employees.isSuccess && (employees.data?.length ?? 0) === 0) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-semibold tracking-tight">Fichaje de horas</h1>
        <EmptyState
          icon={Clock}
          title="No hay empleados"
          description="Crea un empleado para poder imputar horas en su nombre."
        />
      </div>
    );
  }

  const meEmployee = employees.data?.find((e) => e.id === employeeId) ?? null;
  const canShowGrid = activePeriod != null && meEmployee != null;

  return (
    <div className="space-y-6">
      <header className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Fichaje de horas</h1>
          {meEmployee ? (
            <p className="text-sm text-muted-foreground mt-1">
              Imputando horas como{" "}
              <span className="font-medium text-foreground">{meEmployee.full_name}</span>
            </p>
          ) : (
            <p className="text-sm text-muted-foreground mt-1">Selecciona un empleado…</p>
          )}
        </div>
        {(employees.data?.length ?? 0) > 1 && (
          <Select
            value={employeeId != null ? String(employeeId) : undefined}
            onValueChange={(v) => setEmployeeId(Number(v))}
          >
            <SelectTrigger className="w-[240px]">
              <SelectValue placeholder="Seleccionar empleado" />
            </SelectTrigger>
            <SelectContent>
              {(employees.data ?? []).map((e) => (
                <SelectItem key={e.id} value={String(e.id)}>
                  {e.full_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </header>

      {canShowGrid && meEmployee && activePeriod && (
        <PeriodEditor
          tenantId={tenantId}
          periodId={activePeriod.id}
          periodName={activePeriod.name}
          periodStart={activePeriod.start_date}
          periodEnd={activePeriod.end_date}
          employeeId={meEmployee.id}
          weeklyThreshold={otCfg.weekly_threshold}
          canGoPrev={periodIdx < sortedPeriods.length - 1}
          canGoNext={periodIdx > 0}
          onPrev={() => setPeriodIdx((i) => i + 1)}
          onNext={() => setPeriodIdx((i) => i - 1)}
        />
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Periodos recientes</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {sortedPeriods.map((p, i) => (
            <button
              type="button"
              key={p.id}
              onClick={() => setPeriodIdx(i)}
              className={cn(
                "w-full flex items-center justify-between p-3 rounded-lg border text-left hover:bg-muted/40 transition",
                i === periodIdx && "border-primary bg-primary/5",
              )}
            >
              <div>
                <div className="text-sm font-medium">{p.name}</div>
                <div className="text-xs text-muted-foreground mt-0.5">
                  {fmtDate(p.start_date)} — {fmtDate(p.end_date)}
                </div>
              </div>
              {i === periodIdx && <Check className="size-4 text-primary" />}
            </button>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

function PeriodEditor({
  tenantId,
  periodId,
  periodName,
  periodStart,
  periodEnd,
  employeeId,
  weeklyThreshold,
  canGoPrev,
  canGoNext,
  onPrev,
  onNext,
}: {
  tenantId: number;
  periodId: number;
  periodName: string;
  periodStart: string;
  periodEnd: string;
  employeeId: number;
  weeklyThreshold: number;
  canGoPrev: boolean;
  canGoNext: boolean;
  onPrev: () => void;
  onNext: () => void;
}) {
  const qc = useQueryClient();

  const reports = useQuery({
    queryKey: ["time-tracking", "period-reports", tenantId, periodId],
    queryFn: async () => {
      const { data, error } =
        await listTimeReportsForPeriodApiV1TenantsTenantIdPeriodsPeriodIdReportsGet({
          path: { tenant_id: tenantId, period_id: periodId },
        });
      if (error || !data) throw error;
      return data;
    },
  });

  const myReport = useMemo(
    () => (reports.data ?? []).find((r) => r.employee_id === employeeId) ?? null,
    [reports.data, employeeId],
  );

  const createReport = useMutation({
    mutationFn: async () => {
      const { data, error } = await createTimeReportApiV1TenantsTenantIdPeriodsPeriodIdReportsPost({
        path: { tenant_id: tenantId, period_id: periodId },
        body: { employee_id: employeeId },
      });
      if (error || !data) throw error;
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({
        queryKey: ["time-tracking", "period-reports", tenantId, periodId],
      });
      qc.invalidateQueries({ queryKey: ["periods", tenantId, periodId, "reports"] });
    },
  });

  if (reports.isLoading) {
    return (
      <Card>
        <CardContent className="p-6">
          <Skeleton className="h-32 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (!myReport) {
    return (
      <Card>
        <CardHeader className="flex-row items-center justify-between flex-wrap gap-3">
          <div>
            <CardTitle className="text-base">{periodName}</CardTitle>
            <p className="text-xs text-muted-foreground mt-1">
              {fmtDate(periodStart)} — {fmtDate(periodEnd)}
            </p>
          </div>
          <PeriodNav canGoPrev={canGoPrev} canGoNext={canGoNext} onPrev={onPrev} onNext={onNext} />
        </CardHeader>
        <CardContent>
          <div className="rounded-lg border border-dashed p-8 text-center space-y-3">
            <p className="text-sm text-muted-foreground">
              Aún no tienes un reporte para este periodo.
            </p>
            <Button onClick={() => createReport.mutate()} disabled={createReport.isPending}>
              {createReport.isPending ? "Creando…" : "Crear reporte"}
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <ReportEditor
      tenantId={tenantId}
      report={myReport}
      periodName={periodName}
      periodStart={periodStart}
      periodEnd={periodEnd}
      weeklyThreshold={weeklyThreshold}
      canGoPrev={canGoPrev}
      canGoNext={canGoNext}
      onPrev={onPrev}
      onNext={onNext}
    />
  );
}

function PeriodNav({
  canGoPrev,
  canGoNext,
  onPrev,
  onNext,
}: {
  canGoPrev: boolean;
  canGoNext: boolean;
  onPrev: () => void;
  onNext: () => void;
}) {
  return (
    <div className="flex items-center gap-1">
      <Button variant="outline" size="icon" disabled={!canGoPrev} onClick={onPrev}>
        <ChevronLeft className="size-4" />
      </Button>
      <Button variant="outline" size="icon" disabled={!canGoNext} onClick={onNext}>
        <ChevronRight className="size-4" />
      </Button>
    </div>
  );
}

function ReportEditor({
  tenantId,
  report,
  periodName,
  periodStart,
  periodEnd,
  weeklyThreshold,
  canGoPrev,
  canGoNext,
  onPrev,
  onNext,
}: {
  tenantId: number;
  report: TimeReportOut;
  periodName: string;
  periodStart: string;
  periodEnd: string;
  weeklyThreshold: number;
  canGoPrev: boolean;
  canGoNext: boolean;
  onPrev: () => void;
  onNext: () => void;
}) {
  const qc = useQueryClient();

  const entries = useQuery({
    queryKey: ["time-entries", tenantId, report.id],
    queryFn: async () => {
      const { data, error } = await listTimeEntriesApiV1TenantsTenantIdReportsReportIdEntriesGet({
        path: { tenant_id: tenantId, report_id: report.id },
      });
      if (error || !data) throw error;
      return data;
    },
  });

  const invalidateEntries = () =>
    qc.invalidateQueries({ queryKey: ["time-entries", tenantId, report.id] });

  const createEntry = useMutation({
    mutationFn: async (body: { date: string; hours: number }) => {
      const { data, error } = await createTimeEntryApiV1TenantsTenantIdReportsReportIdEntriesPost({
        path: { tenant_id: tenantId, report_id: report.id },
        body: { date: body.date, hours: body.hours },
      });
      if (error || !data) throw error;
      return data;
    },
    onSuccess: invalidateEntries,
  });

  const updateEntry = useMutation({
    mutationFn: async ({ id, date, hours }: { id: number; date: string; hours: number }) => {
      const { data, error } =
        await updateTimeEntryApiV1TenantsTenantIdReportsReportIdEntriesEntryIdPut({
          path: { tenant_id: tenantId, report_id: report.id, entry_id: id },
          body: { date, hours },
        });
      if (error || !data) throw error;
      return data;
    },
    onSuccess: invalidateEntries,
  });

  const deleteEntry = useMutation({
    mutationFn: async (id: number) => {
      const { error } =
        await deleteTimeEntryApiV1TenantsTenantIdReportsReportIdEntriesEntryIdDelete({
          path: { tenant_id: tenantId, report_id: report.id, entry_id: id },
        });
      if (error) throw error;
    },
    onSuccess: invalidateEntries,
  });

  const submitReport = useMutation({
    mutationFn: async () => {
      const { data, error } = await submitTimeReportApiV1TenantsTenantIdReportsReportIdSubmitPost({
        path: { tenant_id: tenantId, report_id: report.id },
      });
      if (error || !data) throw error;
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({
        queryKey: ["time-tracking", "period-reports", tenantId, report.period_id],
      });
      qc.invalidateQueries({
        queryKey: ["periods", tenantId, report.period_id, "reports"],
      });
      qc.invalidateQueries({ queryKey: ["time-report", tenantId, report.id] });
      toast.success("Reporte enviado para aprobación");
    },
    onError: () => toast.error("No se pudo enviar el reporte"),
  });

  const entryByDate = useMemo(() => {
    const m = new Map<string, TimeEntryOut>();
    for (const e of entries.data ?? []) m.set(e.date, e);
    return m;
  }, [entries.data]);

  const days = useMemo(() => eachDay(periodStart, periodEnd), [periodStart, periodEnd]);

  const totalHours = useMemo(
    () => (entries.data ?? []).reduce((s, e) => s + Number(e.hours), 0),
    [entries.data],
  );
  const overtime = Math.max(0, totalHours - weeklyThreshold);

  const editable = report.status === "draft" || report.status === "rejected";

  function commitHours(date: string, raw: string) {
    const hours = clamp(Number(raw), 0, 24);
    const existing = entryByDate.get(date);
    if (Number.isNaN(hours)) return;
    if (existing) {
      if (Number(existing.hours) === hours) return;
      if (hours === 0) {
        deleteEntry.mutate(existing.id);
      } else {
        updateEntry.mutate({ id: existing.id, date, hours });
      }
    } else if (hours > 0) {
      createEntry.mutate({ date, hours });
    }
  }

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between flex-wrap gap-3">
        <div>
          <CardTitle className="text-base">{periodName}</CardTitle>
          <div className="flex items-center gap-2 mt-1.5">
            <Badge
              variant="outline"
              className={cn("capitalize", statusStyle[report.status] ?? statusStyle.draft)}
            >
              {report.status}
            </Badge>
            <span className="text-xs text-muted-foreground">
              {totalHours.toFixed(2)} h totales
              {overtime > 0 && (
                <span className="text-warning-foreground"> · {overtime.toFixed(2)} h extra</span>
              )}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <PeriodNav canGoPrev={canGoPrev} canGoNext={canGoNext} onPrev={onPrev} onNext={onNext} />
          <Button
            onClick={() => submitReport.mutate()}
            disabled={!editable || totalHours === 0 || submitReport.isPending}
          >
            <Send className="size-4 mr-2" />
            {submitReport.isPending ? "Enviando…" : "Enviar para aprobación"}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        {entries.isLoading ? (
          <div className="p-6">
            <Skeleton className="h-24 w-full" />
          </div>
        ) : (
          <div
            className="grid border-t"
            style={{
              gridTemplateColumns: `repeat(${Math.min(days.length, 7)}, minmax(0, 1fr))`,
            }}
          >
            {days.slice(0, 31).map((date) => (
              <DayCell
                key={date}
                date={date}
                entry={entryByDate.get(date)}
                disabled={!editable}
                onCommit={(v) => commitHours(date, v)}
              />
            ))}
          </div>
        )}
        <div className="border-t bg-muted/30 px-4 py-3 flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Total del periodo</span>
          <span className="font-mono font-semibold">{totalHours.toFixed(2)} h</span>
        </div>
      </CardContent>
    </Card>
  );
}

function DayCell({
  date,
  entry,
  disabled,
  onCommit,
}: {
  date: string;
  entry: TimeEntryOut | undefined;
  disabled: boolean;
  onCommit: (raw: string) => void;
}) {
  const initial = entry ? String(Number(entry.hours)) : "";
  const [value, setValue] = useState(initial);

  useEffect(() => {
    setValue(entry ? String(Number(entry.hours)) : "");
  }, [entry]);

  return (
    <div className="border-r last:border-r-0 border-b lg:border-b-0 p-4">
      <div className="text-xs text-muted-foreground uppercase tracking-wide">{dayLabel(date)}</div>
      <div className="text-sm font-medium mt-0.5">{fmtDate(date)}</div>
      <Input
        type="number"
        min={0}
        max={24}
        step={0.25}
        disabled={disabled}
        value={value}
        placeholder="0"
        onChange={(e) => setValue(e.target.value)}
        onBlur={() => onCommit(value || "0")}
        onKeyDown={(e) => {
          if (e.key === "Enter") (e.target as HTMLInputElement).blur();
        }}
        className="mt-3 h-9 text-center font-mono"
      />
    </div>
  );
}

function clamp(n: number, min: number, max: number) {
  if (Number.isNaN(n)) return n;
  return Math.max(min, Math.min(max, n));
}
