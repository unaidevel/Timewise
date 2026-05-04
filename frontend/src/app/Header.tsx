import { useEffect } from "react";
import { Button } from "@/components/ui/Button";
import { Select } from "@/components/ui/Input";
import { useLogout } from "@/features/auth/hooks";
import { useAuthStore } from "@/features/auth/store";
import { useTenants } from "@/features/tenants/hooks";
import { useTenantStore } from "@/features/tenants/store";

export function Header() {
  const user = useAuthStore((s) => s.user);
  const logout = useLogout();
  const { currentTenantId, setCurrentTenantId } = useTenantStore();
  const { data: tenants = [] } = useTenants();

  useEffect(() => {
    if (currentTenantId == null && tenants.length > 0) {
      setCurrentTenantId(tenants[0].id);
    }
  }, [currentTenantId, tenants, setCurrentTenantId]);

  return (
    <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-3">
      <div className="flex items-center gap-3">
        {tenants.length > 0 && (
          <Select
            value={currentTenantId ?? ""}
            onChange={(e) => setCurrentTenantId(Number(e.target.value))}
            className="min-w-[200px]"
          >
            {tenants.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </Select>
        )}
      </div>
      <div className="flex items-center gap-3 text-sm text-slate-700">
        <span className="hidden md:inline">{user?.full_name ?? user?.email}</span>
        <Button variant="ghost" onClick={() => logout.mutate()}>
          Cerrar sesión
        </Button>
      </div>
    </header>
  );
}
