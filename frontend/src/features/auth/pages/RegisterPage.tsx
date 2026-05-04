import { useState } from "react";
import { Link, useNavigate } from "react-router";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useRegister } from "../hooks";

export default function RegisterPage() {
  const navigate = useNavigate();
  const register = useRegister();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    register.mutate(
      { full_name: fullName, email, password },
      { onSuccess: () => navigate("/login") },
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <form
        onSubmit={onSubmit}
        className="w-full max-w-sm space-y-4 rounded-lg border border-slate-200 bg-white p-6 shadow-sm"
      >
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Crear cuenta</h1>
          <p className="text-sm text-slate-600">Empieza a usar TimeWise</p>
        </div>
        <Input
          label="Nombre completo"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          required
        />
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
          autoComplete="new-password"
        />
        {register.isError && (
          <p className="text-sm text-red-600">No se ha podido crear la cuenta.</p>
        )}
        <Button type="submit" className="w-full" disabled={register.isPending}>
          {register.isPending ? "Creando…" : "Crear cuenta"}
        </Button>
        <p className="text-center text-sm text-slate-600">
          ¿Ya tienes cuenta?{" "}
          <Link to="/login" className="font-medium text-slate-900 underline">
            Inicia sesión
          </Link>
        </p>
      </form>
    </div>
  );
}
