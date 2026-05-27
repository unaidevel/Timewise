import { motion } from "framer-motion";
import { ArrowUpRight, CheckSquare, Clock, DollarSign, MoreHorizontal, Users } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { getHourInTimezone, LiveClock, useNow } from "@/components/LiveClock";
import { Badge } from "@/components/shadcn/badge";
import { Button } from "@/components/shadcn/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/shadcn/card";
import { Skeleton } from "@/components/shadcn/skeleton";
import { RecentActivity } from "@/features/activity/RecentActivity";
import { useApprovals } from "@/features/approvals/hooks";
import { useAuthStore } from "@/features/auth/store";
import { useCostTrend } from "@/features/costing/hooks";
import { useDepartments } from "@/features/departments/hooks";
import { useEmployees } from "@/features/employees/hooks";
import { usePeriods } from "@/features/periods/hooks";
import { useCurrentTenantId, useOrganizationProfile } from "@/features/tenants/hooks";

// Placeholder data for charts.
// TODO: replace once backend exposes aggregation endpoints (hours by department).
const hoursByDept = [
  { dept: "Engineering", base: 1840, ot: 220 },
  { dept: "Product", base: 1120, ot: 90 },
  { dept: "Design", base: 760, ot: 40 },
  { dept: "Operations", base: 1480, ot: 180 },
  { dept: "Sales", base: 980, ot: 60 },
  { dept: "Support", base: 720, ot: 95 },
];

export default function HomePage() {
  const tenantId = useCurrentTenantId();
  if (tenantId == null) return <NoTenantState />;
  return <Dashboard tenantId={tenantId} />;
}

function NoTenantState() {
  const { t } = useTranslation();
  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("dashboard.noTenant.title")}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground mb-4">{t("dashboard.noTenant.description")}</p>
        <Link to="/onboarding" className="text-sm font-medium text-primary hover:underline">
          {t("dashboard.noTenant.cta")}
        </Link>
      </CardContent>
    </Card>
  );
}

