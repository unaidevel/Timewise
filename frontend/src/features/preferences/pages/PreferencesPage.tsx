import { RotateCcw, Save } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";
import type { TimezoneOption } from "@/client";
import { Button } from "@/components/shadcn/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/shadcn/card";
import { Label } from "@/components/shadcn/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/shadcn/select";
import { useUpdateMyTimezone } from "@/features/auth/hooks";
import { useAuthStore } from "@/features/auth/store";
import { useCurrentTenantId, useOrganizationProfile, useTimezones } from "@/features/tenants/hooks";

const INHERIT_VALUE = "__inherit__";

export default function PreferencesPage() {
  const { t } = useTranslation();
  const user = useAuthStore((s) => s.user);
  const tenantId = useCurrentTenantId();
  const orgProfile = useOrganizationProfile(tenantId);
  const timezones = useTimezones();
  const update = useUpdateMyTimezone();

  const [selected, setSelected] = useState<string>(INHERIT_VALUE);
  const initial = user?.timezone ?? null;

  useEffect(() => {
    setSelected(initial ?? INHERIT_VALUE);
  }, [initial]);

  const orgTimezone = orgProfile.data?.timezone ?? "UTC";
  const dirty = (selected === INHERIT_VALUE ? null : selected) !== (initial ?? null);

  async function save() {
    try {
      const next = selected === INHERIT_VALUE ? null : selected;
      await update.mutateAsync({ timezone: next });
      toast.success(t("preferences.savedToast"));
    } catch {
      toast.error(t("preferences.saveError"));
    }
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight">{t("preferences.title")}</h1>
        <p className="text-sm text-muted-foreground mt-1">{t("preferences.subtitle")}</p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">{t("preferences.timezone.title")}</CardTitle>
          <CardDescription>{t("preferences.timezone.description")}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="space-y-1.5 max-w-md">
            <Label className="text-xs">{t("preferences.timezone.label")}</Label>
            <TimezoneSelect
              value={selected}
              orgTimezone={orgTimezone}
              loading={timezones.isPending}
              options={timezones.data ?? []}
              onChange={setSelected}
              disabled={update.isPending}
            />
            <p className="text-xs text-muted-foreground">
              {selected === INHERIT_VALUE
                ? t("preferences.timezone.usingOrgDefault", { tz: orgTimezone })
                : t("preferences.timezone.usingOverride", { tz: selected })}
            </p>
          </div>
          <div className="flex gap-2 pt-2">
            <Button onClick={save} disabled={!dirty || update.isPending}>
              <Save className="size-4 mr-2" />
              {update.isPending ? t("preferences.saving") : t("preferences.save")}
            </Button>
            <Button
              variant="outline"
              disabled={update.isPending || selected === INHERIT_VALUE}
              onClick={() => setSelected(INHERIT_VALUE)}
            >
              <RotateCcw className="size-4 mr-2" />
              {t("preferences.timezone.useOrgDefault")}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function TimezoneSelect({
  value,
  orgTimezone,
  loading,
  options,
  onChange,
  disabled,
}: {
  value: string;
  orgTimezone: string;
  loading: boolean;
  options: TimezoneOption[];
  onChange: (value: string) => void;
  disabled: boolean;
}) {
  const { t } = useTranslation();
  const items = useMemo(() => {
    if (value !== INHERIT_VALUE && !options.some((o) => o.value === value)) {
      return [{ value, label: value }, ...options];
    }
    return options;
  }, [options, value]);

  return (
    <Select value={value} onValueChange={onChange} disabled={disabled}>
      <SelectTrigger>
        <SelectValue placeholder={loading ? t("preferences.loading") : undefined} />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={INHERIT_VALUE}>
          {t("preferences.timezone.inheritOption", { tz: orgTimezone })}
        </SelectItem>
        {items.map((opt) => (
          <SelectItem key={opt.value} value={opt.value}>
            {opt.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
