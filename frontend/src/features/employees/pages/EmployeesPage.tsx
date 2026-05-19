import { motion } from "framer-motion";
import { Calendar, Filter, Mail, Plus, Search, Users } from "lucide-react";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";
import type { EmployeeOut } from "@/client";
import { EmptyState } from "@/components/EmptyState";
import { Avatar, AvatarFallback } from "@/components/shadcn/avatar";
import { Badge } from "@/components/shadcn/badge";
import { Button } from "@/components/shadcn/button";
import { Card, CardContent } from "@/components/shadcn/card";
import { Input } from "@/components/shadcn/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/shadcn/select";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/shadcn/sheet";
import { Skeleton } from "@/components/shadcn/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/shadcn/table";
import { useDepartments } from "@/features/departments/hooks";
import { useRoles } from "@/features/roles/hooks";
import { useCurrentTenantId } from "@/features/tenants/hooks";
import { formatDate } from "@/lib/format";
import { cn } from "@/lib/utils";
import { useCreateEmployee, useDeactivateEmployee, useEmployees } from "../hooks";

const initials = (name: string) =>
  name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

const statusStyle = {
  active: "bg-success/15 text-success border-success/20",
  inactive: "bg-muted text-muted-foreground border-border",
} as const;

export default function EmployeesPage() {
  const tenantId = useCurrentTenantId();
  const employees = useEmployees(tenantId);
  const { t } = useTranslation();
  const [q, setQ] = useState("");
  const [status, setStatus] = useState<"all" | "active" | "inactive">("all");
  const [selected, setSelected] = useState<EmployeeOut | null>(null);
  const [createOpen, setCreateOpen] = useState(false);

  const filtered = useMemo(() => {
    const list = employees.data ?? [];
    return list.filter((e) => {
      if (status === "active" && !e.is_active) return false;
      if (status === "inactive" && e.is_active) return false;
      if (q && !`${e.full_name} ${e.email}`.toLowerCase().includes(q.toLowerCase())) return false;
      return true;
    });
  }, [employees.data, q, status]);

  const isEmpty = employees.isSuccess && (employees.data?.length ?? 0) === 0;
  const total = employees.data?.length ?? 0;
  const activeCount = employees.data?.filter((e) => e.is_active).length ?? 0;

  return (
    <div className="space-y-6">
      <header className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">
            {t("workforce.employees.title")}
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            {t("workforce.employees.summary", { total, active: activeCount })}
          </p>
        </div>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="size-4 mr-2" /> {t("workforce.employees.new")}
        </Button>
      </header>

      {isEmpty ? (
        <EmptyState
          icon={Users}
          title={t("workforce.employees.empty.title")}
          description={t("workforce.employees.empty.description")}
          action={
            <Button onClick={() => setCreateOpen(true)}>
              <Plus className="size-4 mr-2" /> {t("workforce.employees.new")}
            </Button>
          }
        />
      ) : (
        <>
          <div className="flex flex-wrap gap-2 items-center">
            <div className="relative flex-1 min-w-[220px] max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
              <Input
                placeholder={t("workforce.employees.searchPlaceholder")}
                className="pl-9"
                value={q}
                onChange={(e) => setQ(e.target.value)}
              />
            </div>
            <Select value={status} onValueChange={(v) => setStatus(v as typeof status)}>
              <SelectTrigger className="w-[160px]">
                <Filter className="size-3.5 mr-1.5" />
                <SelectValue placeholder={t("workforce.employees.filterStatusPlaceholder")} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t("common.all")}</SelectItem>
                <SelectItem value="active">{t("common.active")}</SelectItem>
                <SelectItem value="inactive">{t("common.inactive")}</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow className="hover:bg-transparent">
                    <TableHead>{t("workforce.employees.columns.name")}</TableHead>
                    <TableHead>{t("workforce.employees.columns.email")}</TableHead>
                    <TableHead>{t("workforce.employees.columns.hired")}</TableHead>
                    <TableHead>{t("workforce.employees.columns.status")}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {employees.isLoading &&
                    ["a", "b", "c", "d", "e", "f"].map((row) => (
                      <TableRow key={row}>
                        {["name", "email", "hired", "status"].map((col) => (
                          <TableCell key={col}>
                            <Skeleton className="h-5 w-32" />
                          </TableCell>
                        ))}
                      </TableRow>
                    ))}
                  {filtered.map((e, i) => (
                    <motion.tr
                      key={e.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: Math.min(i * 0.015, 0.2) }}
                      className="border-b cursor-pointer hover:bg-muted/40 transition"
                      onClick={() => setSelected(e)}
                    >
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <Avatar className="size-9">
                            <AvatarFallback className="bg-primary/10 text-primary text-xs font-semibold">
                              {initials(e.full_name)}
                            </AvatarFallback>
                          </Avatar>
                          <Link
                            to={`/employees/${e.id}`}
                            className="font-medium hover:underline"
                            onClick={(ev) => ev.stopPropagation()}
                          >
                            {e.full_name}
                          </Link>
                        </div>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">{e.email}</TableCell>
                      <TableCell className="text-sm">{formatDate(e.hired_at)}</TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className={cn(
                            "capitalize",
                            e.is_active ? statusStyle.active : statusStyle.inactive,
                          )}
                        >
                          {e.is_active ? t("common.active") : t("common.inactive")}
                        </Badge>
                      </TableCell>
                    </motion.tr>
                  ))}
                  {!employees.isLoading && filtered.length === 0 && (
                    <TableRow>
                      <TableCell
                        colSpan={4}
                        className="text-center text-sm text-muted-foreground py-12"
                      >
                        {t("workforce.employees.noMatch")}
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </>
      )}

      <Sheet open={!!selected} onOpenChange={(o) => !o && setSelected(null)}>
        <SheetContent className="sm:max-w-md">
          {selected && (
            <>
              <SheetHeader>
                <div className="flex items-center gap-4 mb-2">
                  <Avatar className="size-14">
                    <AvatarFallback className="bg-primary/10 text-primary text-base font-semibold">
                      {initials(selected.full_name)}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <SheetTitle className="text-left">{selected.full_name}</SheetTitle>
                    <SheetDescription className="text-left">{selected.email}</SheetDescription>
                  </div>
                </div>
              </SheetHeader>
              <div className="px-1 space-y-4 mt-2">
                <DetailRow
                  icon={Mail}
                  label={t("workforce.employees.detail.emailLabel")}
                  value={selected.email}
                />
                <DetailRow
                  icon={Calendar}
                  label={t("workforce.employees.detail.hiredLabel")}
                  value={formatDate(selected.hired_at)}
                />
                <div className="pt-2 flex items-center gap-2">
                  <Badge
                    variant="outline"
                    className={cn(selected.is_active ? statusStyle.active : statusStyle.inactive)}
                  >
                    {selected.is_active ? t("common.active") : t("common.inactive")}
                  </Badge>
                  <Link
                    to={`/employees/${selected.id}`}
                    className="ml-auto text-sm font-medium text-primary hover:underline"
                  >
                    {t("common.viewDetail")}
                  </Link>
                </div>
                {selected.is_active && (
                  <DeactivateButton id={selected.id} onDone={() => setSelected(null)} />
                )}
              </div>
            </>
          )}
        </SheetContent>
      </Sheet>

      <CreateEmployeeSheet open={createOpen} onClose={() => setCreateOpen(false)} />
    </div>
  );
}

