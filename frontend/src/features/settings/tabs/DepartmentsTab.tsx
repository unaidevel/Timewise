import { Plus, Trash2 } from "lucide-react";
import { useMemo, useState } from "react";
import { toast } from "sonner";
import type { DepartmentOut } from "@/client";
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
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/shadcn/dialog";
import { Input } from "@/components/shadcn/input";
import { Label } from "@/components/shadcn/label";
import {
  useCreateDepartment,
  useDeactivateDepartment,
  useDepartments,
  useUpdateDepartment,
} from "@/features/departments/hooks";
import { useEmployees } from "@/features/employees/hooks";
import {
  COLOR_PALETTE,
  colorForDepartment,
  setDepartmentColor,
  useDepartmentColors,
} from "@/features/settings/local-store";

export function DepartmentsTab({ tenantId }: { tenantId: number }) {
  const departments = useDepartments(tenantId);
  const employees = useEmployees(tenantId);
  const colors = useDepartmentColors(tenantId);
  const [openCreate, setOpenCreate] = useState(false);
  const [editing, setEditing] = useState<DepartmentOut | null>(null);

  const create = useCreateDepartment(tenantId);
  const update = useUpdateDepartment(tenantId);
  const deactivate = useDeactivateDepartment(tenantId);

  const counts = useMemo(() => {
    const m: Record<number, number> = {};
    for (const e of employees.data ?? []) {
      // We don't have department_id on EmployeeOut directly, so we can't compute reliable counts
      // without an extra request per employee. Show 0 when unknown.
      void e;
    }
    return m;
  }, [employees.data]);

  function handleCreate(name: string, color: string) {
    create.mutate(
      { name },
      {
        onSuccess: (dept) => {
          if (dept) setDepartmentColor(tenantId, dept.id, color);
          toast.success("Departamento creado");
          setOpenCreate(false);
        },
      },
    );
  }

  function handleEdit(name: string, color: string) {
    if (!editing) return;
    const id = editing.id;
    const promises: Promise<unknown>[] = [];
    if (name !== editing.name) {
      promises.push(
        new Promise((resolve, reject) =>
          update.mutate({ id, body: { name } }, { onSuccess: resolve, onError: reject }),
        ),
      );
    }
    setDepartmentColor(tenantId, id, color);
    Promise.all(promises)
      .then(() => {
        toast.success("Departamento actualizado");
        setEditing(null);
      })
      .catch(() => toast.error("No se pudo actualizar"));
  }

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <div>
          <CardTitle className="text-base">Departamentos</CardTitle>
          <CardDescription>Agrupa empleados para reportes y asignación de costes.</CardDescription>
        </div>
        <Dialog open={openCreate} onOpenChange={setOpenCreate}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="size-4 mr-1.5" />
              Nuevo departamento
            </Button>
          </DialogTrigger>
          <DepartmentDialog
            title="Crear departamento"
            onSubmit={handleCreate}
            pending={create.isPending}
          />
        </Dialog>
      </CardHeader>
      <CardContent className="p-0">
        <div className="divide-y">
          {(departments.data ?? []).map((d) => (
            <div key={d.id} className="flex items-center gap-4 px-6 py-3.5">
              <span
                className="size-3 rounded-full shrink-0"
                style={{ background: colorForDepartment(colors, d.id) }}
              />
              <div className="flex-1 min-w-0">
                <div className="font-medium truncate">{d.name}</div>
                <div className="text-xs text-muted-foreground">
                  {(counts[d.id] ?? 0) === 1 ? "1 persona" : `${counts[d.id] ?? 0} personas`}
                </div>
              </div>
              {d.is_active ? (
                <>
                  <Button variant="ghost" size="sm" onClick={() => setEditing(d)}>
                    Editar
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => {
                      if (window.confirm(`¿Desactivar ${d.name}?`)) deactivate.mutate(d.id);
                    }}
                    className="text-muted-foreground hover:text-destructive"
                  >
                    <Trash2 className="size-4" />
                  </Button>
                </>
              ) : (
                <span className="text-xs text-muted-foreground">Inactivo</span>
              )}
            </div>
          ))}
          {(departments.data?.length ?? 0) === 0 && (
            <div className="p-12 text-center text-sm text-muted-foreground">
              Aún no hay departamentos. Crea el primero para empezar.
            </div>
          )}
        </div>
      </CardContent>

      <Dialog open={!!editing} onOpenChange={(o) => !o && setEditing(null)}>
        {editing && (
          <DepartmentDialog
            title="Editar departamento"
            initialName={editing.name}
            initialColor={colorForDepartment(colors, editing.id)}
            onSubmit={handleEdit}
            pending={update.isPending}
          />
        )}
      </Dialog>
    </Card>
  );
}

function DepartmentDialog({
  title,
  initialName = "",
  initialColor = COLOR_PALETTE[0],
  onSubmit,
  pending,
}: {
  title: string;
  initialName?: string;
  initialColor?: string;
  onSubmit: (name: string, color: string) => void;
  pending: boolean;
}) {
  const [name, setName] = useState(initialName);
  const [color, setColor] = useState(initialColor);
  return (
    <DialogContent>
      <DialogHeader>
        <DialogTitle>{title}</DialogTitle>
      </DialogHeader>
      <div className="space-y-4">
        <div className="space-y-1.5">
          <Label className="text-xs">Nombre</Label>
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="p. ej. Ingeniería"
          />
        </div>
        <div className="space-y-1.5">
          <Label className="text-xs">Color</Label>
          <div className="flex flex-wrap gap-2">
            {COLOR_PALETTE.map((c) => (
              <button
                key={c}
                type="button"
                onClick={() => setColor(c)}
                className={`size-8 rounded-md border-2 transition ${
                  color === c ? "border-foreground" : "border-transparent"
                }`}
                style={{ background: c }}
                aria-label={`Color ${c}`}
              />
            ))}
          </div>
        </div>
      </div>
      <div className="flex justify-end gap-2 pt-2">
        <Button onClick={() => onSubmit(name.trim(), color)} disabled={!name.trim() || pending}>
          {pending ? "Guardando…" : "Guardar"}
        </Button>
      </div>
    </DialogContent>
  );
}
