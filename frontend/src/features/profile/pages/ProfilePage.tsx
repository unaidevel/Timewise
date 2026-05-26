import { RotateCcw, Save } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";
import type { TimezoneOption } from "@/client";
import { Button } from "@/components/shadcn/button";
import { Input } from "@/components/shadcn/input";
import { Label } from "@/components/shadcn/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/shadcn/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/shadcn/tabs";
import {
  useUpdateMyEmail,
  useUpdateMyName,
  useUpdateMyPassword,
  useUpdateMyTimezone,
} from "@/features/auth/hooks";
import { useAuthStore } from "@/features/auth/store";
import { useCurrentTenantId, useOrganizationProfile, useTimezones } from "@/features/tenants/hooks";

const INHERIT_VALUE = "__inherit__";

export default function ProfilePage() {
  const { t } = useTranslation();
  return (
    <div className="space-y-6 max-w-2xl">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight">{t("profile.title")}</h1>
        <p className="text-sm text-muted-foreground mt-1">{t("profile.subtitle")}</p>
      </header>

      <Tabs defaultValue="name" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="name">{t("profile.tabs.name")}</TabsTrigger>
          <TabsTrigger value="email">{t("profile.tabs.email")}</TabsTrigger>
          <TabsTrigger value="password">{t("profile.tabs.password")}</TabsTrigger>
          <TabsTrigger value="timezone">{t("profile.tabs.timezone")}</TabsTrigger>
        </TabsList>
        <TabsContent value="name" className="pt-4">
          <NameForm />
        </TabsContent>
        <TabsContent value="email" className="pt-4">
          <EmailForm />
        </TabsContent>
        <TabsContent value="password" className="pt-4">
          <PasswordForm />
        </TabsContent>
        <TabsContent value="timezone" className="pt-4">
          <TimezoneForm />
        </TabsContent>
      </Tabs>
    </div>
  );
}

function NameForm() {
  const { t } = useTranslation();
  const user = useAuthStore((s) => s.user);
  const updateName = useUpdateMyName();
  const [fullName, setFullName] = useState(user?.full_name ?? "");

  useEffect(() => {
    setFullName(user?.full_name ?? "");
  }, [user?.full_name]);

  const canSubmit =
    !!fullName.trim() && fullName.trim() !== user?.full_name && !updateName.isPending;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;
    try {
      await updateName.mutateAsync({ full_name: fullName.trim() });
      toast.success(t("profile.name.successToast"));
    } catch {
      toast.error(t("profile.name.errorToast"));
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-1.5">
        <Label className="text-xs" htmlFor="profile-fullname">
          {t("profile.name.label")}
        </Label>
        <Input
          id="profile-fullname"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          autoComplete="name"
          required
        />
      </div>
      <div className="flex justify-end pt-2">
        <Button type="submit" disabled={!canSubmit}>
          {updateName.isPending ? t("profile.submitting") : t("profile.save")}
        </Button>
      </div>
    </form>
  );
}

function EmailForm() {
  const { t } = useTranslation();
  const user = useAuthStore((s) => s.user);
  const updateEmail = useUpdateMyEmail();
  const [email, setEmail] = useState(user?.email ?? "");

  useEffect(() => {
    setEmail(user?.email ?? "");
  }, [user?.email]);

  const canSubmit =
    !!email.trim() && email.trim().toLowerCase() !== user?.email && !updateEmail.isPending;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;
    try {
      await updateEmail.mutateAsync({ email: email.trim() });
      toast.success(t("profile.email.successToast"));
    } catch (err) {
      const status = (err as { status?: number } | undefined)?.status;
      if (status === 409) {
        toast.error(t("profile.email.conflictToast"));
      } else {
        toast.error(t("profile.email.errorToast"));
      }
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-1.5">
        <Label className="text-xs" htmlFor="profile-email">
          {t("profile.email.label")}
        </Label>
        <Input
          id="profile-email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          autoComplete="email"
          required
        />
      </div>
      <div className="flex justify-end pt-2">
        <Button type="submit" disabled={!canSubmit}>
          {updateEmail.isPending ? t("profile.submitting") : t("profile.save")}
        </Button>
      </div>
    </form>
  );
}

