import { useState } from "react";
import { Link } from "react-router";
import type { OvertimeRuleIn } from "@/client";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Input, Select } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyRow, Table, Td, Th } from "@/components/ui/Table";
import { useCurrentTenantId } from "@/features/tenants/hooks";
import { useCreateOvertimeRule, useOvertimeRules } from "../hooks";

export default function CostingRulesPage() {
  const tenantId = useCurrentTenantId();
  const { data: rules = [], isLoading } = useOvertimeRules(tenantId);
  const [open, setOpen] = useState(false);

  const active = rules.filter((r) => r.is_active);
  const inactive = rules.filter((r) => !r.is_active);

  return (
    <Card>
      <CardHeader
        title="Reglas de coste"
        description={`${active.length} activa${active.length !== 1 ? "s" : ""} · ${inactive.length} inactiva${inactive.length !== 1 ? "s" : ""}`}
        action={<Button onClick={() => setOpen(true)}>Nueva regla</Button>}
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
                <Th>Multiplicador</Th>
                <Th>Prioridad</Th>
                <Th>Condiciones</Th>
                <Th>Estado</Th>
                <Th></Th>
              </tr>
            </thead>
            <tbody>
              {rules.length === 0 && <EmptyRow colSpan={6} message="Sin reglas de coste." />}
              {rules.map((rule) => (
                <tr key={rule.id}>
                  <Td className="font-medium">
                    <Link to={`/costing-rules/${rule.id}`} className="hover:underline">
                      {rule.name}
                    </Link>
                  </Td>
                  <Td>×{rule.multiplier}</Td>
                  <Td>{rule.priority}</Td>
                  <Td>{rule.conditions.length}</Td>
                  <Td>
                    <Badge status={rule.is_active ? "active" : "inactive"}>
                      {rule.is_active ? "Activa" : "Inactiva"}
                    </Badge>
                  </Td>
                  <Td className="text-right">
                    <Link
                      to={`/costing-rules/${rule.id}`}
                      className="text-sm text-muted-foreground hover:underline"
                    >
                      Ver →
                    </Link>
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </CardBody>

      <CreateRuleModal open={open} onClose={() => setOpen(false)} />
    </Card>
  );
}

const CONDITION_TYPES = [
  { value: "day_of_week", label: "Día de la semana" },
  { value: "hours_per_day", label: "Horas por día" },
  { value: "hours_per_week", label: "Horas por semana" },
];

function CreateRuleModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const tenantId = useCurrentTenantId();
  const create = useCreateOvertimeRule(tenantId);
  const [form, setForm] = useState({
    name: "",
    multiplier: "1.5",
    priority: "1",
    conditionType: "hours_per_day",
    conditionValue: "8",
  });

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const body: OvertimeRuleIn = {
      name: form.name,
      multiplier: form.multiplier,
      priority: Number(form.priority),
      conditions: [
        {
          condition_type: form.conditionType,
          value: form.conditionValue,
        },
      ],
    };
    create.mutate(body, {
      onSuccess: () => {
        onClose();
        resetForm();
      },
    });
  }

  function resetForm() {
    setForm({
      name: "",
      multiplier: "1.5",
      priority: "1",
      conditionType: "hours_per_day",
      conditionValue: "8",
    });
  }

  return (
    <Modal open={open} onClose={onClose} title="Nueva regla de coste">
      <form onSubmit={onSubmit} className="grid grid-cols-2 gap-3">
        <div className="col-span-full">
          <Input
            label="Nombre"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            required
          />
        </div>
        <Input
          label="Multiplicador"
          type="number"
          step="0.01"
          min="1"
          value={form.multiplier}
          onChange={(e) => setForm({ ...form, multiplier: e.target.value })}
          required
        />
        <Input
          label="Prioridad"
          type="number"
          min="1"
          value={form.priority}
          onChange={(e) => setForm({ ...form, priority: e.target.value })}
          required
        />
        <Select
          label="Tipo de condición"
          value={form.conditionType}
          onChange={(e) => setForm({ ...form, conditionType: e.target.value })}
        >
          {CONDITION_TYPES.map((c) => (
            <option key={c.value} value={c.value}>
              {c.label}
            </option>
          ))}
        </Select>
        <Input
          label="Valor de condición"
          value={form.conditionValue}
          onChange={(e) => setForm({ ...form, conditionValue: e.target.value })}
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
