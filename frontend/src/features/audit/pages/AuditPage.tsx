import { motion } from "framer-motion";
import { ChevronDown, ChevronRight, ExternalLink, Pencil, ScrollText, X } from "lucide-react";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useSearchParams } from "react-router";
import { toast } from "sonner";
import type { AuditEventOut, EmployeeOut, TenantMemberResponse } from "@/client";
import { EmptyState } from "@/components/EmptyState";
import { Badge } from "@/components/shadcn/badge";
import { Button } from "@/components/shadcn/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/shadcn/card";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/shadcn/dialog";
import { Input } from "@/components/shadcn/input";
import { Label } from "@/components/shadcn/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/shadcn/select";
import { Textarea } from "@/components/shadcn/textarea";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/shadcn/tooltip";
import { useAuthStore } from "@/features/auth/store";
import { useEmployees } from "@/features/employees/hooks";
import { useCurrentTenantId, useMembers } from "@/features/tenants/hooks";
import { cn } from "@/lib/utils";
import { type AuditFilters, useAuditEvents, useUpdateAuditEventNotes } from "../hooks";

type Outcome = "success" | "failure";

function readOutcome(value: string | null): Outcome | undefined {
  return value === "success" || value === "failure" ? value : undefined;
}

const RESOURCE_ROUTES: Record<string, (id: number) => string> = {
  TimeReport: (id) => `/reports/${id}`,
  Period: (id) => `/periods/${id}`,
  Employee: (id) => `/employees/${id}`,
  OvertimeRule: (id) => `/costing-rules/${id}`,
};

function resourceLink(resourceType: string, resourceId: number | null): string | null {
  if (resourceId == null) return null;
  const build = RESOURCE_ROUTES[resourceType];
  return build ? build(resourceId) : null;
}

