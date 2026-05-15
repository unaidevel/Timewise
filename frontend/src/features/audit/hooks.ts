import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  listEventsApiV1TenantsTenantIdAuditEventsGet,
  updateEventApiV1TenantsTenantIdAuditEventsEventIdPut,
} from "@/client";

export interface AuditFilters {
  action?: string | null;
  resource_type?: string | null;
  resource_id?: number | null;
  actor_id?: number | null;
  outcome?: string | null;
}

export function useAuditEvents(tenantId: number | null, filters: AuditFilters = {}) {
  return useQuery({
    queryKey: ["audit", tenantId, filters],
    enabled: tenantId != null,
    queryFn: async () => {
      const { data, error } = await listEventsApiV1TenantsTenantIdAuditEventsGet({
        path: { tenant_id: tenantId! },
        query: filters,
      });
      if (error || !data) throw error;
      return data;
    },
  });
}

export function useUpdateAuditEventNotes(tenantId: number | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ eventId, notes }: { eventId: number; notes: string }) => {
      const { data, error } = await updateEventApiV1TenantsTenantIdAuditEventsEventIdPut({
        path: { tenant_id: tenantId!, event_id: eventId },
        body: { notes },
      });
      if (error || !data) throw error;
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["audit", tenantId] }),
  });
}
