import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Input, Textarea } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyRow, Table, Td, Th } from "@/components/ui/Table";
import { useCurrentTenantId } from "@/features/tenants/hooks";
import { formatCurrency, formatDate, formatDateTime, formatHours } from "@/lib/format";
import {
  useApproveReport,
  useCalculateReportCost,
  useCreateTimeEntry,
  useDeleteTimeEntry,
  useRejectReport,
  useReopenReport,
  useReportCostBreakdown,
  useReportHistory,
  useSubmitReport,
  useTimeEntries,
  useTimeReport,
} from "../hooks";

export default function TimeReportDetailPage() {
  const { id } = useParams<{ id: string }>();
  const tenantId = useCurrentTenantId();
  const reportId = id ? Number(id) : null;
  const { data: report, isLoading } = useTimeReport(tenantId, reportId);
  const submit = useSubmitReport(tenantId, reportId);
  const approve = useApproveReport(tenantId, reportId);
  const reopen = useReopenReport(tenantId, reportId);
  const { t } = useTranslation();
  const [rejecting, setRejecting] = useState(false);

  if (isLoading)
    return (
      <div className="flex justify-center p-8">
        <Spinner />
      </div>
    );
  if (!report) return <p className="text-slate-600">{t("timekeeping.reports.notFound")}</p>;

  const isDraft = report.status === "draft";
  const isPending = report.status === "pending" || report.status === "submitted";
  const isRejected = report.status === "rejected";

  return (
    <div className="space-y-4">
      <Link to="/reports" className="text-sm text-slate-600 hover:underline">
        {t("timekeeping.reports.backToList")}
      </Link>

      <Card>
        <CardHeader
          title={t("timekeeping.reports.header", { id: report.id })}
          description={t("timekeeping.reports.subheader", {
            employee: report.employee_id,
            period: report.period_id,
          })}
          action={<Badge status={report.status}>{report.status}</Badge>}
        />
        <CardBody>
          <div className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
            <Field
              label={t("timekeeping.reports.fields.submitted")}
              value={formatDateTime(report.submitted_at)}
            />
            <Field
              label={t("timekeeping.reports.fields.approved")}
              value={formatDateTime(report.approved_at)}
            />
            <Field
              label={t("timekeeping.reports.fields.rejected")}
              value={formatDateTime(report.rejected_at)}
            />
            <Field
              label={t("timekeeping.reports.fields.locked")}
              value={formatDateTime(report.locked_at)}
            />
          </div>
          {report.rejection_reason && (
            <p className="mt-3 rounded-md bg-red-50 p-3 text-sm text-red-700">
              <strong>{t("timekeeping.reports.rejectionReason")}</strong> {report.rejection_reason}
            </p>
          )}
          <div className="mt-4 flex flex-wrap gap-2">
            {isDraft && (
              <Button onClick={() => submit.mutate()} disabled={submit.isPending}>
                {t("timekeeping.reports.submit")}
              </Button>
            )}
            {isPending && (
              <>
                <Button onClick={() => approve.mutate()} disabled={approve.isPending}>
                  {t("timekeeping.reports.approve")}
                </Button>
                <Button variant="danger" onClick={() => setRejecting(true)}>
                  {t("timekeeping.reports.reject")}
                </Button>
              </>
            )}
            {isRejected && (
              <Button onClick={() => reopen.mutate()} disabled={reopen.isPending}>
                {t("timekeeping.reports.reopen")}
              </Button>
            )}
          </div>
        </CardBody>
      </Card>

      <EntriesCard reportId={reportId!} canEdit={isDraft} />
      <CostBreakdownCard reportId={reportId!} />
      <HistoryCard reportId={reportId!} />

      <RejectModal open={rejecting} onClose={() => setRejecting(false)} reportId={reportId!} />
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wider text-slate-500">{label}</dt>
      <dd className="mt-1 font-medium text-slate-900">{value}</dd>
    </div>
  );
}

