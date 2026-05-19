import * as DialogPrimitive from "@radix-ui/react-dialog";
import { Sparkles } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/shadcn/button";
import {
  Dialog,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/shadcn/dialog";
import { useCurrentTenantId, useSeedDemoData, useTenantIsEmpty } from "@/features/tenants/hooks";

const DISMISS_KEY = "timewise-demo-data-dismissed";

function isDismissed(tenantId: number): boolean {
  try {
    return sessionStorage.getItem(`${DISMISS_KEY}:${tenantId}`) === "1";
  } catch {
    return false;
  }
}

function markDismissed(tenantId: number): void {
  try {
    sessionStorage.setItem(`${DISMISS_KEY}:${tenantId}`, "1");
  } catch {
    /* ignore */
  }
}

export function DemoDataBanner() {
  const tenantId = useCurrentTenantId();
  const isEmpty = useTenantIsEmpty(tenantId);
  const seed = useSeedDemoData(tenantId);
  const [dismissed, setDismissed] = useState(() =>
    tenantId == null ? false : isDismissed(tenantId),
  );

  const open = tenantId != null && isEmpty && !dismissed;

  function handleStartEmpty() {
    if (tenantId != null) markDismissed(tenantId);
    setDismissed(true);
  }

  return (
    <Dialog open={open}>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/40 backdrop-blur-md data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
        <DialogPrimitive.Content
          className="fixed left-1/2 top-1/2 z-50 grid w-[92vw] max-w-xl -translate-x-1/2 -translate-y-1/2 gap-6 border bg-background p-8 shadow-2xl duration-200 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 sm:rounded-xl"
          onEscapeKeyDown={(e) => e.preventDefault()}
          onPointerDownOutside={(e) => e.preventDefault()}
          onInteractOutside={(e) => e.preventDefault()}
        >
          <DialogHeader>
            <div className="mx-auto mb-2 size-12 rounded-full bg-primary/10 grid place-items-center">
              <Sparkles className="size-6 text-primary" />
            </div>
            <DialogTitle className="text-center text-xl">
              Carga datos para ver el flujo de la app
            </DialogTitle>
            <DialogDescription className="text-center">
              Creamos un equipo de ejemplo (departamentos, empleados, periodos, reportes). Puedes
              editarlos o borrarlos después.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="sm:justify-center gap-2">
            <Button variant="outline" onClick={handleStartEmpty} disabled={seed.isPending}>
              Empezar de cero
            </Button>
            <Button
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
          </DialogFooter>
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </Dialog>
  );
}
