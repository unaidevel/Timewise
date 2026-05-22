import { Check, CheckSquare, Inbox, X } from "lucide-react";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";
import type { ApprovalOut } from "@/client";
import { EmptyState } from "@/components/EmptyState";
import { Badge } from "@/components/shadcn/badge";
import { Button } from "@/components/shadcn/button";
import { Card, CardContent } from "@/components/shadcn/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/shadcn/dialog";
import { Skeleton } from "@/components/shadcn/skeleton";
import { Tabs, TabsList, TabsTrigger } from "@/components/shadcn/tabs";
import { useCurrentTenantId, useIsTenantAdmin } from "@/features/tenants/hooks";
import { formatDateTime } from "@/lib/format";
import { cn } from "@/lib/utils";
import { type Scope, useApprovals, useApproveApproval, useRejectApproval } from "../hooks";

type Tab = "pending" | "approved" | "rejected";

const statusStyle: Record<string, string> = {
  pending: "bg-warning/20 text-warning-foreground border-warning/30",
  approved: "bg-success/15 text-success border-success/20",
  rejected: "bg-destructive/15 text-destructive border-destructive/20",
};

export default function ApprovalsPage() {
  const tenantId = useCurrentTenantId();
  const isAdmin = useIsTenantAdmin(tenantId);
  const [scope, setScope] = useState<Scope>("mine");
  const effectiveScope: Scope = isAdmin ? scope : "mine";
  const approvals = useApprovals(tenantId, effectiveScope);
  const { t } = useTranslation();
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
      <header className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">
            {t("timekeeping.approvals.title")}
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            {t("timekeeping.approvals.subtitle")}
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

      {isEmpty ? (
        <EmptyState
          icon={CheckSquare}
          title={t("timekeeping.approvals.empty.title")}
          description={t("timekeeping.approvals.empty.description")}
        />
      ) : (
        <>
          <Tabs value={tab} onValueChange={(v) => setTab(v as Tab)}>
            <TabsList>
              <TabsTrigger value="pending">
                {t("timekeeping.approvals.tabs.pending")}
                <Badge variant="secondary" className="ml-2 px-1.5">
                  {counts.pending}
                </Badge>
              </TabsTrigger>
              <TabsTrigger value="approved">
                {t("timekeeping.approvals.tabs.approved")}
                <Badge variant="secondary" className="ml-2 px-1.5">
                  {counts.approved}
                </Badge>
              </TabsTrigger>
              <TabsTrigger value="rejected">
                {t("timekeeping.approvals.tabs.rejected")}
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
                <p className="text-sm text-muted-foreground">
                  {t("timekeeping.approvals.nothing")}
                </p>
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

      <RejectDialog approval={rejecting} onClose={() => setRejecting(null)} />
    </div>
  );
}

function ApprovalCard({ approval, onReject }: { approval: ApprovalOut; onReject: () => void }) {
  const tenantId = useCurrentTenantId();
  const approve = useApproveApproval(tenantId);
  const { t } = useTranslation();
  const isPending = approval.status === "pending";

  return (
    <Card className="hover:shadow-[var(--shadow-elegant)] transition">
      <CardContent className="p-4 flex items-center gap-4 flex-wrap">
        <div className="size-10 rounded-full bg-primary/10 text-primary grid place-items-center font-semibold text-xs">
          #{approval.report_id}
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-medium truncate">
            {t("timekeeping.approvals.reportLabel", { id: approval.report_id })}
          </div>
          <div className="text-xs text-muted-foreground mt-0.5">
            {t("timekeeping.approvals.approvalLabel", { id: approval.id })}
            {approval.reviewer_id != null && (
              <> · {t("timekeeping.approvals.reviewer", { id: approval.reviewer_id })}</>
            )}
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
              aria-label={t("timekeeping.approvals.rejectAria")}
              onClick={onReject}
            >
              <X className="size-4" />
            </Button>
            <Button
              size="icon"
              className="size-8"
              aria-label={t("timekeeping.approvals.approveAria")}
              disabled={approve.isPending}
              onClick={() =>
                approve.mutate(approval.id, {
                  onSuccess: () => toast.success(t("timekeeping.approvals.approvedToast")),
                  onError: () => toast.error(t("timekeeping.approvals.approveErrorToast")),
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

function RejectDialog({
  approval,
  onClose,
}: {
  approval: ApprovalOut | null;
  onClose: () => void;
}) {
  const tenantId = useCurrentTenantId();
  const reject = useRejectApproval(tenantId);
  const { t } = useTranslation();
  const [reason, setReason] = useState("");

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!approval) return;
    reject.mutate(
      { id: approval.id, body: { reason } },
      {
        onSuccess: () => {
          toast.success(t("timekeeping.approvals.rejectedToast"));
          setReason("");
          onClose();
        },
        onError: () => toast.error(t("timekeeping.approvals.rejectErrorToast")),
      },
    );
  }

  return (
    <Dialog open={!!approval} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{t("timekeeping.approvals.rejectModal.title")}</DialogTitle>
          <DialogDescription>
            {approval && (
              <>
                {t("timekeeping.approvals.reportLabel", { id: approval.report_id })} ·{" "}
                {t("timekeeping.approvals.approvalLabel", { id: approval.id })}
              </>
            )}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={onSubmit} className="mt-2 space-y-4">
          <div className="space-y-1.5 text-sm">
            <label
              htmlFor="reject-reason"
              className="block text-xs font-medium text-muted-foreground"
            >
              {t("timekeeping.approvals.rejectModal.reasonLabel")}
            </label>
            <textarea
              id="reject-reason"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={4}
              className="w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
              placeholder={t("timekeeping.approvals.rejectModal.reasonPlaceholder")}
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={onClose}>
              {t("common.cancel")}
            </Button>
            <Button type="submit" variant="destructive" disabled={reject.isPending}>
              {reject.isPending
                ? t("timekeeping.approvals.rejectModal.rejecting")
                : t("timekeeping.approvals.rejectAria")}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