function PasswordForm() {
  const { t } = useTranslation();
  const updatePassword = useUpdateMyPassword();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const passwordsMatch = newPassword === confirmPassword;
  const canSubmit =
    !!currentPassword && newPassword.length >= 8 && passwordsMatch && !updatePassword.isPending;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;
    try {
      await updatePassword.mutateAsync({
        current_password: currentPassword,
        new_password: newPassword,
      });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      toast.success(t("profile.password.successToast"));
    } catch (err) {
      const status = (err as { status?: number } | undefined)?.status;
      if (status === 401) {
        toast.error(t("profile.password.wrongCurrentToast"));
      } else if (status === 422) {
        toast.error(t("profile.password.weakToast"));
      } else {
        toast.error(t("profile.password.errorToast"));
      }
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-1.5">
        <Label className="text-xs" htmlFor="profile-current-password">
          {t("profile.password.current")}
        </Label>
        <Input
          id="profile-current-password"
          type="password"
          value={currentPassword}
          onChange={(e) => setCurrentPassword(e.target.value)}
          autoComplete="current-password"
          required
        />
      </div>
      <div className="space-y-1.5">
        <Label className="text-xs" htmlFor="profile-new-password">
          {t("profile.password.new")}
        </Label>
        <Input
          id="profile-new-password"
          type="password"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          autoComplete="new-password"
          required
        />
      </div>
      <div className="space-y-1.5">
        <Label className="text-xs" htmlFor="profile-confirm-password">
          {t("profile.password.confirm")}
        </Label>
        <Input
          id="profile-confirm-password"
          type="password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          autoComplete="new-password"
          required
        />
        {confirmPassword && !passwordsMatch && (
          <p className="text-xs text-destructive">{t("profile.password.mismatch")}</p>
        )}
      </div>
      <div className="flex justify-end pt-2">
        <Button type="submit" disabled={!canSubmit}>
          {updatePassword.isPending ? t("profile.submitting") : t("profile.password.save")}
        </Button>
      </div>
    </form>
  );
}

function TimezoneForm() {
  const { t } = useTranslation();
  const user = useAuthStore((s) => s.user);
  const tenantId = useCurrentTenantId();
  const orgProfile = useOrganizationProfile(tenantId);
  const timezones = useTimezones();
  const update = useUpdateMyTimezone();

  const initial = user?.timezone ?? null;
  const [selected, setSelected] = useState<string>(initial ?? INHERIT_VALUE);

  useEffect(() => {
    setSelected(initial ?? INHERIT_VALUE);
  }, [initial]);

  const orgTimezone = orgProfile.data?.timezone ?? "UTC";
  const dirty = (selected === INHERIT_VALUE ? null : selected) !== (initial ?? null);

  async function save() {
    try {
      const next = selected === INHERIT_VALUE ? null : selected;
      await update.mutateAsync({ timezone: next });
      toast.success(t("profile.timezone.successToast"));
    } catch {
      toast.error(t("profile.timezone.errorToast"));
    }
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">{t("profile.timezone.description")}</p>
      <div className="space-y-1.5">
        <Label className="text-xs">{t("profile.timezone.label")}</Label>
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
            ? t("profile.timezone.usingOrgDefault", { tz: orgTimezone })
            : t("profile.timezone.usingOverride", { tz: selected })}
        </p>
      </div>
      <div className="flex gap-2 pt-2">
        <Button onClick={save} disabled={!dirty || update.isPending}>
          <Save className="size-4 mr-2" />
          {update.isPending ? t("profile.submitting") : t("profile.save")}
        </Button>
        <Button
          variant="outline"
          disabled={update.isPending || selected === INHERIT_VALUE}
          onClick={() => setSelected(INHERIT_VALUE)}
        >
          <RotateCcw className="size-4 mr-2" />
          {t("profile.timezone.useOrgDefault")}
        </Button>
      </div>
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
        <SelectValue placeholder={loading ? t("profile.timezone.loading") : undefined} />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={INHERIT_VALUE}>
          {t("profile.timezone.inheritOption", { tz: orgTimezone })}
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
