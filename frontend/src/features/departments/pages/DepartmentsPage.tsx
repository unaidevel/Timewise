import { useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyRow, Table, Td, Th } from "@/components/ui/Table";
import { useCurrentTenantId } from "@/features/tenants/hooks";
import { formatDate } from "@/lib/format";
import { useCreateDepartment, useDeactivateDepartment, useDepartments } from "../hooks";

export default function DepartmentsPage() {
  const tenantId = useCurrentTenantId();
  const { data, isLoading } = useDepartments(tenantId);
  const [open, setOpen] = useState(false);

  return (
    <Card>
      <CardHeader
        title="Departamentos"
        description="Estructura organizativa de la empresa"
        action={<Button onClick={() => setOpen(true)}>Nuevo departamento</Button>}
      />
      <CardBody className="p-0">
        {isLoading ? (
          <div className="flex justify-center p-8">
            <Spinner />
          </div>
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>Nombre</Th>
                <Th>Estado</Th>
                <Th>Creado</Th>
                <Th></Th>
              </tr>
            </thead>
            <tbody>
              {(!data || data.length === 0) && (
                <EmptyRow colSpan={4} message="Sin departamentos." />
              )}
              {data?.map((d) => (
                <DepartmentRow
                  key={d.id}
                  id={d.id}
                  name={d.name}
                  isActive={d.is_active}
                  createdAt={d.created_at}
                />
              ))}
            </tbody>
          </Table>
        )}
      </CardBody>

      <CreateDepartmentModal open={open} onClose={() => setOpen(false)} />
    </Card>
  );
}

function DepartmentRow({
  id,
  name,
  isActive,
  createdAt,
}: {
  id: number;
  name: string;
  isActive: boolean;
  createdAt: string;
}) {
  const tenantId = useCurrentTenantId();
  const deactivate = useDeactivateDepartment(tenantId);
  return (
    <tr>
      <Td className="font-medium">{name}</Td>
      <Td>
        <Badge status={isActive ? "active" : "inactive"}>{isActive ? "Activo" : "Inactivo"}</Badge>
      </Td>
      <Td>{formatDate(createdAt)}</Td>
      <Td className="text-right">
        {isActive && (
          <Button
            variant="ghost"
            onClick={() => deactivate.mutate(id)}
            disabled={deactivate.isPending}
          >
            Desactivar
          </Button>
        )}
      </Td>
    </tr>
  );
}

function CreateDepartmentModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const tenantId = useCurrentTenantId();
  const create = useCreateDepartment(tenantId);
  const [name, setName] = useState("");

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    create.mutate(
      { name },
      {
        onSuccess: () => {
          setName("");
          onClose();
        },
      },
    );
  }

  return (
    <Modal open={open} onClose={onClose} title="Nuevo departamento">
      <form onSubmit={onSubmit} className="space-y-4">
        <Input label="Nombre" value={name} onChange={(e) => setName(e.target.value)} required />
        <div className="flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" disabled={create.isPending}>
            {create.isPending ? "Creando…" : "Crear"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
