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

const pages = [
  { to: "/", label: "Inicio", icon: LayoutDashboard },
  { to: "/employees", label: "Empleados", icon: Users },
  { to: "/departments", label: "Departamentos", icon: FolderKanban },
  { to: "/roles", label: "Roles", icon: Tag },
  { to: "/periods", label: "Periodos", icon: Clock },
  { to: "/reports", label: "Reportes", icon: Clock },
  { to: "/approvals", label: "Aprobaciones", icon: CheckSquare },
  { to: "/costing-rules", label: "Reglas de coste", icon: Calculator },
] as const;

export function CommandPalette({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const navigate = useNavigate();
  const tenantId = useCurrentTenantId();
  const employees = useEmployees(open ? tenantId : null);

  const peopleItems = useMemo(() => (employees.data ?? []).slice(0, 8), [employees.data]);

  const go = (to: string) => {
    onOpenChange(false);
    navigate(to);
  };

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange}>
      <CommandInput placeholder="Busca personas, páginas, acciones…" />
      <CommandList>
        <CommandEmpty>No hay resultados.</CommandEmpty>
        <CommandGroup heading="Navegar">
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
            <CommandGroup heading="Empleados">
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
