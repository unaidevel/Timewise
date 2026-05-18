import { Sparkles, X } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/shadcn/button";
import {
  useCurrentTenantId,
  useSeedDemoData,
  useTenantIsEmpty,
} from "@/features/tenants/hooks";

export function DemoDataBanner() {
  const tenantId = useCurrentTenantId();
  const isEmpty = useTenantIsEmpty(tenantId);
  const seed = useSeedDemoData(tenantId);
  const [dismissed, setDismissed] = useState(false);

  if (tenantId == null || !isEmpty || dismissed) return null;

  return (
    <div className="flex items-center gap-3 rounded-lg border border-primary/30 bg-primary/5 px-4 py-3">
      <Sparkles className="size-5 text-primary shrink-0" />
      <div className="flex-1 text-sm">
        <p className="font-medium text-foreground">
          Carga datos para ver el flujo de la app
        </p>
        <p className="text-muted-foreground">
          Creamos un equipo de ejemplo (departamentos, empleados, periodos,
          reportes). Puedes editarlos o borrarlos después.
        </p>
      </div>
      <Button
        size="sm"
        onClick={() =>
          seed.mutate(undefined, {
            onSuccess: () => toast.success("Datos de demo cargados"),
            onError: () => toast.error("No se pudieron cargar los datos"),
          })
        }
        disabled={seed.isPending}
      >
        {seed.isPending ? "Cargando…" : "Cargar demo"}
      </Button>
      <button
        type="button"
        aria-label="Descartar"
        onClick={() => setDismissed(true)}
        className="text-muted-foreground hover:text-foreground"
      >
        <X className="size-4" />
      </button>
    </div>
  );
}
