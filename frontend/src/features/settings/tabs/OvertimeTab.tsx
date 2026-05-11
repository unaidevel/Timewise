import { Save, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/shadcn/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/shadcn/card";
import { Input } from "@/components/shadcn/input";
import { Label } from "@/components/shadcn/label";
import {
  DEFAULT_OT,
  getOvertimeConfig,
  type OvertimeConfig,
  setOvertimeConfig,
} from "@/features/settings/local-store";

export function OvertimeTab({ tenantId }: { tenantId: number }) {
  const [cfg, setCfg] = useState<OvertimeConfig>(() => getOvertimeConfig(tenantId));
  const [saving, setSaving] = useState(false);

  useEffect(() => setCfg(getOvertimeConfig(tenantId)), [tenantId]);

  function save() {
    setSaving(true);
    setOvertimeConfig(tenantId, cfg);
    toast.success("Reglas de horas extra actualizadas");
    setSaving(false);
  }

  const preview = computePreview(cfg);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Reglas de horas extra</CardTitle>
        <CardDescription>
          Las horas por encima de los umbrales se pagan al multiplicador configurado al calcular
          costes.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6 max-w-2xl">
        <div className="grid sm:grid-cols-2 gap-4">
          <Field label="Umbral semanal (horas)">
            <Input
              type="number"
              min={0}
              value={cfg.weekly_threshold}
              onChange={(e) => setCfg({ ...cfg, weekly_threshold: Number(e.target.value) })}
            />
          </Field>
          <Field label="Multiplicador semanal">
            <Input
              type="number"
              step="0.05"
              min={1}
              value={cfg.multiplier}
              onChange={(e) => setCfg({ ...cfg, multiplier: Number(e.target.value) })}
            />
          </Field>
          <Field label="Umbral diario (horas)">
            <Input
              type="number"
              min={0}
              value={cfg.daily_threshold}
              onChange={(e) => setCfg({ ...cfg, daily_threshold: Number(e.target.value) })}
            />
          </Field>
          <Field label="Multiplicador diario">
            <Input
              type="number"
              step="0.05"
              min={1}
              value={cfg.daily_multiplier}
              onChange={(e) => setCfg({ ...cfg, daily_multiplier: Number(e.target.value) })}
            />
          </Field>
        </div>

        <div className="rounded-lg bg-muted/40 border border-dashed p-4">
          <div className="flex items-start gap-3">
            <div className="size-8 rounded-md bg-primary/10 text-primary grid place-items-center shrink-0">
              <Sparkles className="size-4" />
            </div>
            <div className="text-sm">
              <div className="font-medium">Vista previa de coste</div>
              <p className="text-muted-foreground mt-1">
                Un empleado a 50 €/h trabajando 50 horas en una semana (con una jornada de 10 horas)
                costaría <span className="font-mono text-foreground">{preview.toFixed(0)} €</span>{" "}
                con estas reglas.
              </p>
            </div>
          </div>
        </div>

        <div className="flex gap-2 pt-1">
          <Button onClick={save} disabled={saving}>
            <Save className="size-4 mr-2" />
            {saving ? "Guardando…" : "Guardar reglas"}
          </Button>
          <Button variant="outline" onClick={() => setCfg(DEFAULT_OT)}>
            Restablecer
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function computePreview(cfg: OvertimeConfig) {
  const rate = 50;
  const totalHours = 50;
  const longDay = 10;
  const dailyOt = Math.max(0, longDay - cfg.daily_threshold);
  const weeklyOt = Math.max(0, totalHours - cfg.weekly_threshold - dailyOt);
  const regHours = totalHours - dailyOt - weeklyOt;
  return regHours * rate + dailyOt * rate * cfg.daily_multiplier + weeklyOt * rate * cfg.multiplier;
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <Label className="text-xs">{label}</Label>
      {children}
    </div>
  );
}
