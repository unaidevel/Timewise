import { useState } from "react";
import { Link } from "react-router";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Input, Select } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyRow, Table, Td, Th } from "@/components/ui/Table";
import { useDepartments } from "@/features/departments/hooks";
import { useRoles } from "@/features/roles/hooks";
import { useCurrentTenantId } from "@/features/tenants/hooks";
import { formatDate } from "@/lib/format";
import { useCreateEmployee, useDeactivateEmployee, useEmployees } from "../hooks";

export default function EmployeesPage() {
  const tenantId = useCurrentTenantId();
  const { data, isLoading } = useEmployees(tenantId);
  const [open, setOpen] = useState(false);

  return (
    <Card>
      <CardHeader
        title="Empleados"
        description="Plantilla de la empresa"
        action={<Button onClick={() => setOpen(true)}>Nuevo empleado</Button>}
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
                <Th>Email</Th>
                <Th>Contratado</Th>
                <Th>Estado</Th>
                <Th></Th>
              </tr>
            </thead>
            <tbody>
              {(!data || data.length === 0) && <EmptyRow colSpan={5} message="Sin empleados." />}
              {data?.map((e) => (
                <EmployeeRow key={e.id} employee={e} />
              ))}
            </tbody>
          </Table>
        )}
      </CardBody>

      <CreateEmployeeModal open={open} onClose={() => setOpen(false)} />
    </Card>
  );
}

function EmployeeRow({ employee }: { employee: import("@/client").EmployeeOut }) {
  const tenantId = useCurrentTenantId();
  const deactivate = useDeactivateEmployee(tenantId);
  return (
    <tr>
      <Td className="font-medium">
        <Link to={`/employees/${employee.id}`} className="hover:underline">
          {employee.full_name}
        </Link>
      </Td>
      <Td className="text-slate-600">{employee.email}</Td>
      <Td>{formatDate(employee.hired_at)}</Td>
      <Td>
        <Badge status={employee.is_active ? "active" : "inactive"}>
          {employee.is_active ? "Activo" : "Inactivo"}
        </Badge>
      </Td>
      <Td className="text-right">
        {employee.is_active && (
          <Button
            variant="ghost"
            onClick={() => deactivate.mutate(employee.id)}
            disabled={deactivate.isPending}
          >
            Desactivar
          </Button>
        )}
      </Td>
    </tr>
  );
}

function CreateEmployeeModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const tenantId = useCurrentTenantId();
  const { data: departments = [] } = useDepartments(tenantId);
  const { data: roles = [] } = useRoles(tenantId);
  const create = useCreateEmployee(tenantId);

  const [form, setForm] = useState({
    full_name: "",
    email: "",
    department_id: "",
    role_id: "",
    hourly_rate: "",
    contract_hours_per_week: "40",
    hired_at: new Date().toISOString().slice(0, 10),
  });

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
      { onSuccess: () => onClose() },
    );
  }

  return (
    <Modal open={open} onClose={onClose} title="Nuevo empleado">
      <form onSubmit={onSubmit} className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <Input
          label="Nombre completo"
          value={form.full_name}
          onChange={(e) => setForm({ ...form, full_name: e.target.value })}
          required
        />
        <Input
          label="Email"
          type="email"
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          required
        />
        <Select
          label="Departamento"
          value={form.department_id}
          onChange={(e) => setForm({ ...form, department_id: e.target.value })}
          required
        >
          <option value="">— Selecciona —</option>
          {departments
            .filter((d) => d.is_active)
            .map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
        </Select>
        <Select
          label="Rol"
          value={form.role_id}
          onChange={(e) => setForm({ ...form, role_id: e.target.value })}
          required
        >
          <option value="">— Selecciona —</option>
          {roles
            .filter((r) => r.is_active)
            .map((r) => (
              <option key={r.id} value={r.id}>
                {r.name}
              </option>
            ))}
        </Select>
        <Input
          label="Tarifa por hora (€)"
          type="number"
          step="0.01"
          value={form.hourly_rate}
          onChange={(e) => setForm({ ...form, hourly_rate: e.target.value })}
          required
        />
        <Input
          label="Horas contrato/semana"
          type="number"
          value={form.contract_hours_per_week}
          onChange={(e) => setForm({ ...form, contract_hours_per_week: e.target.value })}
          required
        />
        <Input
          label="Fecha de contratación"
          type="date"
          value={form.hired_at}
          onChange={(e) => setForm({ ...form, hired_at: e.target.value })}
          required
        />
        <div className="col-span-full flex justify-end gap-2 pt-2">
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
