import { motion } from "framer-motion";
import { ArrowRight, Leaf, Loader2 } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router";
import { toast } from "sonner";
import { Button } from "@/components/shadcn/button";
import { Input } from "@/components/shadcn/input";
import { Label } from "@/components/shadcn/label";
import { useAuthStore } from "@/features/auth/store";
import { useCreateTenant } from "../hooks";
import { useTenantStore } from "../store";

export default function OnboardingPage() {
  const navigate = useNavigate();
  const create = useCreateTenant();
  const setCurrent = useTenantStore((s) => s.setCurrentTenantId);
  const user = useAuthStore((s) => s.user);
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    create.mutate(
      { name, slug: slug || name.toLowerCase().replace(/\s+/g, "-") },
      {
        onSuccess: (data) => {
          setCurrent(data.id);
          toast.success(`${data.name} listo`);
          navigate("/");
        },
        onError: () => toast.error("No se pudo crear el workspace"),
      },
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-6 py-12 bg-gradient-to-br from-background to-muted/40">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        <div className="inline-flex items-center gap-2 mb-8">
          <div className="size-9 rounded-xl bg-primary text-primary-foreground grid place-items-center">
            <Leaf className="size-4" />
          </div>
          <span className="font-semibold tracking-tight">TimeWise</span>
        </div>

        <div className="rounded-2xl border bg-card p-8 shadow-[var(--shadow-elegant)]">
          <p className="text-sm text-muted-foreground">
            Hola {user?.full_name?.split(" ")[0] ?? user?.email} 👋
          </p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight">Crea tu workspace</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Cada workspace es un tenant independiente — tus datos, tu equipo.
          </p>

          <form onSubmit={onSubmit} className="mt-6 space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Nombre de la empresa</Label>
              <Input
                id="name"
                required
                value={name}
                onChange={(e) => {
                  setName(e.target.value);
                  setSlug(
                    e.target.value
                      .toLowerCase()
                      .replace(/[^a-z0-9]+/g, "-")
                      .replace(/^-|-$/g, ""),
                  );
                }}
                placeholder="Acme Robotics"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="slug">URL del workspace</Label>
              <div className="flex items-center rounded-md border bg-background focus-within:ring-2 focus-within:ring-ring overflow-hidden">
                <span className="px-3 text-sm text-muted-foreground border-r bg-muted/40 h-10 grid place-items-center">
                  timewise.app/
                </span>
                <Input
                  id="slug"
                  value={slug}
                  onChange={(e) => setSlug(e.target.value)}
                  className="border-0 focus-visible:ring-0"
                  placeholder="acme"
                />
              </div>
            </div>
            <Button type="submit" className="w-full h-11" disabled={create.isPending || !name}>
              {create.isPending ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <>
                  Crear workspace <ArrowRight className="size-4 ml-1" />
                </>
              )}
            </Button>
          </form>
        </div>
      </motion.div>
    </div>
  );
}
