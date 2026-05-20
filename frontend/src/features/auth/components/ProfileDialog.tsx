import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";
import { Button } from "@/components/shadcn/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/shadcn/dialog";
import { Input } from "@/components/shadcn/input";
import { Label } from "@/components/shadcn/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/shadcn/tabs";
import {
  useUpdateMyEmail,
  useUpdateMyName,
  useUpdateMyPassword,
} from "@/features/auth/hooks";
import { useAuthStore } from "@/features/auth/store";

interface ProfileDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ProfileDialog({ open, onOpenChange }: ProfileDialogProps) {
  const { t } = useTranslation();
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{t("profile.title")}</DialogTitle>
          <DialogDescription>{t("profile.description")}</DialogDescription>
        </DialogHeader>
        <Tabs defaultValue="name" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="name">{t("profile.tabs.name")}</TabsTrigger>
            <TabsTrigger value="email">{t("profile.tabs.email")}</TabsTrigger>
            <TabsTrigger value="password">{t("profile.tabs.password")}</TabsTrigger>
          </TabsList>
          <TabsContent value="name">
            <NameForm />
          </TabsContent>
          <TabsContent value="email">
            <EmailForm />
          </TabsContent>
          <TabsContent value="password">
            <PasswordForm />
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
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
    !!fullName.trim() &&
    fullName.trim() !== user?.full_name &&
    !updateName.isPending;

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
    <form onSubmit={handleSubmit} className="space-y-4 pt-2">
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
    !!email.trim() &&
    email.trim().toLowerCase() !== user?.email &&
    !updateEmail.isPending;

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
    <form onSubmit={handleSubmit} className="space-y-4 pt-2">
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
    !!currentPassword &&
    newPassword.length >= 8 &&
    passwordsMatch &&
    !updatePassword.isPending;

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
    <form onSubmit={handleSubmit} className="space-y-4 pt-2">
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
          <p className="text-xs text-destructive">
            {t("profile.password.mismatch")}
          </p>
        )}
      </div>
      <div className="flex justify-end pt-2">
        <Button type="submit" disabled={!canSubmit}>
          {updatePassword.isPending
            ? t("profile.submitting")
            : t("profile.password.save")}
        </Button>
      </div>
    </form>
  );
}
