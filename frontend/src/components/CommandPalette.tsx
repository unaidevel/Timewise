import {
  Calculator,
  CheckSquare,
  Clock,
  FolderKanban,
  LayoutDashboard,
  Tag,
  Users,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/components/shadcn/command";
import { useEmployees } from "@/features/employees/hooks";
import { useCurrentTenantId } from "@/features/tenants/hooks";

export function CommandPalette({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const tenantId = useCurrentTenantId();
  const employees = useEmployees(open ? tenantId : null);

  const peopleItems = useMemo(() => (employees.data ?? []).slice(0, 8), [employees.data]);

  const pages = [
    { to: "/", label: t("commandPalette.pages.home"), icon: LayoutDashboard },
    { to: "/employees", label: t("commandPalette.pages.employees"), icon: Users },
    { to: "/departments", label: t("commandPalette.pages.departments"), icon: FolderKanban },
    { to: "/roles", label: t("commandPalette.pages.roles"), icon: Tag },
    { to: "/periods", label: t("commandPalette.pages.periods"), icon: Clock },
    { to: "/reports", label: t("commandPalette.pages.reports"), icon: Clock },
    { to: "/approvals", label: t("commandPalette.pages.approvals"), icon: CheckSquare },
    { to: "/settings", label: t("commandPalette.pages.costingRules"), icon: Calculator },
  ];

  const go = (to: string) => {
    onOpenChange(false);
    navigate(to);
  };

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange}>
      <CommandInput placeholder={t("commandPalette.placeholder")} />
      <CommandList>
        <CommandEmpty>{t("commandPalette.empty")}</CommandEmpty>
        <CommandGroup heading={t("commandPalette.navigate")}>
          {pages.map((p) => (
            <CommandItem key={p.to} onSelect={() => go(p.to)}>
              <p.icon className="size-4 mr-2" />
              {p.label}
            </CommandItem>
          ))}
        </CommandGroup>
        {peopleItems.length > 0 && (
          <>
            <CommandSeparator />
            <CommandGroup heading={t("commandPalette.employees")}>
              {peopleItems.map((e) => (
                <CommandItem
                  key={e.id}
                  value={`${e.full_name} ${e.email}`}
                  onSelect={() => go(`/employees/${e.id}`)}
                >
                  <div className="size-5 rounded-full bg-primary/10 text-primary text-[10px] grid place-items-center font-semibold mr-2">
                    {e.full_name
                      .split(" ")
                      .map((n) => n[0])
                      .join("")
                      .slice(0, 2)
                      .toUpperCase()}
                  </div>
                  <span>{e.full_name}</span>
                  <span className="ml-auto text-xs text-muted-foreground">{e.email}</span>
                </CommandItem>
              ))}
            </CommandGroup>
          </>
        )}
      </CommandList>
    </CommandDialog>
  );
}

export function useCommandPalette() {
  const [open, setOpen] = useState(false);
  useEffect(() => {
    function fn(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((o) => !o);
      }
    }
    window.addEventListener("keydown", fn);
    return () => window.removeEventListener("keydown", fn);
  }, []);
  return { open, setOpen };
}