export default function AuditPage() {
  const tenantId = useCurrentTenantId();
  const user = useAuthStore((s) => s.user);
  const members = useMembers(tenantId);
  const employees = useEmployees(tenantId);
  const { t } = useTranslation();
  const [params, setParams] = useSearchParams();

  const actionQ = params.get("action") ?? "";
  const resourceQ = params.get("resource_type") ?? "";
  const outcomeQ = readOutcome(params.get("outcome"));
  const actorQ = params.get("actor_id");
  const actorIdNum = actorQ ? Number(actorQ) : null;

  const filters: AuditFilters = useMemo(
    () => ({
      action: actionQ || null,
      resource_type: resourceQ || null,
      outcome: outcomeQ ?? null,
      actor_id: actorIdNum,
    }),
    [actionQ, resourceQ, outcomeQ, actorIdNum],
  );

  const eventsQ = useAuditEvents(tenantId, filters);

  const currentMember = useMemo(
    () => members.data?.find((m) => m.user_id === user?.id),
    [members.data, user?.id],
  );
  const isAdmin = currentMember?.role === "owner" || currentMember?.role === "admin";

  const employeesByUserId = useMemo(() => {
    const m = new Map<number, EmployeeOut>();
    for (const e of employees.data ?? []) if (e.user_id != null) m.set(e.user_id, e);
    return m;
  }, [employees.data]);

  const membersByUserId = useMemo(() => {
    const m = new Map<number, TenantMemberResponse>();
    for (const memb of members.data ?? []) m.set(memb.user_id, memb);
    return m;
  }, [members.data]);

  function patchParams(patch: Record<string, string | null>) {
    const next = new URLSearchParams(params);
    for (const [k, v] of Object.entries(patch)) {
      if (v == null || v === "") next.delete(k);
      else next.set(k, v);
    }
    setParams(next, { replace: true });
  }

  const hasFilters = Boolean(actionQ || resourceQ || outcomeQ || actorQ);
  const events = eventsQ.data ?? [];

  if (tenantId == null) {
    return (
      <EmptyState
        title={t("audit.noWorkspace.title")}
        description={t("audit.noWorkspace.description")}
      />
    );
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight flex items-center gap-2">
          <ScrollText className="size-7 text-primary" />
          {t("audit.title")}
        </h1>
        <p className="text-sm text-muted-foreground mt-1">{t("audit.subtitle")}</p>
      </header>

      <Card className="sticky top-16 z-10 backdrop-blur-md bg-background/85">
        <CardContent className="py-4 grid gap-3 md:grid-cols-[1fr_1fr_180px_220px_auto]">
          <div className="space-y-1.5">
            <Label className="text-xs">{t("audit.filters.action")}</Label>
            <Input
              placeholder={t("audit.filters.actionPlaceholder")}
              value={actionQ}
              onChange={(e) => patchParams({ action: e.target.value })}
            />
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs">{t("audit.filters.resource")}</Label>
            <Input
              placeholder={t("audit.filters.resourcePlaceholder")}
              value={resourceQ}
              onChange={(e) => patchParams({ resource_type: e.target.value })}
            />
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs">{t("audit.filters.outcome")}</Label>
            <Select
              value={outcomeQ ?? "any"}
              onValueChange={(v) => patchParams({ outcome: v === "any" ? null : v })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="any">{t("audit.filters.any")}</SelectItem>
                <SelectItem value="success">{t("audit.filters.success")}</SelectItem>
                <SelectItem value="failure">{t("audit.filters.failure")}</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs">{t("audit.filters.actor")}</Label>
            <Select
              value={actorQ ?? "any"}
              onValueChange={(v) => patchParams({ actor_id: v === "any" ? null : v })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="any">{t("audit.filters.any")}</SelectItem>
                {(employees.data ?? []).map((e) => (
                  <SelectItem key={e.id} value={String(e.id)}>
                    {e.full_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-end">
            {hasFilters && (
              <Button variant="ghost" size="sm" onClick={() => setParams({}, { replace: true })}>
                <X className="size-4 mr-1" />
                {t("audit.filters.clear")}
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3 flex-row items-center justify-between">
          <CardTitle className="text-base font-medium">
            {eventsQ.isPending
              ? t("audit.table.loading")
              : t("audit.table.eventCount", { count: events.length })}
          </CardTitle>
        </CardHeader>
        <CardContent className="px-0">
          <div className="border-t">
            <div className="grid grid-cols-[40px_180px_1fr_1fr_1fr_110px_60px] gap-3 px-4 py-2.5 text-xs font-medium text-muted-foreground bg-muted/30 border-b">
              <span />
              <span>{t("audit.table.columns.time")}</span>
              <span>{t("audit.table.columns.actor")}</span>
              <span>{t("audit.table.columns.action")}</span>
              <span>{t("audit.table.columns.resource")}</span>
              <span>{t("audit.table.columns.outcome")}</span>
              <span />
            </div>
            <TooltipProvider delayDuration={200}>
              {events.map((ev) => (
                <Row
                  key={ev.id}
                  event={ev}
                  actor={employeesByUserId.get(ev.actor_id)}
                  member={membersByUserId.get(ev.actor_id)}
                  isAdmin={isAdmin}
                  tenantId={tenantId}
                />
              ))}
            </TooltipProvider>
            {!eventsQ.isPending && events.length === 0 && (
              <div className="px-4 py-12 text-center text-sm text-muted-foreground">
                {t("audit.table.empty")}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function Row({
  event,
  actor,
  member,
  isAdmin,
  tenantId,
}: {
  event: AuditEventOut;
  actor: EmployeeOut | undefined;
  member: TenantMemberResponse | undefined;
  isAdmin: boolean;
  tenantId: number;
}) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState(false);
  const actorLabel =
    actor?.full_name ?? member?.full_name ?? t("audit.table.userFallback", { id: event.actor_id });
  const actorEmail = actor?.email ?? member?.email;

  return (
    <>
      <motion.div
        layout
        className={cn(
          "grid grid-cols-[40px_180px_1fr_1fr_1fr_110px_60px] gap-3 px-4 py-3 text-sm border-b items-center hover:bg-muted/30 transition-colors cursor-pointer",
          open && "bg-muted/20",
        )}
        onClick={() => setOpen((o) => !o)}
      >
        <span className="text-muted-foreground">
          {open ? <ChevronDown className="size-4" /> : <ChevronRight className="size-4" />}
        </span>
        <Tooltip>
          <TooltipTrigger asChild>
            <span className="text-muted-foreground tabular-nums">
              {relativeTime(event.occurred_at, t)}
            </span>
          </TooltipTrigger>
          <TooltipContent>{new Date(event.occurred_at).toLocaleString()}</TooltipContent>
        </Tooltip>
        <div className="min-w-0">
          <div className="truncate font-medium">{actorLabel}</div>
          {actorEmail && <div className="truncate text-xs text-muted-foreground">{actorEmail}</div>}
        </div>
        <code className="text-xs font-mono text-foreground/80 truncate">{event.action}</code>
        <span className="text-xs text-muted-foreground truncate inline-flex items-center gap-1.5">
          <span className="truncate">
            {event.resource_type}
            {event.resource_id != null && (
              <span className="text-foreground/60"> #{event.resource_id}</span>
            )}
          </span>
          {event.outcome === "success" &&
            (() => {
              const href = resourceLink(event.resource_type, event.resource_id);
              if (!href) return null;
              return (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Link
                      to={href}
                      onClick={(e) => e.stopPropagation()}
                      className="text-muted-foreground hover:text-foreground shrink-0"
                      aria-label={t("audit.table.goToResource", {
                        type: event.resource_type,
                        id: event.resource_id,
                      })}
                    >
                      <ExternalLink className="size-3.5" />
                    </Link>
                  </TooltipTrigger>
                  <TooltipContent>{t("audit.table.goToResourceTooltip")}</TooltipContent>
                </Tooltip>
              );
            })()}
        </span>
        <Badge
          variant="outline"
          className={cn(
            "justify-self-start capitalize text-xs",
            event.outcome === "success"
              ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
              : "border-red-500/40 bg-red-500/10 text-red-600 dark:text-red-400",
          )}
        >
          {event.outcome}
        </Badge>
        <div className="justify-self-end">
          {isAdmin && (
            <Button
              variant="ghost"
              size="icon"
              className="size-7"
              onClick={(e) => {
                e.stopPropagation();
                setEditing(true);
              }}
              aria-label={t("audit.detail.editNotesAria")}
            >
              <Pencil className="size-3.5" />
            </Button>
          )}
        </div>
      </motion.div>

      {open && (
        <div className="px-4 py-4 bg-muted/10 border-b grid gap-4 md:grid-cols-2">
          <div>
            <div className="text-xs font-medium text-muted-foreground mb-1.5">
              {t("audit.detail.metadata")}
            </div>
            <pre className="text-xs font-mono bg-background border rounded-md p-3 overflow-auto max-h-72">
              {JSON.stringify(event.metadata, null, 2)}
            </pre>
          </div>
          <div>
            <div className="text-xs font-medium text-muted-foreground mb-1.5">
              {t("audit.detail.notes")}
            </div>
            {event.notes ? (
              <p className="text-sm whitespace-pre-wrap bg-background border rounded-md p-3">
                {event.notes}
              </p>
            ) : (
              <p className="text-sm text-muted-foreground italic bg-background border rounded-md p-3">
                {t("audit.detail.noNotes")}
              </p>
            )}
          </div>
        </div>
      )}

      {isAdmin && (
        <EditNotesDialog
          open={editing}
          onOpenChange={setEditing}
          event={event}
          tenantId={tenantId}
        />
      )}
    </>
  );
}

function EditNotesDialog({
  open,
  onOpenChange,
  event,
  tenantId,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  event: AuditEventOut;
  tenantId: number;
}) {
  const { t } = useTranslation();
  const [notes, setNotes] = useState(event.notes);
  const mutation = useUpdateAuditEventNotes(tenantId);

  return (
    <Dialog
      open={open}
      onOpenChange={(v) => {
        if (v) setNotes(event.notes);
        onOpenChange(v);
      }}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t("audit.editNotes.title")}</DialogTitle>
        </DialogHeader>
        <div className="space-y-3">
          <div className="text-xs text-muted-foreground">
            {t("audit.editNotes.eventLine", { id: event.id })}
            <code className="font-mono">{event.action}</code>
          </div>
          <Textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder={t("audit.editNotes.placeholder")}
            rows={6}
          />
        </div>
        <DialogFooter>
          <Button variant="ghost" onClick={() => onOpenChange(false)}>
            {t("common.cancel")}
          </Button>
          <Button
            onClick={() =>
              mutation.mutate(
                { eventId: event.id, notes },
                {
                  onSuccess: () => {
                    toast.success(t("audit.editNotes.successToast"));
                    onOpenChange(false);
                  },
                  onError: () => toast.error(t("audit.editNotes.errorToast")),
                },
              )
            }
            disabled={mutation.isPending}
          >
            {mutation.isPending ? t("audit.editNotes.saving") : t("audit.editNotes.save")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function relativeTime(iso: string, t: (key: string, opts?: Record<string, unknown>) => string) {
  const diff = Date.now() - new Date(iso).getTime();
  const s = Math.floor(diff / 1000);
  if (s < 60) return t("audit.relative.seconds", { n: s });
  const m = Math.floor(s / 60);
  if (m < 60) return t("audit.relative.minutes", { n: m });
  const h = Math.floor(m / 60);
  if (h < 24) return t("audit.relative.hours", { n: h });
  const d = Math.floor(h / 24);
  if (d < 30) return t("audit.relative.days", { n: d });
  return new Date(iso).toLocaleDateString();
}