function Dashboard({ tenantId }: { tenantId: number }) {
  const user = useAuthStore((s) => s.user);
  const { t, i18n } = useTranslation();
  const employees = useEmployees(tenantId);
  const departments = useDepartments(tenantId);
  const periods = usePeriods(tenantId);
  const approvals = useApprovals(tenantId);
  const profile = useOrganizationProfile(tenantId);
  const costTrend = useCostTrend(tenantId);
  const currency = profile.data?.currency ?? "EUR";
  const pendingApprovals = approvals.data?.filter((a) => a.status === "pending").length;

  const now = useNow();
  const locale = i18n.resolvedLanguage === "es" ? "es-ES" : "en-US";
  const timezone = user?.timezone || profile.data?.timezone || undefined;
  const hour = getHourInTimezone(now, timezone);
  const greeting =
    hour < 12
      ? t("dashboard.greetingMorning")
      : hour < 18
        ? t("dashboard.greetingAfternoon")
        : t("dashboard.greetingEvening");

  const kpis = [
    {
      label: t("dashboard.kpi.activeEmployees"),
      value: employees.data?.length,
      icon: Users,
      delta: "+0",
    },
    {
      label: t("dashboard.kpi.pendingApprovals"),
      value: pendingApprovals,
      icon: CheckSquare,
      delta: "0",
    },
    {
      label: t("dashboard.kpi.periods"),
      value: periods.data?.length,
      icon: Clock,
      delta: "0",
    },
    {
      label: t("dashboard.kpi.departments"),
      value: departments.data?.length,
      icon: DollarSign,
      delta: "0",
    },
  ];

  return (
    <div className="space-y-8">
      <header className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">
            {greeting}, {user?.full_name?.split(" ")[0] ?? t("dashboard.greetingFallback")}
          </h1>
          <p className="text-sm text-muted-foreground mt-1">{t("dashboard.summary")}</p>
        </div>
        <LiveClock
          className="text-right [&>div:first-child]:text-5xl [&>div:first-child]:font-light [&>div:last-child]:text-sm [&>div:last-child]:mt-1.5"
          locale={locale}
          timezone={timezone}
          showSeconds
        />
      </header>

      <section
        data-tour="dashboard-kpis"
        className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4"
      >
        {kpis.map((k, i) => (
          <motion.div
            key={k.label}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
          >
            <Card className="overflow-hidden border bg-card hover:shadow-[var(--shadow-elegant)] transition-shadow">
              <CardContent className="p-5">
                <div className="flex items-center justify-between">
                  <div className="size-9 rounded-lg bg-primary/10 text-primary grid place-items-center">
                    <k.icon className="size-4" />
                  </div>
                  <Badge variant="secondary" className="gap-1 font-normal">
                    <ArrowUpRight className="size-3" />
                    {k.delta}
                  </Badge>
                </div>
                <div className="mt-5">
                  <div className="text-2xl font-semibold tracking-tight">{k.value ?? "—"}</div>
                  <div className="text-xs text-muted-foreground mt-1">{k.label}</div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </section>

      <section data-tour="dashboard-charts" className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2" data-tour="dashboard-cost-trend">
          <CardHeader className="flex-row items-center justify-between">
            <div>
              <CardTitle className="text-base">{t("dashboard.costTrend.title")}</CardTitle>
              <p className="text-xs text-muted-foreground mt-1">
                {t("dashboard.costTrend.subtitle")}
              </p>
            </div>
            <Button variant="ghost" size="icon">
              <MoreHorizontal className="size-4" />
            </Button>
          </CardHeader>
          <CardContent>
            <div className="h-[260px]">
              {costTrend.isLoading && costTrend.points.length === 0 ? (
                <Skeleton className="h-full w-full" />
              ) : costTrend.points.length === 0 ? (
                <div className="h-full grid place-items-center text-sm text-muted-foreground">
                  {t("dashboard.costTrend.empty")}
                </div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={costTrend.points} margin={{ left: -10, right: 8, top: 6 }}>
                    <defs>
                      <linearGradient id="costFill" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="var(--color-primary)" stopOpacity={0.3} />
                        <stop offset="100%" stopColor="var(--color-primary)" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid
                      stroke="var(--color-border)"
                      strokeDasharray="3 3"
                      vertical={false}
                    />
                    <XAxis
                      dataKey="label"
                      stroke="var(--color-muted-foreground)"
                      fontSize={12}
                      tickLine={false}
                      axisLine={false}
                    />
                    <YAxis
                      stroke="var(--color-muted-foreground)"
                      fontSize={12}
                      tickLine={false}
                      axisLine={false}
                      tickFormatter={(v) => formatCompactCurrency(v as number, currency, locale)}
                    />
                    <Tooltip
                      contentStyle={{
                        background: "var(--color-popover)",
                        border: "1px solid var(--color-border)",
                        borderRadius: 8,
                        fontSize: 12,
                      }}
                      formatter={(v: number) => formatCurrency(v, currency, locale)}
                    />
                    <Area
                      type="monotone"
                      dataKey="cost"
                      stroke="var(--color-primary)"
                      strokeWidth={2}
                      fill="url(#costFill)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">{t("dashboard.quickActions.title")}</CardTitle>
            <p className="text-xs text-muted-foreground">{t("dashboard.quickActions.subtitle")}</p>
          </CardHeader>
          <CardContent className="space-y-3">
            <QuickAction to="/employees" title={t("dashboard.quickActions.manageEmployees")} />
            <QuickAction to="/periods" title={t("dashboard.quickActions.periods")} />
            <QuickAction to="/approvals" title={t("dashboard.quickActions.approvals")} />
            <QuickAction to="/settings" title={t("dashboard.quickActions.costRules")} />
          </CardContent>
        </Card>
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">{t("dashboard.hoursByDept.title")}</CardTitle>
            <p className="text-xs text-muted-foreground">{t("dashboard.hoursByDept.subtitle")}</p>
          </CardHeader>
          <CardContent>
            <div className="h-[280px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={hoursByDept} margin={{ left: -10, right: 8, top: 6 }}>
                  <CartesianGrid
                    stroke="var(--color-border)"
                    strokeDasharray="3 3"
                    vertical={false}
                  />
                  <XAxis
                    dataKey="dept"
                    stroke="var(--color-muted-foreground)"
                    fontSize={11}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis
                    stroke="var(--color-muted-foreground)"
                    fontSize={12}
                    tickLine={false}
                    axisLine={false}
                  />
                  <Tooltip
                    contentStyle={{
                      background: "var(--color-popover)",
                      border: "1px solid var(--color-border)",
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                  />
                  <Bar dataKey="base" stackId="a" fill="var(--color-primary)" />
                  <Bar dataKey="ot" stackId="a" fill="var(--color-chart-3)" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="flex gap-4 mt-4 text-xs text-muted-foreground">
              <div className="flex items-center gap-1.5">
                <span className="size-2.5 rounded-sm bg-primary" />{" "}
                {t("dashboard.hoursByDept.base")}
              </div>
              <div className="flex items-center gap-1.5">
                <span className="size-2.5 rounded-sm bg-chart-3" />{" "}
                {t("dashboard.hoursByDept.overtime")}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card data-tour="dashboard-activity">
          <CardHeader>
            <CardTitle className="text-base">{t("dashboard.activity.title")}</CardTitle>
            <p className="text-xs text-muted-foreground">{t("dashboard.activity.subtitle")}</p>
          </CardHeader>
          <CardContent>
            <RecentActivity tenantId={tenantId} />
          </CardContent>
        </Card>
      </section>
    </div>
  );
}

function formatCurrency(value: number, currency: string, locale: string): string {
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(value);
}

function formatCompactCurrency(value: number, currency: string, locale: string): string {
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency,
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value);
}

function QuickAction({ to, title }: { to: string; title: string }) {
  return (
    <Link
      to={to}
      className="block rounded-lg border p-3 hover:bg-muted/40 transition text-sm font-medium"
    >
      {title}
    </Link>
  );
}
