import { useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Textarea } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyRow, Table, Td, Th } from "@/components/ui/Table";
import { useCurrentTenantId } from "@/features/tenants/hooks";
import { formatDateTime } from "@/lib/format";
import { useApprovals, useApproveApproval, useRejectApproval } from "../hooks";

export default function ApprovalsPage() {
  const tenantId = useCurrentTenantId();
  const { data, isLoading } = useApprovals(tenantId);
  const [rejecting, setRejecting] = useState<number | null>(null);

  return (
    <Card>
      <CardHeader title="Aprobaciones" description="Reportes pendientes de tu revisión" />
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
                <Th>Reporte</Th>
                <Th>Estado</Th>
                <Th>Revisor</Th>
                <Th>Revisado</Th>
                <Th>Creado</Th>
                <Th></Th>
              </tr>
            </thead>
            <tbody>
              {(!data || data.length === 0) && <EmptyRow colSpan={7} message="Sin aprobaciones." />}
              {data?.map((a) => (
                <ApprovalRow key={a.id} approval={a} onReject={() => setRejecting(a.id)} />
              ))}
            </tbody>
          </Table>
        )}
      </CardBody>

      <RejectModal approvalId={rejecting} onClose={() => setRejecting(null)} />
    </Card>
  );
}

function ApprovalRow({
  approval,
  onReject,
}: {
  approval: import("@/client").ApprovalOut;
  onReject: () => void;
}) {
  const tenantId = useCurrentTenantId();
  const approve = useApproveApproval(tenantId);
  const isPending = approval.status === "pending";

  return (
    <tr>
      <Td>#{approval.id}</Td>
      <Td>#{approval.report_id}</Td>
      <Td>
        <Badge status={approval.status}>{approval.status}</Badge>
      </Td>
      <Td>{approval.reviewer_id ? `#${approval.reviewer_id}` : "—"}</Td>
      <Td>{formatDateTime(approval.reviewed_at)}</Td>
      <Td>{formatDateTime(approval.created_at)}</Td>
      <Td className="text-right">
        {isPending && (
          <div className="flex justify-end gap-2">
            <Button onClick={() => approve.mutate(approval.id)} disabled={approve.isPending}>
              Aprobar
            </Button>
            <Button variant="danger" onClick={onReject}>
              Rechazar
            </Button>
          </div>
        )}
      </Td>
    </tr>
  );
}

function RejectModal({ approvalId, onClose }: { approvalId: number | null; onClose: () => void }) {
  const tenantId = useCurrentTenantId();
  const reject = useRejectApproval(tenantId);
  const [reason, setReason] = useState("");

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (approvalId == null) return;
    reject.mutate(
      { id: approvalId, body: { reason } },
      {
        onSuccess: () => {
          setReason("");
          onClose();
        },
      },
    );
  }

  return (
    <Modal open={approvalId != null} onClose={onClose} title="Rechazar aprobación">
      <form onSubmit={onSubmit} className="space-y-3">
        <Textarea
          label="Motivo (opcional)"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          rows={3}
        />
        <div className="flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" variant="danger" disabled={reject.isPending}>
            {reject.isPending ? "Rechazando…" : "Rechazar"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
