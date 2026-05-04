import { useState } from "react";
import { useNavigate } from "react-router";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { useCreateTenant } from "../hooks";
import { useTenantStore } from "../store";

export default function OnboardingPage() {
  const navigate = useNavigate();
  const create = useCreateTenant();
  const setCurrent = useTenantStore((s) => s.setCurrentTenantId);
  const [form, setForm] = useState({ name: "", slug: "" });

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    create.mutate(form, {
      onSuccess: (data) => {
        setCurrent(data.id);
        navigate("/");
      },
    });
  }

  return (
    <div className="mx-auto max-w-md">
      <Card>
        <CardHeader
          title="Crea tu organización"
          description="Empieza a gestionar las horas de tu equipo"
        />
        <CardBody>
          <form onSubmit={onSubmit} className="space-y-3">
            <Input
              label="Nombre"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              required
            />
            <Input
              label="Slug"
              value={form.slug}
              onChange={(e) =>
                setForm({ ...form, slug: e.target.value.toLowerCase().replace(/\s+/g, "-") })
              }
              required
              placeholder="mi-empresa"
            />
            <Button type="submit" className="w-full" disabled={create.isPending}>
              {create.isPending ? "Creando…" : "Crear organización"}
            </Button>
          </form>
        </CardBody>
      </Card>
    </div>
  );
}
