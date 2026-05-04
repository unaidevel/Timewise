import { create } from "zustand";
import { persist } from "zustand/middleware";

interface TenantState {
  currentTenantId: number | null;
  setCurrentTenantId: (id: number | null) => void;
}

export const useTenantStore = create<TenantState>()(
  persist(
    (set) => ({
      currentTenantId: null,
      setCurrentTenantId: (id) => set({ currentTenantId: id }),
    }),
    { name: "timewise-tenant" },
  ),
);
