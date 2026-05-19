import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Select } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyRow, Table, Td, Th } from "@/components/ui/Table";
import { useEmployees } from "@/features/employees/hooks";
import { useCurrentTenantId } from "@/features/tenants/hooks";
import { formatDate } from "@/lib/format";
import { useCreateTimeReport, usePeriod, usePeriodReports } from "../hooks";

export default function PeriodDetailPage() {
  const { id } = useParams<{ id: string }>();
  const tenantId = useCurrentTenantId();
  const periodId = id ? Number(id) : null;
  const { data: period, isLoading } = usePeriod(tenantId, periodId);
  const { data: reports = [], isLoading: loadingReports } = usePeriodReports(tenantId, periodId);
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);

  if (isLoading)
    return (
      <div className="flex justify-center p-8">
        <Spinner />
      </div>
    );
  if (!period) return <p className="text-muted-foreground">{t("timekeeping.periods.notFound")}</p>;

  return (
    <div className="space-y-4">
      <Link to="/periods" className="text-sm text-muted-foreground hover:underline">
        {t("timekeeping.periods.backToList")}
      </Link>

      <Card>
        <CardHeader
          title={period.name}
          description={`${formatDate(period.start_date)} – ${formatDate(period.end_date)}`}
          action={<Badge status={period.status}>{period.status}</Badge>}
        />
      </Card>

      <Card>
        <CardHeader
          title={t("timekeeping.periods.reports.title")}
          description={t("timekeeping.periods.reports.subtitle")}
          action={
            !period.locked_at && (
              <Button onClick={() => setOpen(true)}>
                {t("timekeeping.periods.reports.createReport")}
              </Button>
            )
          }
        />
        <CardBody className="p-0">
          {loadingReports ? (
            <div className="flex justify-center p-8">
              <Spinner />
            </div>
          ) : (
            <Table>
              <thead>
                <tr>
                  <Th>{t("timekeeping.periods.reports.columns.id")}</Th>
                  <Th>{t("timekeeping.periods.reports.columns.employee")}</Th>
                  <Th>{t("timekeeping.periods.reports.columns.status")}</Th>
                  <Th>{t("timekeeping.periods.reports.columns.version")}</Th>
                  <Th>{t("timekeeping.periods.reports.columns.submitted")}</Th>
                  <Th></Th>
                </tr>
              </thead>
              <tbody>
                {reports.length === 0 && (
                  <EmptyRow colSpan={6} message={t("timekeeping.periods.reports.empty")} />
                )}
                {reports.map((r) => (
                  <tr key={r.id}>
                    <Td>#{r.id}</Td>
                    <Td>#{r.employee_id}</Td>
                    <Td>
                      <Badge status={r.status}>{r.status}</Badge>
                    </Td>
                    <Td>v{r.version}</Td>
                    <Td>{formatDate(r.submitted_at)}</Td>
                    <Td className="text-right">
                      <Link
                        to={`/reports/${r.id}`}
                        className="text-sm font-medium text-foreground hover:underline"
                      >
                        {t("timekeeping.periods.reports.view")}
                      </Link>
                    </Td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </CardBody>
      </Card>

      <CreateReportModal open={open} onClose={() => setOpen(false)} periodId={periodId!} />
    </div>
  );
}

function CreateReportModal({
  open,
  onClose,
  periodId,
}: {
  open: boolean;
  onClose: () => void;
  periodId: number;
}) {
  const tenantId = useCurrentTenantId();
  const { data: employees = [] } = useEmployees(tenantId);
  const create = useCreateTimeReport(tenantId, periodId);
  const { t } = useTranslation();
  const [employeeId, setEmployeeId] = useState("");

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    create.mutate({ employee_id: Number(employeeId) }, { onSuccess: () => onClose() });
  }

  return (
    <Modal open={open} onClose={onClose} title={t("timekeeping.periods.reports.createForEmployee")}>
      <form onSubmit={onSubmit} className="space-y-3">
        <Select
          label={t("timekeeping.periods.reports.employee")}
          value={employeeId}
          onChange={(e) => setEmployeeId(e.target.value)}
          required
        >
          <option value="">{t("timekeeping.periods.reports.selectPlaceholder")}</option>
          {employees
            .filter((e) => e.is_active)
            .map((e) => (
              <option key={e.id} value={e.id}>
                {e.full_name}
              </option>
            ))}
        </Select>
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            {t("common.cancel")}
          </Button>
          <Button type="submit" disabled={create.isPending}>
            {create.isPending ? t("common.creating") : t("common.create")}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
