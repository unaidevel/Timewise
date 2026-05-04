import { useState } from "react";
import { Link, useNavigate } from "react-router";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useLogin } from "../hooks";

export default function LoginPage() {
  const navigate = useNavigate();
  const login = useLogin();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    login.mutate({ email, password }, { onSuccess: () => navigate("/") });
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <form
        onSubmit={onSubmit}
        className="w-full max-w-sm space-y-4 rounded-lg border border-slate-200 bg-white p-6 shadow-sm"
      >
        <div>
          <h1 className="text-xl font-semibold text-slate-900">TimeWise</h1>
          <p className="text-sm text-slate-600">Inicia sesión para continuar</p>
        </div>
        <Input
          label="Email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          autoComplete="email"
        />
        <Input
          label="Contraseña"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          autoComplete="current-password"
        />
        {login.isError && (
          <p className="text-sm text-red-600">
            No se ha podido iniciar sesión. Comprueba tus credenciales.
          </p>
        )}
        <Button type="submit" className="w-full" disabled={login.isPending}>
          {login.isPending ? "Entrando…" : "Entrar"}
        </Button>
        <p className="text-center text-sm text-slate-600">
          ¿No tienes cuenta?{" "}
          <Link to="/register" className="font-medium text-slate-900 underline">
            Regístrate
          </Link>
        </p>
      </form>
    </div>
  );
}
