import { useRef, useState } from "react";
import { useTranslation } from "react-i18next";
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

const CONDITION_TYPE_KEYS: Record<string, string> = {
  day_of_week: "costingRules.conditionTypes.dayOfWeek",
  hours_per_day: "costingRules.conditionTypes.hoursPerDay",
  hours_per_week: "costingRules.conditionTypes.hoursPerWeek",
};

export default function CostingRuleDetailPage() {
  const { id } = useParams<{ id: string }>();
  const tenantId = useCurrentTenantId();
  const ruleId = id ? Number(id) : null;
  const { data: rule, isLoading } = useOvertimeRule(tenantId, ruleId);
  const deactivate = useDeactivateOvertimeRule(tenantId);
  const { t } = useTranslation();
  const [editOpen, setEditOpen] = useState(false);

  if (isLoading)
    return (
      <div className="flex justify-center p-8">
        <Spinner />
      </div>
    );
  if (!rule) return <p className="text-muted-foreground">{t("costingRules.notFound")}</p>;

  return (
    <div className="space-y-4">
      <Link to="/costing-rules" className="text-sm text-muted-foreground hover:underline">
        {t("costingRules.backToList")}
      </Link>

      <Card>
        <CardHeader
          title={rule.name}
          description={t("costingRules.detailDescription", {
            priority: rule.priority,
            multiplier: rule.multiplier,
          })}
          action={
            <div className="flex items-center gap-2">
              <Badge status={rule.is_active ? "active" : "inactive"}>
                {rule.is_active ? t("costingRules.active") : t("costingRules.inactive")}
              </Badge>
              {rule.is_active && (
                <>
                  <Button variant="secondary" onClick={() => setEditOpen(true)}>
                    {t("costingRules.edit")}
                  </Button>
                  <Button
                    variant="danger"
                    onClick={() => deactivate.mutate(rule.id)}
                    disabled={deactivate.isPending}
                  >
                    {deactivate.isPending
                      ? t("costingRules.deactivating")
                      : t("costingRules.deactivate")}
                  </Button>
                </>
              )}
            </div>
          }
        />
        <CardBody>
          <dl className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
            <Field label={t("costingRules.fields.multiplier")} value={`×${rule.multiplier}`} />
            <Field label={t("costingRules.fields.priority")} value={String(rule.priority)} />
            <Field label={t("costingRules.fields.created")} value={formatDate(rule.created_at)} />
            <Field label={t("costingRules.fields.updated")} value={formatDate(rule.updated_at)} />
          </dl>
        </CardBody>
      </Card>

      <Card>
        <CardHeader
          title={t("costingRules.conditions.title")}
          description={t("costingRules.conditions.subtitle")}
        />
        <CardBody className="p-0">
          <Table>
            <thead>
              <tr>
                <Th>{t("costingRules.conditions.columns.type")}</Th>
                <Th>{t("costingRules.conditions.columns.value")}</Th>
              </tr>
            </thead>
            <tbody>
              {rule.conditions.length === 0 && (
                <EmptyRow colSpan={2} message={t("costingRules.conditions.empty")} />
              )}
              {rule.conditions.map((c) => (
                <tr key={c.id}>
                  <Td>
                    {CONDITION_TYPE_KEYS[c.condition_type]
                      ? t(CONDITION_TYPE_KEYS[c.condition_type])
                      : c.condition_type}
                  </Td>
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
      <dt className="text-xs uppercase tracking-wider text-muted-foreground">{label}</dt>
      <dd className="mt-1 font-medium text-foreground">{value}</dd>
    </div>
  );
}

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
  const { t } = useTranslation();
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

  const conditionTypeOptions = [
    { value: "day_of_week", label: t("costingRules.conditionTypes.dayOfWeek") },
    { value: "hours_per_day", label: t("costingRules.conditionTypes.hoursPerDay") },
    { value: "hours_per_week", label: t("costingRules.conditionTypes.hoursPerWeek") },
  ];

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
    <Modal open={open} onClose={onClose} title={t("costingRules.editTitle")}>
      <form onSubmit={onSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div className="col-span-full">
            <Input
              label={t("costingRules.form.name")}
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              required
            />
          </div>
          <Input
            label={t("costingRules.form.multiplier")}
            type="number"
            step="0.01"
            min="1"
            value={form.multiplier}
            onChange={(e) => setForm({ ...form, multiplier: e.target.value })}
            required
          />
          <Input
            label={t("costingRules.form.priority")}
            type="number"
            min="1"
            value={form.priority}
            onChange={(e) => setForm({ ...form, priority: e.target.value })}
            required
          />
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-foreground">
              {t("costingRules.conditions.title")}
            </p>
            <Button type="button" variant="secondary" onClick={addCondition}>
              {t("costingRules.conditions.add")}
            </Button>
          </div>
          {form.conditions.map((c, i) => (
            <div key={c._key} className="grid grid-cols-[1fr_1fr_auto] gap-2 items-end">
              <Select
                label={i === 0 ? t("costingRules.conditions.type") : undefined}
                value={c.condition_type}
                onChange={(e) => setCondition(i, "condition_type", e.target.value)}
              >
                {conditionTypeOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </Select>
              <Input
                label={i === 0 ? t("costingRules.conditions.value") : undefined}
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
            {t("common.cancel")}
          </Button>
          <Button type="submit" disabled={update.isPending}>
            {update.isPending ? t("common.saving") : t("common.save")}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
