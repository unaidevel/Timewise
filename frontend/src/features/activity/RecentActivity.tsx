import { m } from "framer-motion";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import type { AuditEventOut, EmployeeOut, TenantMemberResponse } from "@/client";
import { Avatar, AvatarFallback } from "@/components/shadcn/avatar";
import { Skeleton } from "@/components/shadcn/skeleton";
import { useAuditEvents } from "@/features/audit/hooks";
import { useEmployees } from "@/features/employees/hooks";
import { useMembers } from "@/features/tenants/hooks";

interface RecentActivityProps {
  tenantId: number | null;
  actorId?: number | null;
  limit?: number;
}

export function RecentActivity({ tenantId, actorId = null, limit = 6 }: RecentActivityProps) {
  const { t } = useTranslation();
  const events = useAuditEvents(tenantId, actorId != null ? { actor_id: actorId } : {});
  const employees = useEmployees(tenantId);
  const members = useMembers(tenantId);

  const employeesByUserId = useMemo(() => {
    const m = new Map<number, EmployeeOut>();
    for (const e of employees.data ?? []) if (e.user_id != null) m.set(e.user_id, e);
    return m;
  }, [employees.data]);

  const visible = useMemo(
    () =>
      (events.data ?? [])
        .filter((e) => e.outcome === "success")
        .slice()
        .sort((a, b) => +new Date(b.occurred_at) - +new Date(a.occurred_at))
        .slice(0, limit),
    [events.data, limit],
  );

  if (events.isPending) {
    return (
      <div className="space-y-4">
        {["a", "b", "c"].map((k) => (
          <div key={k} className="flex gap-3">
            <Skeleton className="size-8 rounded-full" />
            <div className="flex-1 space-y-2">
              <Skeleton className="h-3 w-2/3" />
              <Skeleton className="h-2 w-20" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (visible.length === 0) {
    return <p className="text-sm text-muted-foreground py-2">{t("activity.empty")}</p>;
  }

  return (
    <div className="space-y-4">
      {visible.map((ev, i) => (
        <ActivityRow
          key={ev.id}
          event={ev}
          actor={employeesByUserId.get(ev.actor_id)}
          member={members.data?.find((m) => m.user_id === ev.actor_id)}
          index={i}
        />
      ))}
    </div>
  );
}

interface ActivityRowProps {
  event: AuditEventOut;
  actor: EmployeeOut | undefined;
  member: TenantMemberResponse | undefined;
  index: number;
}

function ActivityRow({ event, actor, member, index }: ActivityRowProps) {
  const { t } = useTranslation();
  const actorName = actor?.full_name ?? member?.full_name ?? t("activity.unknownActor");
  const sentence = humanizeAction(event, t);
  const initials = actorName
    .split(" ")
    .map((n) => n[0])
    .filter(Boolean)
    .slice(0, 2)
    .join("")
    .toUpperCase();

  return (
    <m.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.04 }}
      className="flex gap-3"
    >
      <Avatar className="size-8 mt-0.5">
        <AvatarFallback className="text-[10px] bg-primary/10 text-primary font-semibold">
          {initials || "?"}
        </AvatarFallback>
      </Avatar>
      <div className="flex-1 min-w-0">
        <p className="text-sm leading-tight">
          <span className="font-medium">{actorName}</span>{" "}
          <span className="text-muted-foreground">{sentence}</span>
        </p>
        <p className="text-xs text-muted-foreground mt-1">{relativeTime(event.occurred_at, t)}</p>
      </div>
    </m.div>
  );
}

function humanizeAction(
  event: AuditEventOut,
  t: (key: string, opts?: Record<string, unknown>) => string,
): string {
  const key = `activity.actions.${event.action}`;
  const translated = t(key);
  if (translated !== key) return translated;
  const resource =
    event.resource_id != null
      ? `${event.resource_type} #${event.resource_id}`
      : event.resource_type;
  return t("activity.actions.fallback", { action: event.action, resource });
}

function relativeTime(
  iso: string,
  t: (key: string, opts?: Record<string, unknown>) => string,
): string {
  const diff = Date.now() - new Date(iso).getTime();
  const s = Math.floor(diff / 1000);
  if (s < 60) return t("activity.relative.seconds", { n: s });
  const m = Math.floor(s / 60);
  if (m < 60) return t("activity.relative.minutes", { n: m });
  const h = Math.floor(m / 60);
  if (h < 24) return t("activity.relative.hours", { n: h });
  const d = Math.floor(h / 24);
  if (d < 30) return t("activity.relative.days", { n: d });
  return new Date(iso).toLocaleDateString();
}
