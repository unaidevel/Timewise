import { Plus } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useSearchParams } from "react-router";
import { toast } from "sonner";
import type { EmployeeOut } from "@/client";
import { Avatar, AvatarFallback } from "@/components/shadcn/avatar";
import { Badge } from "@/components/shadcn/badge";
import { Button } from "@/components/shadcn/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/shadcn/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
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
import { useRegister } from "@/features/auth/hooks";
import { useEmployees } from "@/features/employees/hooks";
import { useAddMember, useLinkEmployeeUser, useMembers } from "@/features/tenants/hooks";
import { formatDate } from "@/lib/format";

const MEMBER_ROLES = ["employee", "manager", "admin", "freelance"] as const;
type MemberRole = (typeof MEMBER_ROLES)[number];

export function MembersTab({ tenantId }: { tenantId: number }) {
  const members = useMembers(tenantId);
  const employees = useEmployees(tenantId);
  const { t } = useTranslation();
  const [searchParams, setSearchParams] = useSearchParams();
  const [open, setOpen] = useState(false);
  const [prefilledEmployeeId, setPrefilledEmployeeId] = useState<string>("");
  const rows = members.data ?? [];
  const employeeByUserId = useMemo(() => {
    const map = new Map<number, EmployeeOut>();
    for (const e of employees.data ?? []) {
      if (e.user_id != null) map.set(e.user_id, e);
    }
    return map;
  }, [employees.data]);

  const inviteParam = searchParams.get("invite");
  useEffect(() => {
    if (!inviteParam || !employees.data) return;
    const match = employees.data.find(
      (e) => String(e.id) === inviteParam && e.user_id == null && e.is_active,
    );
    if (match) {
      setPrefilledEmployeeId(String(match.id));
      setOpen(true);
    }
  }, [inviteParam, employees.data]);

  function clearInviteParam() {
    if (!searchParams.has("invite")) return;
    const next = new URLSearchParams(searchParams);
    next.delete("invite");
    setSearchParams(next, { replace: true });
  }

  function handleOpenChange(o: boolean) {
    setOpen(o);
    if (!o) {
      setPrefilledEmployeeId("");
      clearInviteParam();
    }
  }

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <div>
          <CardTitle className="text-base">{t("settings.members.title")}</CardTitle>
          <CardDescription>{t("settings.members.subtitle")}</CardDescription>
        </div>
        <Dialog open={open} onOpenChange={handleOpenChange}>
          <DialogTrigger asChild>
            <Button variant="outline">
              <Plus className="size-4 mr-1.5" />
              {t("settings.members.invite")}
            </Button>
          </DialogTrigger>
          {open && (
            <InviteMemberDialog
              key={prefilledEmployeeId || "new"}
              tenantId={tenantId}
              prefilledEmployeeId={prefilledEmployeeId}
              onDone={() => handleOpenChange(false)}
            />
          )}
        </Dialog>
      </CardHeader>
      <CardContent className="p-0">
        <div className="divide-y">
          {rows.map((m) => {
            const employee = employeeByUserId.get(m.user_id);
            const displayName =
              employee?.full_name ??
              m.full_name ??
              t("settings.members.userLabel", { id: m.user_id });
            const displayEmail = employee?.email ?? m.email;
            return (
              <div key={m.id} className="flex items-center gap-3 px-6 py-3">
                <Avatar className="size-9">
                  <AvatarFallback className="bg-primary/10 text-primary text-xs font-semibold">
                    #{m.user_id}
                  </AvatarFallback>
                </Avatar>
                <div className="flex-1 min-w-0">
                  <div className="font-medium truncate">{displayName}</div>
                  <div className="text-xs text-muted-foreground truncate">
                    {displayEmail
                      ? `${displayEmail} · ${t("settings.members.joined", { date: formatDate(m.joined_at) })}`
                      : t("settings.members.joined", { date: formatDate(m.joined_at) })}
                  </div>
                </div>
                <Badge variant="outline" className="capitalize">
                  {m.role}
                </Badge>
                {m.left_at && (
                  <Badge variant="outline" className="text-muted-foreground">
                    {t("settings.members.inactive")}
                  </Badge>
                )}
              </div>
            );
          })}
          {rows.length === 0 && (
            <div className="p-12 text-center text-sm text-muted-foreground">
              {members.isLoading ? t("settings.members.loading") : t("settings.members.empty")}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function InviteMemberDialog({
  tenantId,
  prefilledEmployeeId,
  onDone,
}: {
  tenantId: number;
  prefilledEmployeeId?: string;
  onDone: () => void;
}) {
  const { t } = useTranslation();
  const employees = useEmployees(tenantId);
  const register = useRegister();
  const addMember = useAddMember(tenantId);
  const linkEmployee = useLinkEmployeeUser(tenantId);

  // Seed from the prefilled employee once at mount. The parent remounts this
  // dialog via `key={prefilledEmployeeId}` when the prefill changes, so the
  // initializers re-run with fresh values — no syncing effect, no extra render.
  const prefilled = prefilledEmployeeId
    ? (employees.data ?? []).find((e) => String(e.id) === prefilledEmployeeId)
    : undefined;
  const [fullName, setFullName] = useState(prefilled?.full_name ?? "");
  const [email, setEmail] = useState(prefilled?.email ?? "");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<MemberRole>("employee");
  const [employeeId, setEmployeeId] = useState<string>(prefilled ? String(prefilled.id) : "");

  const unlinkedEmployees = useMemo(
    () => (employees.data ?? []).filter((e) => e.user_id == null && e.is_active),
    [employees.data],
  );

  const submitting = register.isPending || addMember.isPending || linkEmployee.isPending;
  const canSubmit =
    !!fullName.trim() && !!email.trim() && !!password && !!employeeId && !submitting;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;
    try {
      const user = await register.mutateAsync({
        email: email.trim(),
        full_name: fullName.trim(),
        password,
      });
      await addMember.mutateAsync({ user_id: user.id, role });
      await linkEmployee.mutateAsync({
        employeeId: Number(employeeId),
        body: { user_id: user.id },
      });
      toast.success(t("settings.members.inviteDialog.successToast"));
      onDone();
    } catch {
      toast.error(t("settings.members.inviteDialog.errorToast"));
    }
  }

  return (
    <DialogContent className="sm:max-w-md">
      <DialogHeader>
        <DialogTitle>{t("settings.members.inviteDialog.title")}</DialogTitle>
        <DialogDescription>{t("settings.members.inviteDialog.description")}</DialogDescription>
      </DialogHeader>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-1.5">
          <Label className="text-xs" htmlFor="invite-fullname">
            {t("settings.members.inviteDialog.fullName")}
          </Label>
          <Input
            id="invite-fullname"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            autoComplete="off"
            required
          />
        </div>
        <div className="space-y-1.5">
          <Label className="text-xs" htmlFor="invite-email">
            {t("settings.members.inviteDialog.email")}
          </Label>
          <Input
            id="invite-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="off"
            required
          />
        </div>
        <div className="space-y-1.5">
          <Label className="text-xs" htmlFor="invite-password">
            {t("settings.members.inviteDialog.password")}
          </Label>
          <Input
            id="invite-password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="new-password"
            required
          />
        </div>
        <div className="space-y-1.5">
          <Label className="text-xs">{t("settings.members.inviteDialog.role")}</Label>
          <Select value={role} onValueChange={(v) => setRole(v as MemberRole)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {MEMBER_ROLES.map((r) => (
                <SelectItem key={r} value={r} className="capitalize">
                  {t(`settings.members.roles.${r}`)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-1.5">
          <Label className="text-xs">{t("settings.members.inviteDialog.employee")}</Label>
          <Select value={employeeId} onValueChange={setEmployeeId}>
            <SelectTrigger>
              <SelectValue placeholder={t("settings.members.inviteDialog.employeePlaceholder")} />
            </SelectTrigger>
            <SelectContent>
              {unlinkedEmployees.length === 0 ? (
                <div className="px-2 py-1.5 text-xs text-muted-foreground">
                  {t("settings.members.inviteDialog.noUnlinked")}
                </div>
              ) : (
                unlinkedEmployees.map((e) => (
                  <SelectItem key={e.id} value={String(e.id)}>
                    {e.full_name} · {e.email}
                  </SelectItem>
                ))
              )}
            </SelectContent>
          </Select>
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="outline" onClick={onDone} disabled={submitting}>
            {t("common.cancel")}
          </Button>
          <Button type="submit" disabled={!canSubmit}>
            {submitting
              ? t("settings.members.inviteDialog.submitting")
              : t("settings.members.inviteDialog.submit")}
          </Button>
        </div>
      </form>
    </DialogContent>
  );
}
