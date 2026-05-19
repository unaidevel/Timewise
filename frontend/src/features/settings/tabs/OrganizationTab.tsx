import { Save } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/shadcn/select";
import {
  DEFAULT_ORG,
  getOrgProfile,
  type OrgProfile,
  setOrgProfile,
} from "@/features/settings/local-store";

const CURRENCIES = ["EUR", "USD", "GBP", "JPY", "CAD", "AUD"];

export function OrganizationTab({ tenantId }: { tenantId: number }) {
  const [profile, setProfile] = useState<OrgProfile>(() => getOrgProfile(tenantId));
  const [saving, setSaving] = useState(false);
  const { t } = useTranslation();

  useEffect(() => setProfile(getOrgProfile(tenantId)), [tenantId]);

  const upd = <K extends keyof OrgProfile>(k: K, v: OrgProfile[K]) =>
    setProfile((p) => ({ ...p, [k]: v }));

  function save() {
    setSaving(true);
    setOrgProfile(tenantId, profile);
    toast.success(t("settings.org.updated"));
    setSaving(false);
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{t("settings.org.title")}</CardTitle>
        <CardDescription>{t("settings.org.subtitle")}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-5 max-w-2xl">
        <div className="grid sm:grid-cols-2 gap-4">
          <Field label={t("settings.org.fields.name")}>
            <Input value={profile.name} onChange={(e) => upd("name", e.target.value)} />
          </Field>
          <Field label={t("settings.org.fields.legalName")}>
            <Input value={profile.legal_name} onChange={(e) => upd("legal_name", e.target.value)} />
          </Field>
        </div>
        <div className="grid sm:grid-cols-2 gap-4">
          <Field label={t("settings.org.fields.country")}>
            <Input value={profile.country} onChange={(e) => upd("country", e.target.value)} />
          </Field>
          <Field label={t("settings.org.fields.timezone")}>
            <Input value={profile.timezone} onChange={(e) => upd("timezone", e.target.value)} />
          </Field>
        </div>
        <div className="grid sm:grid-cols-2 gap-4">
          <Field label={t("settings.org.fields.currency")}>
            <Select value={profile.currency} onValueChange={(v) => upd("currency", v)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {CURRENCIES.map((c) => (
                  <SelectItem key={c} value={c}>
                    {c}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </Field>
          <Field label={t("settings.org.fields.fiscalYear")}>
            <Input
              value={profile.fiscal_year_start}
              onChange={(e) => upd("fiscal_year_start", e.target.value)}
              placeholder="01-01"
            />
          </Field>
        </div>
        <div className="flex gap-2 pt-2">
          <Button onClick={save} disabled={saving}>
            <Save className="size-4 mr-2" />
            {saving ? t("settings.org.saving") : t("settings.org.save")}
          </Button>
          <Button variant="outline" onClick={() => setProfile(DEFAULT_ORG)}>
            {t("settings.org.reset")}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <Label className="text-xs">{label}</Label>
      {children}
    </div>
  );
}
