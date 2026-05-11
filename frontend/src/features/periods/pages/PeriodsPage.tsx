import { useState } from "react";
import { Link } from "react-router";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyRow, Table, Td, Th } from "@/components/ui/Table";
import { useCurrentTenantId } from "@/features/tenants/hooks";
import { formatDate } from "@/lib/format";
import { useCreatePeriod, useLockPeriod, usePeriods } from "../hooks";

export default function PeriodsPage() {
  const tenantId = useCurrentTenantId();
  const { data, isLoading } = usePeriods(tenantId);
  const [open, setOpen] = useState(false);

  return (
    <Card>
      <CardHeader
        title="Periodos"
        description="Ventanas temporales de imputación de horas"
        action={<Button onClick={() => setOpen(true)}>Nuevo periodo</Button>}
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
                <Th>Inicio</Th>
                <Th>Fin</Th>
                <Th>Estado</Th>
                <Th>Bloqueado</Th>
                <Th></Th>
              </tr>
            </thead>
            <tbody>
              {(!data || data.length === 0) && <EmptyRow colSpan={6} message="Sin periodos." />}
              {data?.map((p) => (
                <PeriodRow key={p.id} period={p} />
              ))}
            </tbody>
          </Table>
        )}
      </CardBody>

      <CreatePeriodModal open={open} onClose={() => setOpen(false)} />
    </Card>
  );
}

function PeriodRow({ period }: { period: import("@/client").PeriodOut }) {
  const tenantId = useCurrentTenantId();
  const lock = useLockPeriod(tenantId);
  return (
    <tr>
      <Td className="font-medium">
        <Link to={`/periods/${period.id}`} className="hover:underline">
          {period.name}
        </Link>
      </Td>
      <Td>{formatDate(period.start_date)}</Td>
      <Td>{formatDate(period.end_date)}</Td>
      <Td>
        <Badge status={period.status}>{period.status}</Badge>
      </Td>
      <Td>{formatDate(period.locked_at)}</Td>
      <Td className="text-right">
        {!period.locked_at && (
          <Button variant="ghost" onClick={() => lock.mutate(period.id)} disabled={lock.isPending}>
            Bloquear
          </Button>
        )}
      </Td>
    </tr>
  );
}

function CreatePeriodModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const tenantId = useCurrentTenantId();
  const create = useCreatePeriod(tenantId);
  const [form, setForm] = useState({ name: "", start_date: "", end_date: "" });

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    create.mutate(form, { onSuccess: () => onClose() });
  }

  return (
    <Modal open={open} onClose={onClose} title="Nuevo periodo">
      <form onSubmit={onSubmit} className="space-y-3">
        <Input
          label="Nombre"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          required
        />
        <div className="grid grid-cols-2 gap-3">
          <Input
            label="Inicio"
            type="date"
            value={form.start_date}
            onChange={(e) => setForm({ ...form, start_date: e.target.value })}
            required
          />
          <Input
            label="Fin"
            type="date"
            value={form.end_date}
            onChange={(e) => setForm({ ...form, end_date: e.target.value })}
            required
          />
        </div>
        <div className="flex justify-end gap-2 pt-2">
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
