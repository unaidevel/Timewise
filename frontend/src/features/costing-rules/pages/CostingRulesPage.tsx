import { useState } from "react";
import { useTranslation } from "react-i18next";
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
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);

  const active = rules.filter((r) => r.is_active);
  const inactive = rules.filter((r) => !r.is_active);

  return (
    <Card>
      <CardHeader
        title={t("costingRules.title")}
        description={t("costingRules.summary", {
          active: active.length,
          inactive: inactive.length,
        })}
        action={<Button onClick={() => setOpen(true)}>{t("costingRules.new")}</Button>}
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
                <Th>{t("costingRules.columns.name")}</Th>
                <Th>{t("costingRules.columns.multiplier")}</Th>
                <Th>{t("costingRules.columns.priority")}</Th>
                <Th>{t("costingRules.columns.conditions")}</Th>
                <Th>{t("costingRules.columns.status")}</Th>
                <Th></Th>
              </tr>
            </thead>
            <tbody>
              {rules.length === 0 && (
                <EmptyRow colSpan={6} message={t("costingRules.empty")} />
              )}
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
                      {rule.is_active ? t("costingRules.active") : t("costingRules.inactive")}
                    </Badge>
                  </Td>
                  <Td className="text-right">
                    <Link
                      to={`/costing-rules/${rule.id}`}
                      className="text-sm text-muted-foreground hover:underline"
                    >
                      {t("costingRules.view")}
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

function CreateRuleModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const tenantId = useCurrentTenantId();
  const create = useCreateOvertimeRule(tenantId);
  const { t } = useTranslation();
  const [form, setForm] = useState({
    name: "",
    multiplier: "1.5",
    priority: "1",
    conditionType: "hours_per_day",
    conditionValue: "8",
  });

  const conditionTypes = [
    { value: "day_of_week", label: t("costingRules.conditionTypes.dayOfWeek") },
    { value: "hours_per_day", label: t("costingRules.conditionTypes.hoursPerDay") },
    { value: "hours_per_week", label: t("costingRules.conditionTypes.hoursPerWeek") },
  ];

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
    <Modal open={open} onClose={onClose} title={t("costingRules.createTitle")}>
      <form onSubmit={onSubmit} className="grid grid-cols-2 gap-3">
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
        <Select
          label={t("costingRules.form.conditionType")}
          value={form.conditionType}
          onChange={(e) => setForm({ ...form, conditionType: e.target.value })}
        >
          {conditionTypes.map((c) => (
            <option key={c.value} value={c.value}>
              {c.label}
            </option>
          ))}
        </Select>
        <Input
          label={t("costingRules.form.conditionValue")}
          value={form.conditionValue}
          onChange={(e) => setForm({ ...form, conditionValue: e.target.value })}
          required
        />
        <div className="col-span-full flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            {t("common.cancel")}
          </Button>
          <Button type="submit" disabled={create.isPending}>
            {create.isPending ? t("common.creating") : t("common.create")}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
