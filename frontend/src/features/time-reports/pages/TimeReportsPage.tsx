import { useQueries } from "@tanstack/react-query";
import { m } from "framer-motion";
import { ArrowRight, Clock, Filter, Search } from "lucide-react";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";
import { listTimeReportsForPeriodApiV1TenantsTenantIdPeriodsPeriodIdReportsGet } from "@/client";
import { EmptyState } from "@/components/EmptyState";
import { Badge } from "@/components/shadcn/badge";
import { Card, CardContent } from "@/components/shadcn/card";
import { Input } from "@/components/shadcn/input";
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
import { Tabs, TabsList, TabsTrigger } from "@/components/shadcn/tabs";
import { usePeriods } from "@/features/periods/hooks";
import { useCurrentTenantId, useIsTenantAdmin } from "@/features/tenants/hooks";
import { formatDate } from "@/lib/format";
import { cn } from "@/lib/utils";

type Scope = "mine" | "all";

const statusStyle: Record<string, string> = {
  draft: "bg-muted text-muted-foreground border-border",
  submitted: "bg-warning/20 text-warning-foreground border-warning/30",
  approved: "bg-success/15 text-success border-success/20",
  rejected: "bg-destructive/15 text-destructive border-destructive/20",
};

export default function TimeReportsPage() {
  const tenantId = useCurrentTenantId();
  const isAdmin = useIsTenantAdmin(tenantId);
  const periods = usePeriods(tenantId);
  const { t } = useTranslation();
  const [q, setQ] = useState("");
  const [status, setStatus] = useState<"all" | "draft" | "submitted" | "approved" | "rejected">(
    "all",
  );
  const [scope, setScope] = useState<Scope>("all");
  const effectiveScope: Scope = isAdmin ? scope : "mine";

  const reportQueries = useQueries({
    queries: (periods.data ?? []).map((period) => ({
      queryKey: ["periods", tenantId, period.id, "reports", effectiveScope],
      enabled: tenantId != null,
      queryFn: async () => {
        const { data, error } =
          await listTimeReportsForPeriodApiV1TenantsTenantIdPeriodsPeriodIdReportsGet({
            path: { tenant_id: tenantId!, period_id: period.id },
            query: { scope: effectiveScope },
          });
        if (error || !data) throw error;
        return data.map((r) => ({ ...r, period }));
      },
    })),
  });

  const isLoading = periods.isLoading || reportQueries.some((r) => r.isLoading);
  const reports = useMemo(() => reportQueries.flatMap((r) => r.data ?? []), [reportQueries]);

  const filtered = useMemo(() => {
    return reports.filter((r) => {
      if (status !== "all" && r.status !== status) return false;
      if (q) {
        const needle = q.toLowerCase();
        if (
          !(r.period?.name?.toLowerCase().includes(needle) ?? false) &&
          !`#${r.id}`.includes(needle) &&
          !`#${r.employee_id}`.includes(needle)
        )
          return false;
      }
      return true;
    });
  }, [reports, q, status]);

  const total = reports.length;
  const submitted = reports.filter((r) => r.status === "submitted").length;
  const approved = reports.filter((r) => r.status === "approved").length;

  if (!isLoading && total === 0) {
    return (
      <div className="space-y-6">
        <header className="flex items-end justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-3xl font-semibold tracking-tight">
              {t("timekeeping.reports.title")}
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              {t("timekeeping.reports.subtitle")}
            </p>
          </div>
          {isAdmin && (
            <Tabs value={scope} onValueChange={(v) => setScope(v as Scope)}>
              <TabsList>
                <TabsTrigger value="mine">{t("timekeeping.scope.mine")}</TabsTrigger>
                <TabsTrigger value="all">{t("timekeeping.scope.all")}</TabsTrigger>
              </TabsList>
            </Tabs>
          )}
        </header>
        <EmptyState
          icon={Clock}
          title={t("timekeeping.reports.empty.title")}
          description={t("timekeeping.reports.empty.description")}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <header className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">
            {t("timekeeping.reports.title")}
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            {t("timekeeping.reports.summary", { total, submitted, approved })}
          </p>
        </div>
        {isAdmin && (
          <Tabs value={scope} onValueChange={(v) => setScope(v as Scope)}>
            <TabsList>
              <TabsTrigger value="mine">{t("timekeeping.scope.mine")}</TabsTrigger>
              <TabsTrigger value="all">{t("timekeeping.scope.all")}</TabsTrigger>
            </TabsList>
          </Tabs>
        )}
      </header>

      <div data-tour="reports-filters" className="flex flex-wrap gap-2 items-center">
        <div className="relative flex-1 min-w-[220px] max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
          <Input
            placeholder={t("timekeeping.reports.searchPlaceholder")}
            className="pl-9"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        </div>
        <Select value={status} onValueChange={(v) => setStatus(v as typeof status)}>
          <SelectTrigger className="w-[180px]">
            <Filter className="size-3.5 mr-1.5" />
            <SelectValue placeholder={t("timekeeping.reports.filterStatusPlaceholder")} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{t("timekeeping.reports.statusAll")}</SelectItem>
            <SelectItem value="draft">{t("timekeeping.reports.statusDraft")}</SelectItem>
            <SelectItem value="submitted">{t("timekeeping.reports.statusSubmitted")}</SelectItem>
            <SelectItem value="approved">{t("timekeeping.reports.statusApproved")}</SelectItem>
            <SelectItem value="rejected">{t("timekeeping.reports.statusRejected")}</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Card data-tour="reports-table">
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead>{t("timekeeping.reports.columns.id")}</TableHead>
                <TableHead>{t("timekeeping.reports.columns.period")}</TableHead>
                <TableHead>{t("timekeeping.reports.columns.employee")}</TableHead>
                <TableHead>{t("timekeeping.reports.columns.status")}</TableHead>
                <TableHead>{t("timekeeping.reports.columns.submitted")}</TableHead>
                <TableHead className="text-right">
                  {t("timekeeping.reports.columns.action")}
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading &&
                ["a", "b", "c", "d", "e"].map((row) => (
                  <TableRow key={row}>
                    {["id", "period", "emp", "status", "sub", "act"].map((col) => (
                      <TableCell key={col}>
                        <Skeleton className="h-5 w-24" />
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              {filtered.map((r, i) => (
                <m.tr
                  key={r.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: Math.min(i * 0.015, 0.2) }}
                  className="border-b hover:bg-muted/40 transition"
                >
                  <TableCell className="font-mono text-sm">#{r.id}</TableCell>
                  <TableCell className="font-medium">{r.period?.name ?? "—"}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">#{r.employee_id}</TableCell>
                  <TableCell>
                    <Badge
                      variant="outline"
                      className={cn("capitalize", statusStyle[r.status] ?? statusStyle.draft)}
                    >
                      {r.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm">{formatDate(r.submitted_at)}</TableCell>
                  <TableCell className="text-right">
                    <Link
                      to={`/reports/${r.id}`}
                      className="inline-flex items-center text-sm font-medium text-primary hover:underline"
                    >
                      {t("timekeeping.reports.view")} <ArrowRight className="size-3.5 ml-1" />
                    </Link>
                  </TableCell>
                </m.tr>
              ))}
              {!isLoading && filtered.length === 0 && (
                <TableRow>
                  <TableCell
                    colSpan={6}
                    className="text-center text-sm text-muted-foreground py-12"
                  >
                    {t("timekeeping.reports.noMatch")}
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
