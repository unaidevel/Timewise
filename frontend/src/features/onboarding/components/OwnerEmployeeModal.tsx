import { Plus } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/shadcn/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
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
import { useAuthStore } from "@/features/auth/store";
import { useRoles } from "@/features/roles/hooks";
import { useCurrentTenantId } from "@/features/tenants/hooks";

const NEW_DEPT_SENTINEL = "__new__";

export type OwnerEmployeeFormData =
  | { skip: true }
  | {
      skip: false;
      departmentId: number | null;
      newDepartmentName: string | null;
      roleId: number;
      hourlyRate: string;
      contractHours: number;
    };

export function OwnerEmployeeModal({
  open,
  onSubmit,
}: {
  open: boolean;
  /** Called with the collected form data. Parent is responsible for API calls. */
  onSubmit: (data: OwnerEmployeeFormData) => void;
}) {
  const { t } = useTranslation();
  const tenantId = useCurrentTenantId();
  const user = useAuthStore((s) => s.user);
  const roles = useRoles(tenantId);

  const [departmentId, setDepartmentId] = useState("");
  const [newDeptName, setNewDeptName] = useState("");
  const [roleId, setRoleId] = useState("");
  const [hourlyRate, setHourlyRate] = useState("");
  const [contractHours, setContractHours] = useState("40");

  const isCreatingNewDept = departmentId === NEW_DEPT_SENTINEL;
  const activeRoles = (roles.data ?? []).filter((r) => r.is_active);

  const canSubmit =
    roleId &&
    hourlyRate &&
    contractHours &&
    (isCreatingNewDept ? newDeptName.trim() : departmentId);

  function reset() {
    setDepartmentId("");
    setNewDeptName("");
    setRoleId("");
    setHourlyRate("");
    setContractHours("40");
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    onSubmit({
      skip: false,
      departmentId: isCreatingNewDept ? null : Number(departmentId),
      newDepartmentName: isCreatingNewDept ? newDeptName.trim() : null,
      roleId: Number(roleId),
      hourlyRate,
      contractHours: Number(contractHours),
    });
    reset();
  }

  function handleSkip() {
    reset();
    onSubmit({ skip: true });
  }

  return (
    <Dialog open={open}>
      <DialogContent
        className="sm:max-w-md"
        onEscapeKeyDown={(e) => e.preventDefault()}
        onPointerDownOutside={(e) => e.preventDefault()}
        onInteractOutside={(e) => e.preventDefault()}
      >
        <DialogHeader>
          <DialogTitle>{t("onboarding.ownerEmployee.title")}</DialogTitle>
          <DialogDescription>{t("onboarding.ownerEmployee.description")}</DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4 mt-2">
          {/* Name — read-only, pre-filled */}
          <div className="space-y-1.5 text-sm">
            <Label className="text-xs font-medium text-muted-foreground">
              {t("onboarding.ownerEmployee.fullName")}
            </Label>
            <Input value={user?.full_name ?? ""} disabled />
          </div>

          {/* Email — read-only, pre-filled */}
          <div className="space-y-1.5 text-sm">
            <Label className="text-xs font-medium text-muted-foreground">
              {t("onboarding.ownerEmployee.email")}
            </Label>
            <Input value={user?.email ?? ""} disabled />
          </div>

          {/* Department — free text for new, since seed depts don't exist yet */}
          <div className="space-y-1.5 text-sm">
            <Label className="text-xs font-medium text-muted-foreground">
              {t("onboarding.ownerEmployee.department")} <span className="text-destructive">*</span>
            </Label>
            <Select value={departmentId} onValueChange={setDepartmentId}>
              <SelectTrigger>
                <SelectValue placeholder={t("onboarding.ownerEmployee.selectPlaceholder")} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={NEW_DEPT_SENTINEL}>
                  <span className="flex items-center gap-1.5 text-primary">
                    <Plus className="size-3.5" />
                    {t("onboarding.ownerEmployee.newDepartment")}
                  </span>
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Inline new department name */}
          {isCreatingNewDept && (
            <div className="space-y-1.5 text-sm">
              <Label className="text-xs font-medium text-muted-foreground">
                {t("onboarding.ownerEmployee.newDepartmentName")}{" "}
                <span className="text-destructive">*</span>
              </Label>
              <Input
                value={newDeptName}
                onChange={(e) => setNewDeptName(e.target.value)}
                placeholder={t("onboarding.ownerEmployee.newDepartmentPlaceholder")}
                autoFocus
              />
            </div>
          )}

          {/* Role */}
          <div className="space-y-1.5 text-sm">
            <Label className="text-xs font-medium text-muted-foreground">
              {t("onboarding.ownerEmployee.role")} <span className="text-destructive">*</span>
            </Label>
            <Select value={roleId} onValueChange={setRoleId}>
              <SelectTrigger>
                <SelectValue placeholder={t("onboarding.ownerEmployee.selectPlaceholder")} />
              </SelectTrigger>
              <SelectContent>
                {activeRoles.map((r) => (
                  <SelectItem key={r.id} value={String(r.id)}>
                    {r.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Hourly rate + contract hours side by side */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5 text-sm">
              <Label className="text-xs font-medium text-muted-foreground">
                {t("onboarding.ownerEmployee.hourlyRate")}{" "}
                <span className="text-destructive">*</span>
              </Label>
              <Input
                type="number"
                step="0.01"
                min="0"
                value={hourlyRate}
                onChange={(e) => setHourlyRate(e.target.value)}
                required
              />
            </div>
            <div className="space-y-1.5 text-sm">
              <Label className="text-xs font-medium text-muted-foreground">
                {t("onboarding.ownerEmployee.contractHours")}{" "}
                <span className="text-destructive">*</span>
              </Label>
              <Input
                type="number"
                min="1"
                value={contractHours}
                onChange={(e) => setContractHours(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="flex justify-between gap-2 pt-2">
            <Button type="button" variant="ghost" onClick={handleSkip}>
              {t("onboarding.ownerEmployee.skip")}
            </Button>
            <Button type="submit" disabled={!canSubmit}>
              {t("onboarding.ownerEmployee.create")}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