function DetailRow({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-start gap-3 text-sm">
      <Icon className="size-4 text-muted-foreground mt-0.5" />
      <div className="flex-1">
        <div className="text-xs text-muted-foreground">{label}</div>
        <div className="font-medium">{value}</div>
      </div>
    </div>
  );
}

function DeactivateButton({ id, onDone }: { id: number; onDone: () => void }) {
  const tenantId = useCurrentTenantId();
  const deactivate = useDeactivateEmployee(tenantId);
  const { t } = useTranslation();
  return (
    <Button
      variant="outline"
      className="w-full"
      disabled={deactivate.isPending}
      onClick={() => deactivate.mutate(id, { onSuccess: onDone })}
    >
      {deactivate.isPending
        ? t("workforce.employees.deactivating")
        : t("workforce.employees.deactivate")}
    </Button>
  );
}

function CreateEmployeeSheet({ open, onClose }: { open: boolean; onClose: () => void }) {
  const tenantId = useCurrentTenantId();
  const departments = useDepartments(tenantId);
  const roles = useRoles(tenantId);
  const create = useCreateEmployee(tenantId);
  const { t } = useTranslation();

  const [form, setForm] = useState({
    full_name: "",
    email: "",
    department_id: "",
    role_id: "",
    hourly_rate: "",
    contract_hours_per_week: "40",
    hired_at: new Date().toISOString().slice(0, 10),
  });

  function reset() {
    setForm({
      full_name: "",
      email: "",
      department_id: "",
      role_id: "",
      hourly_rate: "",
      contract_hours_per_week: "40",
      hired_at: new Date().toISOString().slice(0, 10),
    });
  }

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    create.mutate(
      {
        full_name: form.full_name,
        email: form.email,
        department_id: Number(form.department_id),
        role_id: Number(form.role_id),
        hourly_rate: form.hourly_rate,
        contract_hours_per_week: Number(form.contract_hours_per_week),
        hired_at: form.hired_at,
      },
      {
        onSuccess: () => {
          reset();
          onClose();
        },
      },
    );
  }

  return (
    <Sheet open={open} onOpenChange={(o) => !o && onClose()}>
      <SheetContent className="sm:max-w-lg">
        <SheetHeader>
          <SheetTitle>{t("workforce.employees.create.title")}</SheetTitle>
          <SheetDescription>{t("workforce.employees.create.subtitle")}</SheetDescription>
        </SheetHeader>
        <form onSubmit={onSubmit} className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-6">
          <Field label={t("workforce.employees.create.fullName")} required>
            <Input
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              required
            />
          </Field>
          <Field label={t("workforce.employees.create.email")} required>
            <Input
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              required
            />
          </Field>
          <Field label={t("workforce.employees.create.department")} required>
            <Select
              value={form.department_id}
              onValueChange={(v) => setForm({ ...form, department_id: v })}
            >
              <SelectTrigger>
                <SelectValue placeholder={t("workforce.employees.create.selectPlaceholder")} />
              </SelectTrigger>
              <SelectContent>
                {(departments.data ?? [])
                  .filter((d) => d.is_active)
                  .map((d) => (
                    <SelectItem key={d.id} value={String(d.id)}>
                      {d.name}
                    </SelectItem>
                  ))}
              </SelectContent>
            </Select>
          </Field>
          <Field label={t("workforce.employees.create.role")} required>
            <Select value={form.role_id} onValueChange={(v) => setForm({ ...form, role_id: v })}>
              <SelectTrigger>
                <SelectValue placeholder={t("workforce.employees.create.selectPlaceholder")} />
              </SelectTrigger>
              <SelectContent>
                {(roles.data ?? [])
                  .filter((r) => r.is_active)
                  .map((r) => (
                    <SelectItem key={r.id} value={String(r.id)}>
                      {r.name}
                    </SelectItem>
                  ))}
              </SelectContent>
            </Select>
          </Field>
          <Field label={t("workforce.employees.create.hourlyRate")} required>
            <Input
              type="number"
              step="0.01"
              value={form.hourly_rate}
              onChange={(e) => setForm({ ...form, hourly_rate: e.target.value })}
              required
            />
          </Field>
          <Field label={t("workforce.employees.create.weeklyHours")} required>
            <Input
              type="number"
              value={form.contract_hours_per_week}
              onChange={(e) => setForm({ ...form, contract_hours_per_week: e.target.value })}
              required
            />
          </Field>
          <Field label={t("workforce.employees.create.hiredAt")} required>
            <Input
              type="date"
              value={form.hired_at}
              onChange={(e) => setForm({ ...form, hired_at: e.target.value })}
              required
            />
          </Field>
          <div className="col-span-full flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={onClose}>
              {t("common.cancel")}
            </Button>
            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? t("common.creating") : t("common.create")}
            </Button>
          </div>
        </form>
      </SheetContent>
    </Sheet>
  );
}

function Field({
  label,
  required,
  children,
}: {
  label: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5 text-sm">
      <div className="text-xs font-medium text-muted-foreground">
        {label}
        {required && <span className="text-destructive"> *</span>}
      </div>
      {children}
    </div>
  );
}
