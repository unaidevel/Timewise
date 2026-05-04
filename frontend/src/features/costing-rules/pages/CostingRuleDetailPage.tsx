import { useRef, useState } from "react";
import { Link, useParams } from "react-router";
import type { OvertimeRuleUpdate, RuleConditionIn, RuleConditionOut } from "@/client";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Input, Select } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyRow, Table, Td, Th } from "@/components/ui/Table";
import { useCurrentTenantId } from "@/features/tenants/hooks";
import { formatDate } from "@/lib/format";
import { useDeactivateOvertimeRule, useOvertimeRule, useUpdateOvertimeRule } from "../hooks";

const CONDITION_TYPES: Record<string, string> = {
  day_of_week: "Día de la semana",
  hours_per_day: "Horas por día",
  hours_per_week: "Horas por semana",
};

export default function CostingRuleDetailPage() {
  const { id } = useParams<{ id: string }>();
  const tenantId = useCurrentTenantId();
  const ruleId = id ? Number(id) : null;
  const { data: rule, isLoading } = useOvertimeRule(tenantId, ruleId);
  const deactivate = useDeactivateOvertimeRule(tenantId);
  const [editOpen, setEditOpen] = useState(false);

  if (isLoading)
    return (
      <div className="flex justify-center p-8">
        <Spinner />
      </div>
    );
  if (!rule) return <p className="text-slate-600">Regla no encontrada.</p>;

  return (
    <div className="space-y-4">
      <Link to="/costing-rules" className="text-sm text-slate-600 hover:underline">
        ← Volver a reglas
      </Link>

      <Card>
        <CardHeader
          title={rule.name}
          description={`Prioridad ${rule.priority} · Multiplicador ×${rule.multiplier}`}
          action={
            <div className="flex items-center gap-2">
              <Badge status={rule.is_active ? "active" : "inactive"}>
                {rule.is_active ? "Activa" : "Inactiva"}
              </Badge>
              {rule.is_active && (
                <>
                  <Button variant="secondary" onClick={() => setEditOpen(true)}>
                    Editar
                  </Button>
                  <Button
                    variant="danger"
                    onClick={() => deactivate.mutate(rule.id)}
                    disabled={deactivate.isPending}
                  >
                    {deactivate.isPending ? "Desactivando…" : "Desactivar"}
                  </Button>
                </>
              )}
            </div>
          }
        />
        <CardBody>
          <dl className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
            <Field label="Multiplicador" value={`×${rule.multiplier}`} />
            <Field label="Prioridad" value={String(rule.priority)} />
            <Field label="Creado" value={formatDate(rule.created_at)} />
            <Field label="Actualizado" value={formatDate(rule.updated_at)} />
          </dl>
        </CardBody>
      </Card>

      <Card>
        <CardHeader
          title="Condiciones"
          description="La regla se aplica cuando se cumplen todas las condiciones"
        />
        <CardBody className="p-0">
          <Table>
            <thead>
              <tr>
                <Th>Tipo</Th>
                <Th>Valor</Th>
              </tr>
            </thead>
            <tbody>
              {rule.conditions.length === 0 && <EmptyRow colSpan={2} message="Sin condiciones." />}
              {rule.conditions.map((c) => (
                <tr key={c.id}>
                  <Td>{CONDITION_TYPES[c.condition_type] ?? c.condition_type}</Td>
                  <Td className="font-medium">{c.value}</Td>
                </tr>
              ))}
            </tbody>
          </Table>
        </CardBody>
      </Card>

      {editOpen && (
        <EditRuleModal
          open={editOpen}
          onClose={() => setEditOpen(false)}
          rule={{
            name: rule.name,
            multiplier: rule.multiplier,
            priority: rule.priority,
            conditions: rule.conditions,
          }}
          ruleId={rule.id}
        />
      )}
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wider text-slate-500">{label}</dt>
      <dd className="mt-1 font-medium text-slate-900">{value}</dd>
    </div>
  );
}

const CONDITION_TYPE_OPTIONS = [
  { value: "day_of_week", label: "Día de la semana" },
  { value: "hours_per_day", label: "Horas por día" },
  { value: "hours_per_week", label: "Horas por semana" },
];

function EditRuleModal({
  open,
  onClose,
  rule,
  ruleId,
}: {
  open: boolean;
  onClose: () => void;
  rule: {
    name: string;
    multiplier: string;
    priority: number;
    conditions: (RuleConditionIn | RuleConditionOut)[];
  };
  ruleId: number;
}) {
  const tenantId = useCurrentTenantId();
  const update = useUpdateOvertimeRule(tenantId);
  const keyCounter = useRef(0);
  const nextKey = () => (keyCounter.current += 1);
  const [form, setForm] = useState({
    name: rule.name,
    multiplier: String(rule.multiplier),
    priority: String(rule.priority),
    conditions: rule.conditions.map((c) => ({
      _key: nextKey(),
      condition_type: c.condition_type,
      value: c.value,
    })),
  });

  function setCondition(index: number, field: keyof RuleConditionIn, value: string) {
    const updated = form.conditions.map((c, i) => (i === index ? { ...c, [field]: value } : c));
    setForm({ ...form, conditions: updated });
  }

  function addCondition() {
    setForm({
      ...form,
      conditions: [
        ...form.conditions,
        { _key: nextKey(), condition_type: "hours_per_day", value: "8" },
      ],
    });
  }

  function removeCondition(index: number) {
    setForm({ ...form, conditions: form.conditions.filter((_, i) => i !== index) });
  }

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const body: OvertimeRuleUpdate = {
      name: form.name,
      multiplier: form.multiplier,
      priority: Number(form.priority),
      conditions: form.conditions.map(({ _key: _, ...rest }) => rest),
    };
    update.mutate({ id: ruleId, body }, { onSuccess: () => onClose() });
  }

  return (
    <Modal open={open} onClose={onClose} title="Editar regla">
      <form onSubmit={onSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
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
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-slate-700">Condiciones</p>
            <Button type="button" variant="secondary" onClick={addCondition}>
              + Añadir
            </Button>
          </div>
          {form.conditions.map((c, i) => (
            <div key={c._key} className="grid grid-cols-[1fr_1fr_auto] gap-2 items-end">
              <Select
                label={i === 0 ? "Tipo" : undefined}
                value={c.condition_type}
                onChange={(e) => setCondition(i, "condition_type", e.target.value)}
              >
                {CONDITION_TYPE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </Select>
              <Input
                label={i === 0 ? "Valor" : undefined}
                value={c.value}
                onChange={(e) => setCondition(i, "value", e.target.value)}
                required
              />
              <Button
                type="button"
                variant="ghost"
                onClick={() => removeCondition(i)}
                className="mb-0.5"
              >
                ×
              </Button>
            </div>
          ))}
        </div>

        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" disabled={update.isPending}>
            {update.isPending ? "Guardando…" : "Guardar"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
