import { motion } from "framer-motion";
import { ChevronDown, ChevronRight, Pencil, ScrollText, X } from "lucide-react";
import { useMemo, useState } from "react";
import { useSearchParams } from "react-router";
import { toast } from "sonner";
import type { AuditEventOut, EmployeeOut } from "@/client";
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

export default function AuditPage() {
  const tenantId = useCurrentTenantId();
  const user = useAuthStore((s) => s.user);
  const members = useMembers(tenantId);
  const employees = useEmployees(tenantId);
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

  const employeesById = useMemo(() => {
    const m = new Map<number, EmployeeOut>();
    for (const e of employees.data ?? []) m.set(e.id, e);
    return m;
  }, [employees.data]);

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
        title="No workspace selected"
        description="Pick a workspace from the sidebar to see its audit log."
      />
    );
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight flex items-center gap-2">
          <ScrollText className="size-7 text-primary" />
          Registro de auditoría
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Cada acción tomada en este workspace, en orden cronológico inverso.
        </p>
      </header>

      <Card className="sticky top-16 z-10 backdrop-blur-md bg-background/85">
        <CardContent className="py-4 grid gap-3 md:grid-cols-[1fr_1fr_180px_220px_auto]">
          <div className="space-y-1.5">
            <Label className="text-xs">Acción contiene</Label>
            <Input
              placeholder="p. ej. time_report.submitted"
              value={actionQ}
              onChange={(e) => patchParams({ action: e.target.value })}
            />
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs">Tipo de recurso</Label>
            <Input
              placeholder="p. ej. TimeReport"
              value={resourceQ}
              onChange={(e) => patchParams({ resource_type: e.target.value })}
            />
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs">Resultado</Label>
            <Select
              value={outcomeQ ?? "any"}
              onValueChange={(v) => patchParams({ outcome: v === "any" ? null : v })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="any">Cualquiera</SelectItem>
                <SelectItem value="success">Éxito</SelectItem>
                <SelectItem value="failure">Fallo</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs">Actor</Label>
            <Select
              value={actorQ ?? "any"}
              onValueChange={(v) => patchParams({ actor_id: v === "any" ? null : v })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="any">Cualquiera</SelectItem>
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
                Limpiar
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3 flex-row items-center justify-between">
          <CardTitle className="text-base font-medium">
            {eventsQ.isPending ? "Cargando…" : `${events.length} eventos`}
          </CardTitle>
        </CardHeader>
        <CardContent className="px-0">
          <div className="border-t">
            <div className="grid grid-cols-[40px_180px_1fr_1fr_1fr_110px_60px] gap-3 px-4 py-2.5 text-xs font-medium text-muted-foreground bg-muted/30 border-b">
              <span />
              <span>Hora</span>
              <span>Actor</span>
              <span>Acción</span>
              <span>Recurso</span>
              <span>Resultado</span>
              <span />
            </div>
            <TooltipProvider delayDuration={200}>
              {events.map((ev) => (
                <Row
                  key={ev.id}
                  event={ev}
                  actor={employeesById.get(ev.actor_id)}
                  isAdmin={isAdmin}
                  tenantId={tenantId}
                />
              ))}
            </TooltipProvider>
            {!eventsQ.isPending && events.length === 0 && (
              <div className="px-4 py-12 text-center text-sm text-muted-foreground">
                Ningún evento coincide con los filtros.
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
  isAdmin,
  tenantId,
}: {
  event: AuditEventOut;
  actor: EmployeeOut | undefined;
  isAdmin: boolean;
  tenantId: number;
}) {
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState(false);
  const actorLabel = actor?.full_name ?? `Usuario #${event.actor_id}`;
  const actorEmail = actor?.email;

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
              {relativeTime(event.occurred_at)}
            </span>
          </TooltipTrigger>
          <TooltipContent>{new Date(event.occurred_at).toLocaleString()}</TooltipContent>
        </Tooltip>
        <div className="min-w-0">
          <div className="truncate font-medium">{actorLabel}</div>
          {actorEmail && <div className="truncate text-xs text-muted-foreground">{actorEmail}</div>}
        </div>
        <code className="text-xs font-mono text-foreground/80 truncate">{event.action}</code>
        <span className="text-xs text-muted-foreground truncate">
          {event.resource_type}
          {event.resource_id != null && (
            <span className="text-foreground/60"> #{event.resource_id}</span>
          )}
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
              aria-label="Editar notas"
            >
              <Pencil className="size-3.5" />
            </Button>
          )}
        </div>
      </motion.div>

      {open && (
        <div className="px-4 py-4 bg-muted/10 border-b grid gap-4 md:grid-cols-2">
          <div>
            <div className="text-xs font-medium text-muted-foreground mb-1.5">Metadata</div>
            <pre className="text-xs font-mono bg-background border rounded-md p-3 overflow-auto max-h-72">
              {JSON.stringify(event.metadata, null, 2)}
            </pre>
          </div>
          <div>
            <div className="text-xs font-medium text-muted-foreground mb-1.5">Notas</div>
            {event.notes ? (
              <p className="text-sm whitespace-pre-wrap bg-background border rounded-md p-3">
                {event.notes}
              </p>
            ) : (
              <p className="text-sm text-muted-foreground italic bg-background border rounded-md p-3">
                Sin notas todavía.
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
          <DialogTitle>Editar notas</DialogTitle>
        </DialogHeader>
        <div className="space-y-3">
          <div className="text-xs text-muted-foreground">
            Evento #{event.id} — <code className="font-mono">{event.action}</code>
          </div>
          <Textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Contexto, seguimiento, notas de investigación…"
            rows={6}
          />
        </div>
        <DialogFooter>
          <Button variant="ghost" onClick={() => onOpenChange(false)}>
            Cancelar
          </Button>
          <Button
            onClick={() =>
              mutation.mutate(
                { eventId: event.id, notes },
                {
                  onSuccess: () => {
                    toast.success("Notas actualizadas");
                    onOpenChange(false);
                  },
                  onError: () => toast.error("No se pudieron guardar las notas"),
                },
              )
            }
            disabled={mutation.isPending}
          >
            {mutation.isPending ? "Guardando…" : "Guardar"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function relativeTime(iso: string) {
  const diff = Date.now() - new Date(iso).getTime();
  const s = Math.floor(diff / 1000);
  if (s < 60) return `hace ${s}s`;
  const m = Math.floor(s / 60);
  if (m < 60) return `hace ${m}m`;
  const h = Math.floor(m / 60);
  if (h < 24) return `hace ${h}h`;
  const d = Math.floor(h / 24);
  if (d < 30) return `hace ${d}d`;
  return new Date(iso).toLocaleDateString();
}
