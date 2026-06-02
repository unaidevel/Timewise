import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, ChevronLeft, ChevronRight, Clock, Send } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
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
  const { t } = useTranslation();
  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("timekeeping.time.noTenant.title")}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground mb-4">
          {t("timekeeping.time.noTenant.description")}
        </p>
        <Link to="/onboarding" className="text-sm font-medium text-primary hover:underline">
          {t("timekeeping.time.noTenant.cta")}
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
  const { t } = useTranslation();

  const sortedPeriods = useMemo(
    () => (periods.data ?? []).toSorted((a, b) => b.start_date.localeCompare(a.start_date)),
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
    // False positive: one-time lazy init of a user-selectable value from an
    // external store (localStorage) + async data, not a prop mirror. Guarded to
    // run once; user overrides it afterward, so it can't be derived in render.
    // react-doctor-disable-next-line react-doctor/no-derived-state
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
        <h1 className="text-3xl font-semibold tracking-tight">{t("timekeeping.time.title")}</h1>
        <EmptyState
          icon={Clock}
          title={t("timekeeping.time.noPeriods.title")}
          description={t("timekeeping.time.noPeriods.description")}
        />
      </div>
    );
  }

  if (employees.isSuccess && (employees.data?.length ?? 0) === 0) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-semibold tracking-tight">{t("timekeeping.time.title")}</h1>
        <EmptyState
          icon={Clock}
          title={t("timekeeping.time.noEmployees.title")}
          description={t("timekeeping.time.noEmployees.description")}
        />
      </div>
    );
  }

  const meEmployee = employees.data?.find((e) => e.id === employeeId) ?? null;
  const canShowGrid = activePeriod != null && meEmployee != null;

  return (
    <div className="space-y-6">
      <header data-tour="time-header" className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">{t("timekeeping.time.title")}</h1>
          {meEmployee ? (
            <p className="text-sm text-muted-foreground mt-1">
              {t("timekeeping.time.loggingAs")}{" "}
              <span className="font-medium text-foreground">{meEmployee.full_name}</span>
            </p>
          ) : (
            <p className="text-sm text-muted-foreground mt-1">
              {t("timekeeping.time.selectEmployeePrompt")}
            </p>
          )}
        </div>
        {(employees.data?.length ?? 0) > 1 && (
          <Select
            value={employeeId != null ? String(employeeId) : undefined}
            onValueChange={(v) => setEmployeeId(Number(v))}
          >
            <SelectTrigger className="w-[240px]">
              <SelectValue placeholder={t("timekeeping.time.selectEmployeePlaceholder")} />
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

      <Card data-tour="time-periods-list">
        <CardHeader>
          <CardTitle className="text-base">{t("timekeeping.time.recentPeriods")}</CardTitle>
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
      <NoReportCard
        periodName={periodName}
        periodStart={periodStart}
        periodEnd={periodEnd}
        canGoPrev={canGoPrev}
        canGoNext={canGoNext}
        onPrev={onPrev}
        onNext={onNext}
        isCreating={createReport.isPending}
        onCreate={() => createReport.mutate()}
      />
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

function NoReportCard({
  periodName,
  periodStart,
  periodEnd,
  canGoPrev,
  canGoNext,
  onPrev,
  onNext,
  isCreating,
  onCreate,
}: {
  periodName: string;
  periodStart: string;
  periodEnd: string;
  canGoPrev: boolean;
  canGoNext: boolean;
  onPrev: () => void;
  onNext: () => void;
  isCreating: boolean;
  onCreate: () => void;
}) {
  const { t } = useTranslation();
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
          <p className="text-sm text-muted-foreground">{t("timekeeping.time.noReportYet")}</p>
          <Button data-tour="time-create-report" onClick={onCreate} disabled={isCreating}>
            {isCreating ? t("timekeeping.time.creating") : t("timekeeping.time.createReport")}
          </Button>
        </div>
      </CardContent>
    </Card>
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
  const { t } = useTranslation();

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
      toast.success(t("timekeeping.time.submittedToast"));
    },
    onError: () => toast.error(t("timekeeping.time.submitErrorToast")),
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
    <Card data-tour="time-grid">
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
              {totalHours.toFixed(2)} {t("timekeeping.time.totalHoursSuffix")}
              {overtime > 0 && (
                <span className="text-warning-foreground">
                  {" "}
                  · {overtime.toFixed(2)} {t("timekeeping.time.overtimeSuffix")}
                </span>
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
            {submitReport.isPending
              ? t("timekeeping.time.submitting")
              : t("timekeeping.time.submit")}
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
                key={`${date}:${entryByDate.get(date)?.hours ?? ""}`}
                date={date}
                entry={entryByDate.get(date)}
                disabled={!editable}
                onCommit={(v) => commitHours(date, v)}
              />
            ))}
          </div>
        )}
        <div className="border-t bg-muted/30 px-4 py-3 flex items-center justify-between text-sm">
          <span className="text-muted-foreground">{t("timekeeping.time.periodTotal")}</span>
          <span className="font-mono font-semibold">
            {totalHours.toFixed(2)} {t("timekeeping.time.totalHoursShort")}
          </span>
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
  const [value, setValue] = useState(entry ? String(Number(entry.hours)) : "");

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
