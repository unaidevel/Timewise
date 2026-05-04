import { useQueries } from "@tanstack/react-query";
import { Link } from "react-router";
import { listTimeReportsForPeriodApiV1TenantsTenantIdPeriodsPeriodIdReportsGet } from "@/client";
import { Badge } from "@/components/ui/Badge";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyRow, Table, Td, Th } from "@/components/ui/Table";
import { usePeriods } from "@/features/periods/hooks";
import { useCurrentTenantId } from "@/features/tenants/hooks";
import { formatDate } from "@/lib/format";

export default function TimeReportsPage() {
  const tenantId = useCurrentTenantId();
  const { data: periods = [], isLoading: loadingPeriods } = usePeriods(tenantId);

  const reportQueries = useQueries({
    queries: periods.map((period) => ({
      queryKey: ["periods", tenantId, period.id, "reports"],
      enabled: tenantId != null,
      queryFn: async () => {
        const { data, error } =
          await listTimeReportsForPeriodApiV1TenantsTenantIdPeriodsPeriodIdReportsGet({
            path: { tenant_id: tenantId!, period_id: period.id },
          });
        if (error || !data) throw error;
        return data.map((r) => ({ ...r, period }));
      },
    })),
  });

  const isLoading = loadingPeriods || reportQueries.some((q) => q.isLoading);
  const reports = reportQueries.flatMap((q) => q.data ?? []);

  return (
    <Card>
      <CardHeader title="Reportes" description="Todos los reportes de tiempo del tenant" />
      <CardBody className="p-0">
        {isLoading ? (
          <div className="flex justify-center p-8">
            <Spinner />
          </div>
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>ID</Th>
                <Th>Periodo</Th>
                <Th>Empleado</Th>
                <Th>Estado</Th>
                <Th>Versión</Th>
                <Th>Enviado</Th>
                <Th></Th>
              </tr>
            </thead>
            <tbody>
              {reports.length === 0 && <EmptyRow colSpan={7} message="Sin reportes." />}
              {reports.map((r) => (
                <tr key={r.id}>
                  <Td>#{r.id}</Td>
                  <Td>{r.period.name}</Td>
                  <Td>#{r.employee_id}</Td>
                  <Td>
                    <Badge status={r.status}>{r.status}</Badge>
                  </Td>
                  <Td>v{r.version}</Td>
                  <Td>{formatDate(r.submitted_at)}</Td>
                  <Td className="text-right">
                    <Link
                      to={`/reports/${r.id}`}
                      className="text-sm font-medium text-slate-900 hover:underline"
                    >
                      Ver →
                    </Link>
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </CardBody>
    </Card>
  );
}
