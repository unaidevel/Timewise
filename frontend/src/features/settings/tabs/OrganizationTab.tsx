import { Save } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";
import type { OrganizationProfileIn, OrganizationProfileOut, TimezoneOption } from "@/client";
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
  useIsTenantAdmin,
  useOrganizationProfile,
  useTimezones,
  useUpdateOrganizationProfile,
} from "@/features/tenants/hooks";

const CURRENCIES = ["EUR", "USD", "GBP", "JPY", "CAD", "AUD"];

type FormState = Required<OrganizationProfileIn>;

function toFormState(profile: OrganizationProfileOut): FormState {
  return {
    public_name: profile.public_name ?? "",
    legal_name: profile.legal_name ?? "",
    country: profile.country ?? "",
    timezone: profile.timezone ?? "UTC",
    currency: profile.currency ?? "EUR",
    vat_number: profile.vat_number ?? "",
  };
}

export function OrganizationTab({ tenantId }: { tenantId: number }) {
  const { t } = useTranslation();
  const profile = useOrganizationProfile(tenantId);
  const timezones = useTimezones();
  if (timezones.error) console.error("Failed to load timezones", timezones.error);
  const update = useUpdateOrganizationProfile(tenantId);
  const canEdit = useIsTenantAdmin(tenantId);

  const [form, setForm] = useState<FormState | null>(null);

  useEffect(() => {
    if (profile.data) setForm(toFormState(profile.data));
  }, [profile.data]);

  useEffect(() => {
    if (profile.error) toast.error(t("settings.org.loadError"));
  }, [profile.error, t]);

  const upd = <K extends keyof FormState>(k: K, v: FormState[K]) =>
    setForm((p) => (p ? { ...p, [k]: v } : p));

  async function save() {
    if (!form) return;
    try {
      await update.mutateAsync(form);
      toast.success(t("settings.org.updated"));
    } catch {
      toast.error(t("settings.org.saveError"));
    }
  }

  if (profile.isPending || !form) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{t("settings.org.title")}</CardTitle>
          <CardDescription>{t("settings.org.subtitle")}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-32 animate-pulse rounded-md bg-muted/40" />
        </CardContent>
      </Card>
    );
  }

  const disabled = !canEdit || update.isPending;
  const isDirty = profile.data
    ? (Object.keys(form) as (keyof FormState)[]).some(
        (k) => form[k] !== toFormState(profile.data!)[k],
      )
    : false;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{t("settings.org.title")}</CardTitle>
        <CardDescription>{t("settings.org.subtitle")}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        {!canEdit && <p className="text-xs text-muted-foreground">{t("settings.org.readOnly")}</p>}
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <Field label={t("settings.org.fields.publicName")}>
            <Input
              value={form.public_name}
              disabled={disabled}
              onChange={(e) => upd("public_name", e.target.value)}
            />
          </Field>
          <Field label={t("settings.org.fields.legalName")}>
            <Input
              value={form.legal_name}
              disabled={disabled}
              onChange={(e) => upd("legal_name", e.target.value)}
            />
          </Field>
          <Field label={t("settings.org.fields.country")}>
            <Input
              value={form.country}
              disabled={disabled}
              maxLength={2}
              placeholder="ES"
              onChange={(e) => upd("country", e.target.value.toUpperCase())}
            />
          </Field>
          <Field label={t("settings.org.fields.timezone")}>
            <TimezoneSelect
              value={form.timezone}
              disabled={disabled}
              loading={timezones.isPending}
              options={timezones.data ?? []}
              onChange={(v) => upd("timezone", v)}
            />
          </Field>
          <Field label={t("settings.org.fields.currency")}>
            <Select
              value={form.currency}
              disabled={disabled}
              onValueChange={(v) => upd("currency", v)}
            >
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
          <Field label={t("settings.org.fields.vatNumber")}>
            <Input
              value={form.vat_number}
              disabled={disabled}
              onChange={(e) => upd("vat_number", e.target.value)}
            />
          </Field>
        </div>
        <div className="flex gap-2 pt-2">
          <Button onClick={save} disabled={disabled || !isDirty}>
            <Save className="size-4 mr-2" />
            {update.isPending ? t("settings.org.saving") : t("settings.org.save")}
          </Button>
          <Button
            variant="outline"
            disabled={disabled || !isDirty}
            onClick={() => profile.data && setForm(toFormState(profile.data))}
          >
            {t("settings.org.reset")}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function TimezoneSelect({
  value,
  disabled,
  loading,
  options,
  onChange,
}: {
  value: string;
  disabled: boolean;
  loading: boolean;
  options: TimezoneOption[];
  onChange: (value: string) => void;
}) {
  const now = useLiveNow();
  const items = useMemo(() => {
    if (value && !options.some((o) => o.value === value)) {
      return [{ value, label: value }, ...options];
    }
    return options;
  }, [options, value]);

  return (
    <Select value={value} disabled={disabled} onValueChange={onChange}>
      <SelectTrigger>
        <SelectValue placeholder={loading ? "Loading…" : value || "UTC"} />
      </SelectTrigger>
      <SelectContent>
        {items.map((opt) => (
          <SelectItem key={opt.value} value={opt.value}>
            <span>{opt.label}</span>
            <span className="ml-2 text-xs text-muted-foreground tabular-nums">
              {formatTimeIn(opt.value, now)}
            </span>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

function formatTimeIn(timezone: string, date: Date): string {
  try {
    return new Intl.DateTimeFormat(undefined, {
      timeZone: timezone,
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    }).format(date);
  } catch {
    return "--:--";
  }
}

function useLiveNow(): Date {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const id = window.setInterval(() => setNow(new Date()), 30_000);
    return () => window.clearInterval(id);
  }, []);
  return now;
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <Label className="text-xs">{label}</Label>
      {children}
    </div>
  );
}
