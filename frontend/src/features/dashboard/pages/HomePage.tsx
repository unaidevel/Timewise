import type { ReactNode } from "react";
import { Link } from "react-router";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Spinner } from "@/components/ui/Spinner";
import { useApprovals } from "@/features/approvals/hooks";
import { useDepartments } from "@/features/departments/hooks";
import { useEmployees } from "@/features/employees/hooks";
import { usePeriods } from "@/features/periods/hooks";
import { useCurrentTenantId } from "@/features/tenants/hooks";

export default function HomePage() {
  const tenantId = useCurrentTenantId();

  if (tenantId == null) {
    return <NoTenantState />;
  }

  return <DashboardStats tenantId={tenantId} />;
}

function NoTenantState() {
  return (
    <Card>
      <CardHeader
        title="Bienvenido a TimeWise"
        description="Necesitas crear o seleccionar una organización"
      />
      <CardBody>
        <Link to="/onboarding" className="font-medium text-slate-900 underline">
          Crear primera organización →
        </Link>
      </CardBody>
    </Card>
  );
}

function DashboardStats({ tenantId }: { tenantId: number }) {
  const employees = useEmployees(tenantId);
  const departments = useDepartments(tenantId);
  const periods = usePeriods(tenantId);
  const approvals = useApprovals(tenantId);
  const pendingApprovals = approvals.data?.filter((a) => a.status === "pending").length;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Empleados" value={employees.data?.length} link="/employees" />
        <StatCard label="Departamentos" value={departments.data?.length} link="/departments" />
        <StatCard label="Periodos" value={periods.data?.length} link="/periods" />
        <StatCard label="Aprobaciones pendientes" value={pendingApprovals} link="/approvals" />
      </div>

      <Card>
        <CardHeader title="Acciones rápidas" />
        <CardBody>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <QuickAction
              to="/employees"
              title="Gestionar empleados"
              description="Alta, baja, datos de contrato"
            />
            <QuickAction
              to="/periods"
              title="Periodos de imputación"
              description="Crea o bloquea ventanas temporales"
            />
            <QuickAction
              to="/approvals"
              title="Revisar aprobaciones"
              description="Aprueba o rechaza reportes"
            />
          </div>
        </CardBody>
      </Card>
    </div>
  );
}

function StatCard({
  label,
  value,
  link,
}: {
  label: string;
  value: number | undefined;
  link: string;
}) {
  return (
    <Link to={link}>
      <Card className="transition-shadow hover:shadow-md">
        <CardBody>
          <div className="text-xs uppercase tracking-wider text-slate-500">{label}</div>
          <div className="mt-2 text-3xl font-semibold text-slate-900">
            {value ?? ((<Spinner />) as ReactNode)}
          </div>
        </CardBody>
      </Card>
    </Link>
  );
}

function QuickAction({
  to,
  title,
  description,
}: {
  to: string;
  title: string;
  description: string;
}) {
  return (
    <Link
      to={to}
      className="block rounded-md border border-slate-200 p-4 transition-colors hover:bg-slate-50"
    >
      <div className="font-medium text-slate-900">{title}</div>
      <div className="mt-1 text-sm text-slate-600">{description}</div>
    </Link>
  );
}
