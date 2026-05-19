import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router";
import { Badge } from "@/components/ui/Badge";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Spinner } from "@/components/ui/Spinner";
import { useCurrentTenantId } from "@/features/tenants/hooks";
import { formatDate } from "@/lib/format";
import { useEmployee } from "../hooks";

export default function EmployeeDetailPage() {
  const { id } = useParams<{ id: string }>();
  const tenantId = useCurrentTenantId();
  const employeeId = id ? Number(id) : null;
  const { data: employee, isLoading } = useEmployee(tenantId, employeeId);
  const { t } = useTranslation();

  if (isLoading)
    return (
      <div className="flex justify-center p-8">
        <Spinner />
      </div>
    );
  if (!employee) return <p className="text-slate-600">{t("workforce.employees.notFound")}</p>;

  return (
    <div className="space-y-4">
      <Link to="/employees" className="text-sm text-slate-600 hover:underline">
        {t("workforce.employees.backToList")}
      </Link>

      <Card>
        <CardHeader
          title={employee.full_name}
          description={employee.email}
          action={
            <Badge status={employee.is_active ? "active" : "inactive"}>
              {employee.is_active ? t("common.active") : t("common.inactive")}
            </Badge>
          }
        />
        <CardBody>
          <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Field
              label={t("workforce.employees.fields.hireDate")}
              value={formatDate(employee.hired_at)}
            />
            <Field
              label={t("workforce.employees.fields.manager")}
              value={employee.manager_id ? `#${employee.manager_id}` : "—"}
            />
            <Field label={t("workforce.employees.fields.id")} value={`#${employee.id}`} />
            <Field
              label={t("workforce.employees.fields.createdAt")}
              value={formatDate(employee.created_at)}
            />
          </dl>
        </CardBody>
      </Card>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wider text-slate-500">{label}</dt>
      <dd className="mt-1 text-sm font-medium text-slate-900">{value}</dd>
    </div>
  );
}
