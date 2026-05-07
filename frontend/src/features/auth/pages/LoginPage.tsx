import { motion } from "framer-motion";
import { Leaf, Loader2 } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate } from "react-router";
import { toast } from "sonner";
import { Button } from "@/components/shadcn/button";
import { Input } from "@/components/shadcn/input";
import { Label } from "@/components/shadcn/label";
import { AuthHero } from "@/features/auth/components/AuthHero";
import { useLogin } from "../hooks";

export default function LoginPage() {
  const navigate = useNavigate();
  const login = useLogin();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    login.mutate(
      { email, password },
      {
        onSuccess: (data) => {
          toast.success(`Bienvenido, ${data.user.full_name?.split(" ")[0] ?? data.user.email}`);
          navigate("/");
        },
        onError: () => {
          toast.error("Credenciales incorrectas");
        },
      },
    );
  }

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
          <h1 className="text-3xl font-semibold tracking-tight">Bienvenido de nuevo</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Inicia sesión para continuar en tu workspace.
          </p>

          <form onSubmit={onSubmit} className="mt-8 space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
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
              <div className="flex items-center justify-between">
                <Label htmlFor="password">Contraseña</Label>
              </div>
              <Input
                id="password"
                type="password"
                required
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            <Button type="submit" className="w-full h-11" disabled={login.isPending}>
              {login.isPending ? <Loader2 className="size-4 animate-spin" /> : "Entrar"}
            </Button>
          </form>

          <p className="mt-6 text-sm text-muted-foreground text-center">
            ¿No tienes cuenta?{" "}
            <Link to="/register" className="text-foreground font-medium hover:underline">
              Crear una cuenta
            </Link>
          </p>
        </div>
      </motion.div>

      <AuthHero />
    </div>
  );
}
