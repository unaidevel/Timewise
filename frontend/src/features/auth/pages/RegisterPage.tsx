import { motion } from "framer-motion";
import { Leaf, Loader2 } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate } from "react-router";
import { toast } from "sonner";
import { Button } from "@/components/shadcn/button";
import { Input } from "@/components/shadcn/input";
import { Label } from "@/components/shadcn/label";
import { AuthHero } from "@/features/auth/components/AuthHero";
import { useLogin, useRegister } from "../hooks";

export default function RegisterPage() {
  const navigate = useNavigate();
  const register = useRegister();
  const login = useLogin();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    register.mutate(
      { full_name: fullName, email, password },
      {
        onSuccess: () => {
          login.mutate(
            { email, password },
            {
              onSuccess: () => {
                toast.success("Cuenta creada");
                navigate("/onboarding");
              },
              onError: () => {
                toast.success("Cuenta creada — inicia sesión");
                navigate("/login");
              },
            },
          );
        },
        onError: () => toast.error("No se pudo crear la cuenta"),
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
          <h1 className="text-3xl font-semibold tracking-tight">Crea tu cuenta</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Empieza a gestionar tu equipo en minutos.
          </p>

          <form onSubmit={onSubmit} className="mt-8 space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Nombre completo</Label>
              <Input
                id="name"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email de trabajo</Label>
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
              <Label htmlFor="password">Contraseña</Label>
              <Input
                id="password"
                type="password"
                required
                minLength={8}
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">Mínimo 8 caracteres.</p>
            </div>
            <Button type="submit" className="w-full h-11" disabled={submitting}>
              {submitting ? <Loader2 className="size-4 animate-spin" /> : "Crear cuenta"}
            </Button>
          </form>

          <p className="mt-6 text-sm text-muted-foreground text-center">
            ¿Ya tienes cuenta?{" "}
            <Link to="/login" className="text-foreground font-medium hover:underline">
              Inicia sesión
            </Link>
          </p>
        </div>
      </motion.div>

      <AuthHero />
    </div>
  );
}
