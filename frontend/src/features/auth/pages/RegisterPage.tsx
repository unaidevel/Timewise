import { motion } from "framer-motion";
import { Leaf, Loader2 } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router";
import { toast } from "sonner";
import { Button } from "@/components/shadcn/button";
import { Input } from "@/components/shadcn/input";
import { Label } from "@/components/shadcn/label";
import { AuthHero } from "@/features/auth/components/AuthHero";
import { useLogin, useRegister } from "../hooks";

function extractErrorMessages(error: unknown): string[] {
  if (error && typeof error === "object" && "detail" in error) {
    const detail = (error as { detail: unknown }).detail;
    if (Array.isArray(detail)) return detail.map(String);
    if (typeof detail === "string") return [detail];
  }
  return [];
}

export default function RegisterPage() {
  const navigate = useNavigate();
  const register = useRegister();
  const login = useLogin();
  const { t } = useTranslation();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [formErrors, setFormErrors] = useState<string[]>([]);

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormErrors([]);
    register.mutate(
      { full_name: fullName, email, password },
      {
        onSuccess: () => {
          login.mutate(
            { email, password },
            {
              onSuccess: () => {
                toast.success(t("auth.register.success"));
                navigate("/onboarding");
              },
              onError: () => {
                toast.success(t("auth.register.successNeedLogin"));
                navigate("/login");
              },
            },
          );
        },
        onError: (error: unknown) => {
          const raw = extractErrorMessages(error);
          const messages = raw.map((msg) =>
            msg.toLowerCase().includes("email") && msg.toLowerCase().includes("exist")
              ? t("auth.register.errorEmailTaken")
              : msg,
          );
          setFormErrors(messages.length ? messages : [t("auth.register.error")]);
        },
      },
    );
  }

  const submitting = register.isPending || login.isPending;

  return (
    <div className="min-h-screen grid lg:grid-cols-2">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="flex items-center justify-center px-6 py-12"
      >
        <div className="w-full max-w-sm">
          <Link to="/login" className="inline-flex items-center gap-2 mb-10">
            <div className="size-9 rounded-xl bg-primary text-primary-foreground grid place-items-center">
              <Leaf className="size-4" />
            </div>
            <span className="font-semibold tracking-tight">TimeWise</span>
          </Link>
          <h1 className="text-3xl font-semibold tracking-tight">{t("auth.register.title")}</h1>
          <p className="mt-2 text-sm text-muted-foreground">{t("auth.register.subtitle")}</p>

          <form onSubmit={onSubmit} className="mt-8 space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">{t("auth.register.fullName")}</Label>
              <Input
                id="name"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">{t("auth.register.workEmail")}</Label>
              <Input
                id="email"
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">{t("auth.register.password")}</Label>
              <Input
                id="password"
                type="password"
                required
                minLength={8}
                autoComplete="new-password"
                value={password}
                onChange={(e) => { setPassword(e.target.value); setFormErrors([]); }}
              />
              <p className="text-xs text-muted-foreground">{t("auth.register.passwordHint")}</p>
            </div>
            {formErrors.length > 0 && (
              <ul className="space-y-1">
                {formErrors.map((msg) => (
                  <li key={msg} className="text-sm text-destructive">
                    {msg}
                  </li>
                ))}
              </ul>
            )}
            <Button type="submit" className="w-full h-11" disabled={submitting}>
              {submitting ? <Loader2 className="size-4 animate-spin" /> : t("auth.register.submit")}
            </Button>
          </form>

          <p className="mt-6 text-sm text-muted-foreground text-center">
            {t("auth.register.haveAccount")}{" "}
            <Link to="/login" className="text-foreground font-medium hover:underline">
              {t("auth.register.signIn")}
            </Link>
          </p>
        </div>
      </motion.div>

      <AuthHero />
    </div>
  );
}
