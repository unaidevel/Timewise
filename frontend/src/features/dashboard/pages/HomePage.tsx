import { motion } from "framer-motion";
import { ArrowUpRight, CheckSquare, Clock, DollarSign, MoreHorizontal, Users } from "lucide-react";
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
import { Avatar, AvatarFallback } from "@/components/shadcn/avatar";
import { Badge } from "@/components/shadcn/badge";
import { Button } from "@/components/shadcn/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/shadcn/card";
import { useApprovals } from "@/features/approvals/hooks";
import { useAuthStore } from "@/features/auth/store";
import { useDepartments } from "@/features/departments/hooks";
import { useEmployees } from "@/features/employees/hooks";
import { DemoDataBanner } from "@/features/onboarding/components/DemoDataBanner";
import { usePeriods } from "@/features/periods/hooks";
import { useCurrentTenantId } from "@/features/tenants/hooks";

// Placeholder data for charts and activity feed.
// TODO: replace once backend exposes aggregation endpoints (cost trend, hours by department, recent activity).
const costTrend = [
  { day: "Sem 1", cost: 62000 },
  { day: "Sem 2", cost: 71500 },
  { day: "Sem 3", cost: 68900 },
  { day: "Sem 4", cost: 81910 },
];

const hoursByDept = [
  { dept: "Engineering", base: 1840, ot: 220 },
  { dept: "Product", base: 1120, ot: 90 },
  { dept: "Design", base: 760, ot: 40 },
  { dept: "Operations", base: 1480, ot: 180 },
  { dept: "Sales", base: 980, ot: 60 },
  { dept: "Support", base: 720, ot: 95 },
];

const activity = [
  { who: "Maya Patel", action: "envió un parte de horas", when: "hace 12m" },
  { who: "James O'Connor", action: "aprobó 3 reportes", when: "hace 1h" },
  { who: "Lina Hoffmann", action: "añadió una regla de horas extra", when: "hace 3h" },
  { who: "Diego Alvarez", action: "se unió a Engineering", when: "ayer" },
];

export default function HomePage() {
  const tenantId = useCurrentTenantId();
  if (tenantId == null) return <NoTenantState />;
  return <Dashboard tenantId={tenantId} />;
}

function NoTenantState() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Bienvenido a TimeWise</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground mb-4">
          Necesitas crear o seleccionar una organización para empezar.
        </p>
        <Link to="/onboarding" className="text-sm font-medium text-primary hover:underline">
          Crear primera organización →
        </Link>
      </CardContent>
    </Card>
  );
}

function Dashboard({ tenantId }: { tenantId: number }) {
  const user = useAuthStore((s) => s.user);
  const employees = useEmployees(tenantId);
  const departments = useDepartments(tenantId);
  const periods = usePeriods(tenantId);
  const approvals = useApprovals(tenantId);
  const pendingApprovals = approvals.data?.filter((a) => a.status === "pending").length;

  const today = new Date();
  const fmt = new Intl.DateTimeFormat("es-ES", { weekday: "long", day: "numeric", month: "long" });

  const kpis = [
    {
      label: "Empleados activos",
      value: employees.data?.length,
      icon: Users,
      delta: "+0",
    },
    {
      label: "Aprobaciones pendientes",
      value: pendingApprovals,
      icon: CheckSquare,
      delta: "0",
    },
    {
      label: "Periodos",
      value: periods.data?.length,
      icon: Clock,
      delta: "0",
    },
    {
      label: "Departamentos",
      value: departments.data?.length,
      icon: DollarSign,
      delta: "0",
    },
  ];

  return (
    <div className="space-y-8">
      <DemoDataBanner />
      <header className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <p className="text-sm text-muted-foreground capitalize">{fmt.format(today)}</p>
          <h1 className="text-3xl font-semibold tracking-tight mt-1">
            Hola, {user?.full_name?.split(" ")[0] ?? "bienvenido"}
          </h1>
          <p className="text-sm text-muted-foreground mt-1">Resumen del workspace.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">Exportar</Button>
          <Button>Nuevo reporte</Button>
        </div>
      </header>

      <section className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
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

      <section className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2">
          <CardHeader className="flex-row items-center justify-between">
            <div>
              <CardTitle className="text-base">Tendencia de coste laboral</CardTitle>
              <p className="text-xs text-muted-foreground mt-1">Últimas 4 semanas (placeholder)</p>
            </div>
            <Button variant="ghost" size="icon">
              <MoreHorizontal className="size-4" />
            </Button>
          </CardHeader>
          <CardContent>
            <div className="h-[260px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={costTrend} margin={{ left: -10, right: 8, top: 6 }}>
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
                    dataKey="day"
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
                    tickFormatter={(v) => `${v / 1000}k €`}
                  />
                  <Tooltip
                    contentStyle={{
                      background: "var(--color-popover)",
                      border: "1px solid var(--color-border)",
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                    formatter={(v: number) => `${v.toLocaleString()} €`}
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
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Acciones rápidas</CardTitle>
            <p className="text-xs text-muted-foreground">Atajos del workspace</p>
          </CardHeader>
          <CardContent className="space-y-3">
            <QuickAction to="/employees" title="Gestionar empleados" />
            <QuickAction to="/periods" title="Periodos de imputación" />
            <QuickAction to="/approvals" title="Revisar aprobaciones" />
            <QuickAction to="/costing-rules" title="Reglas de coste" />
          </CardContent>
        </Card>
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Horas por departamento</CardTitle>
            <p className="text-xs text-muted-foreground">
              Base vs. extra · placeholder hasta tener endpoint de agregación
            </p>
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
                <span className="size-2.5 rounded-sm bg-primary" /> Horas base
              </div>
              <div className="flex items-center gap-1.5">
                <span className="size-2.5 rounded-sm bg-chart-3" /> Horas extra
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Actividad reciente</CardTitle>
            <p className="text-xs text-muted-foreground">Placeholder</p>
          </CardHeader>
          <CardContent className="space-y-4">
            {activity.map((a, i) => (
              <motion.div
                key={a.who}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
                className="flex gap-3"
              >
                <Avatar className="size-8 mt-0.5">
                  <AvatarFallback className="text-[10px] bg-primary/10 text-primary font-semibold">
                    {a.who
                      .split(" ")
                      .map((n) => n[0])
                      .join("")}
                  </AvatarFallback>
                </Avatar>
                <div className="flex-1 min-w-0">
                  <p className="text-sm leading-tight">
                    <span className="font-medium">{a.who}</span>{" "}
                    <span className="text-muted-foreground">{a.action}</span>
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">{a.when}</p>
                </div>
              </motion.div>
            ))}
          </CardContent>
        </Card>
      </section>
    </div>
  );
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