function EntriesCard({ reportId, canEdit }: { reportId: number; canEdit: boolean }) {
  const tenantId = useCurrentTenantId();
  const { data: entries = [], isLoading } = useTimeEntries(tenantId, reportId);
  const remove = useDeleteTimeEntry(tenantId, reportId);
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);

  const totalHours = entries.reduce((sum, e) => sum + parseFloat(e.hours), 0);

  return (
    <Card>
      <CardHeader
        title={t("timekeeping.reports.entries.title")}
        description={t("timekeeping.reports.entries.totalLabel", { hours: totalHours.toFixed(2) })}
        action={
          canEdit && (
            <Button onClick={() => setOpen(true)}>{t("timekeeping.reports.entries.add")}</Button>
          )
        }
      />
      <CardBody className="p-0">
        {isLoading ? (
          <div className="flex justify-center p-8">
            <Spinner />
          </div>
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>{t("timekeeping.reports.entries.columns.date")}</Th>
                <Th>{t("timekeeping.reports.entries.columns.hours")}</Th>
                <Th>{t("timekeeping.reports.entries.columns.start")}</Th>
                <Th>{t("timekeeping.reports.entries.columns.end")}</Th>
                <Th>{t("timekeeping.reports.entries.columns.description")}</Th>
                <Th></Th>
              </tr>
            </thead>
            <tbody>
              {entries.length === 0 && (
                <EmptyRow colSpan={6} message={t("timekeeping.reports.entries.empty")} />
              )}
              {entries.map((e) => (
                <tr key={e.id}>
                  <Td>{formatDate(e.date)}</Td>
                  <Td>{formatHours(e.hours)}</Td>
                  <Td>{e.start_time ?? "—"}</Td>
                  <Td>{e.end_time ?? "—"}</Td>
                  <Td className="text-slate-600">{e.description || "—"}</Td>
                  <Td className="text-right">
                    {canEdit && (
                      <Button
                        variant="ghost"
                        onClick={() => remove.mutate(e.id)}
                        disabled={remove.isPending}
                      >
                        {t("timekeeping.reports.entries.delete")}
                      </Button>
                    )}
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </CardBody>

      <CreateEntryModal open={open} onClose={() => setOpen(false)} reportId={reportId} />
    </Card>
  );
}

function CreateEntryModal({
  open,
  onClose,
  reportId,
}: {
  open: boolean;
  onClose: () => void;
  reportId: number;
}) {
  const tenantId = useCurrentTenantId();
  const create = useCreateTimeEntry(tenantId, reportId);
  const { t } = useTranslation();
  const [form, setForm] = useState({
    date: new Date().toISOString().slice(0, 10),
    hours: "8",
    start_time: "",
    end_time: "",
    description: "",
  });

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    create.mutate(
      {
        date: form.date,
        hours: form.hours,
        start_time: form.start_time || null,
        end_time: form.end_time || null,
        description: form.description,
      },
      { onSuccess: () => onClose() },
    );
  }

  return (
    <Modal open={open} onClose={onClose} title={t("timekeeping.reports.entries.createTitle")}>
      <form onSubmit={onSubmit} className="grid grid-cols-2 gap-3">
        <Input
          label={t("timekeeping.reports.entries.date")}
          type="date"
          value={form.date}
          onChange={(e) => setForm({ ...form, date: e.target.value })}
          required
        />
        <Input
          label={t("timekeeping.reports.entries.hours")}
          type="number"
          step="0.25"
          value={form.hours}
          onChange={(e) => setForm({ ...form, hours: e.target.value })}
          required
        />
        <Input
          label={t("timekeeping.reports.entries.start")}
          type="time"
          value={form.start_time}
          onChange={(e) => setForm({ ...form, start_time: e.target.value })}
        />
        <Input
          label={t("timekeeping.reports.entries.end")}
          type="time"
          value={form.end_time}
          onChange={(e) => setForm({ ...form, end_time: e.target.value })}
        />
        <div className="col-span-full">
          <Textarea
            label={t("timekeeping.reports.entries.description")}
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            rows={2}
          />
        </div>
        <div className="col-span-full flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            {t("common.cancel")}
          </Button>
          <Button type="submit" disabled={create.isPending}>
            {create.isPending
              ? t("timekeeping.reports.entries.adding")
              : t("timekeeping.reports.entries.add2")}
          </Button>
        </div>
      </form>
    </Modal>
  );
}

function CostBreakdownCard({ reportId }: { reportId: number }) {
  const tenantId = useCurrentTenantId();
  const { data: breakdowns = [], isLoading } = useReportCostBreakdown(tenantId, reportId);
  const calculate = useCalculateReportCost(tenantId, reportId);
  const { t } = useTranslation();

  const totalCost = breakdowns.reduce((sum, b) => sum + parseFloat(b.total_cost), 0);
  const totalBaseHours = breakdowns.reduce((sum, b) => sum + parseFloat(b.base_hours), 0);
  const totalOvertimeHours = breakdowns.reduce((sum, b) => sum + parseFloat(b.overtime_hours), 0);

  return (
    <Card>
      <CardHeader
        title={t("timekeeping.reports.cost.title")}
        description={
          breakdowns.length > 0
            ? t("timekeeping.reports.cost.summary", {
                base: formatHours(String(totalBaseHours)),
                overtime: formatHours(String(totalOvertimeHours)),
                total: formatCurrency(String(totalCost)),
              })
            : t("timekeeping.reports.cost.empty")
        }
        action={
          <Button
            variant="secondary"
            onClick={() => calculate.mutate()}
            disabled={calculate.isPending}
          >
            {calculate.isPending
              ? t("timekeeping.reports.cost.calculating")
              : t("timekeeping.reports.cost.calculate")}
          </Button>
        }
      />
      {isLoading ? (
        <CardBody className="flex justify-center p-8">
          <Spinner />
        </CardBody>
      ) : breakdowns.length > 0 ? (
        <CardBody className="p-0">
          <Table>
            <thead>
              <tr>
                <Th>{t("timekeeping.reports.cost.columns.rule")}</Th>
                <Th>{t("timekeeping.reports.cost.columns.multiplier")}</Th>
                <Th>{t("timekeeping.reports.cost.columns.baseHours")}</Th>
                <Th>{t("timekeeping.reports.cost.columns.overtimeHours")}</Th>
                <Th>{t("timekeeping.reports.cost.columns.baseCost")}</Th>
                <Th>{t("timekeeping.reports.cost.columns.totalCost")}</Th>
              </tr>
            </thead>
            <tbody>
              {breakdowns.map((b) => (
                <tr key={b.id}>
                  <Td className="font-medium">{b.applied_rule_name}</Td>
                  <Td>×{b.multiplier}</Td>
                  <Td>{formatHours(b.base_hours)}</Td>
                  <Td>{formatHours(b.overtime_hours)}</Td>
                  <Td>{formatCurrency(b.base_cost)}</Td>
                  <Td className="font-semibold">{formatCurrency(b.total_cost)}</Td>
                </tr>
              ))}
              <tr className="border-t border-slate-200 bg-slate-50">
                <Td colSpan={4} className="font-semibold text-slate-700">
                  {t("timekeeping.reports.cost.total")}
                </Td>
                <Td></Td>
                <Td className="font-bold text-slate-900">{formatCurrency(String(totalCost))}</Td>
              </tr>
            </tbody>
          </Table>
        </CardBody>
      ) : null}
    </Card>
  );
}

function HistoryCard({ reportId }: { reportId: number }) {
  const tenantId = useCurrentTenantId();
  const { data = [] } = useReportHistory(tenantId, reportId);
  const { t } = useTranslation();

  if (data.length === 0) return null;

  return (
    <Card>
      <CardHeader title={t("timekeeping.reports.history.title")} />
      <CardBody className="p-0">
        <Table>
          <thead>
            <tr>
              <Th>{t("timekeeping.reports.history.columns.when")}</Th>
              <Th>{t("timekeeping.reports.history.columns.from")}</Th>
              <Th>{t("timekeeping.reports.history.columns.to")}</Th>
              <Th>{t("timekeeping.reports.history.columns.by")}</Th>
            </tr>
          </thead>
          <tbody>
            {data.map((h) => (
              <tr key={h.id}>
                <Td>{formatDateTime(h.changed_at)}</Td>
                <Td>
                  <Badge status={h.from_status ?? undefined}>{h.from_status ?? "—"}</Badge>
                </Td>
                <Td>
                  <Badge status={h.to_status}>{h.to_status}</Badge>
                </Td>
                <Td>#{h.changed_by_id}</Td>
              </tr>
            ))}
          </tbody>
        </Table>
      </CardBody>
    </Card>
  );
}

function RejectModal({
  open,
  onClose,
  reportId,
}: {
  open: boolean;
  onClose: () => void;
  reportId: number;
}) {
  const tenantId = useCurrentTenantId();
  const reject = useRejectReport(tenantId, reportId);
  const { t } = useTranslation();
  const [reason, setReason] = useState("");

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    reject.mutate({ reason }, { onSuccess: () => onClose() });
  }

  return (
    <Modal open={open} onClose={onClose} title={t("timekeeping.reports.rejectModal.title")}>
      <form onSubmit={onSubmit} className="space-y-3">
        <Textarea
          label={t("timekeeping.reports.rejectModal.reason")}
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          required
          rows={3}
        />
        <div className="flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            {t("common.cancel")}
          </Button>
          <Button type="submit" variant="danger" disabled={reject.isPending}>
            {reject.isPending
              ? t("timekeeping.reports.rejectModal.rejecting")
              : t("timekeeping.reports.reject")}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
