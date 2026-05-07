import { Check, CheckSquare, Inbox, X } from "lucide-react";
import { useMemo, useState } from "react";
import { toast } from "sonner";
import type { ApprovalOut } from "@/client";
import { EmptyState } from "@/components/EmptyState";
import { Badge } from "@/components/shadcn/badge";
import { Button } from "@/components/shadcn/button";
import { Card, CardContent } from "@/components/shadcn/card";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/shadcn/sheet";
import { Skeleton } from "@/components/shadcn/skeleton";
import { Tabs, TabsList, TabsTrigger } from "@/components/shadcn/tabs";
import { useCurrentTenantId } from "@/features/tenants/hooks";
import { formatDateTime } from "@/lib/format";
import { cn } from "@/lib/utils";
import { useApprovals, useApproveApproval, useRejectApproval } from "../hooks";

type Tab = "pending" | "approved" | "rejected";

const statusStyle: Record<string, string> = {
  pending: "bg-warning/20 text-warning-foreground border-warning/30",
  approved: "bg-success/15 text-success border-success/20",
  rejected: "bg-destructive/15 text-destructive border-destructive/20",
};

export default function ApprovalsPage() {
  const tenantId = useCurrentTenantId();
  const approvals = useApprovals(tenantId);
  const [tab, setTab] = useState<Tab>("pending");
  const [rejecting, setRejecting] = useState<ApprovalOut | null>(null);

  const counts = useMemo(() => {
    const list = approvals.data ?? [];
    return {
      pending: list.filter((a) => a.status === "pending").length,
      approved: list.filter((a) => a.status === "approved").length,
      rejected: list.filter((a) => a.status === "rejected").length,
    };
  }, [approvals.data]);

  const filtered = useMemo(
    () => (approvals.data ?? []).filter((a) => a.status === tab),
    [approvals.data, tab],
  );

  const isEmpty = approvals.isSuccess && (approvals.data?.length ?? 0) === 0;

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight">Aprobaciones</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Revisa y actúa sobre los reportes enviados por tu equipo.
        </p>
      </header>

      {isEmpty ? (
        <EmptyState
          icon={CheckSquare}
          title="Bandeja vacía"
          description="Cuando lleguen reportes para revisar, los verás aquí agrupados por estado."
        />
      ) : (
        <>
          <Tabs value={tab} onValueChange={(v) => setTab(v as Tab)}>
            <TabsList>
              <TabsTrigger value="pending">
                Pendientes
                <Badge variant="secondary" className="ml-2 px-1.5">
                  {counts.pending}
                </Badge>
              </TabsTrigger>
              <TabsTrigger value="approved">
                Aprobadas
                <Badge variant="secondary" className="ml-2 px-1.5">
                  {counts.approved}
                </Badge>
              </TabsTrigger>
              <TabsTrigger value="rejected">
                Rechazadas
                <Badge variant="secondary" className="ml-2 px-1.5">
                  {counts.rejected}
                </Badge>
              </TabsTrigger>
            </TabsList>
          </Tabs>

          {approvals.isLoading ? (
            <div className="space-y-2">
              {["a", "b", "c", "d"].map((k) => (
                <Card key={k}>
                  <CardContent className="p-4 flex items-center gap-4">
                    <Skeleton className="size-10 rounded-full" />
                    <div className="flex-1 space-y-2">
                      <Skeleton className="h-4 w-48" />
                      <Skeleton className="h-3 w-32" />
                    </div>
                    <Skeleton className="h-6 w-20" />
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : filtered.length === 0 ? (
            <Card>
              <CardContent className="p-12 text-center">
                <div className="mx-auto size-12 rounded-full bg-muted grid place-items-center mb-3">
                  <Inbox className="size-5 text-muted-foreground" />
                </div>
                <p className="text-sm text-muted-foreground">Nada por aquí ahora mismo.</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-2">
              {filtered.map((a) => (
                <ApprovalCard key={a.id} approval={a} onReject={() => setRejecting(a)} />
              ))}
            </div>
          )}
        </>
      )}

      <RejectSheet approval={rejecting} onClose={() => setRejecting(null)} />
    </div>
  );
}

function ApprovalCard({ approval, onReject }: { approval: ApprovalOut; onReject: () => void }) {
  const tenantId = useCurrentTenantId();
  const approve = useApproveApproval(tenantId);
  const isPending = approval.status === "pending";

  return (
    <Card className="hover:shadow-[var(--shadow-elegant)] transition">
      <CardContent className="p-4 flex items-center gap-4 flex-wrap">
        <div className="size-10 rounded-full bg-primary/10 text-primary grid place-items-center font-semibold text-xs">
          #{approval.report_id}
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-medium truncate">Reporte #{approval.report_id}</div>
          <div className="text-xs text-muted-foreground mt-0.5">
            Aprobación #{approval.id}
            {approval.reviewer_id != null && <> · Revisor #{approval.reviewer_id}</>}
            {approval.reviewed_at && <> · {formatDateTime(approval.reviewed_at)}</>}
          </div>
        </div>
        <Badge variant="outline" className={cn("capitalize", statusStyle[approval.status])}>
          {approval.status}
        </Badge>
        {isPending && (
          <div className="flex gap-1">
            <Button
              size="icon"
              variant="outline"
              className="size-8"
              aria-label="Rechazar"
              onClick={onReject}
            >
              <X className="size-4" />
            </Button>
            <Button
              size="icon"
              className="size-8"
              aria-label="Aprobar"
              disabled={approve.isPending}
              onClick={() =>
                approve.mutate(approval.id, {
                  onSuccess: () => toast.success("Reporte aprobado"),
                  onError: () => toast.error("No se pudo aprobar"),
                })
              }
            >
              <Check className="size-4" />
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function RejectSheet({ approval, onClose }: { approval: ApprovalOut | null; onClose: () => void }) {
  const tenantId = useCurrentTenantId();
  const reject = useRejectApproval(tenantId);
  const [reason, setReason] = useState("");

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!approval) return;
    reject.mutate(
      { id: approval.id, body: { reason } },
      {
        onSuccess: () => {
          toast.success("Reporte rechazado");
          setReason("");
          onClose();
        },
        onError: () => toast.error("No se pudo rechazar"),
      },
    );
  }

  return (
    <Sheet open={!!approval} onOpenChange={(o) => !o && onClose()}>
      <SheetContent className="sm:max-w-md">
        <SheetHeader>
          <SheetTitle>Rechazar reporte</SheetTitle>
          <SheetDescription>
            {approval && (
              <>
                Reporte #{approval.report_id} · Aprobación #{approval.id}
              </>
            )}
          </SheetDescription>
        </SheetHeader>
        <form onSubmit={onSubmit} className="mt-6 space-y-4">
          <div className="space-y-1.5 text-sm">
            <label
              htmlFor="reject-reason"
              className="block text-xs font-medium text-muted-foreground"
            >
              Motivo (opcional)
            </label>
            <textarea
              id="reject-reason"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={4}
              className="w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
              placeholder="Cuéntale al empleado qué cambiar antes de reenviar."
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancelar
            </Button>
            <Button type="submit" variant="destructive" disabled={reject.isPending}>
              {reject.isPending ? "Rechazando…" : "Rechazar"}
            </Button>
          </div>
        </form>
      </SheetContent>
    </Sheet>
  );
}
