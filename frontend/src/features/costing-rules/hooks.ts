import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { OvertimeRuleIn, OvertimeRuleUpdate } from "@/client";
import {
  createRuleApiV1TenantsTenantIdCostingRulesPost,
  deactivateRuleApiV1TenantsTenantIdCostingRulesRuleIdDelete,
  getRuleApiV1TenantsTenantIdCostingRulesRuleIdGet,
  listRulesApiV1TenantsTenantIdCostingRulesGet,
  updateRuleApiV1TenantsTenantIdCostingRulesRuleIdPut,
} from "@/client";

export function useOvertimeRules(tenantId: number | null) {
  return useQuery({
    queryKey: ["costing-rules", tenantId],
    enabled: tenantId != null,
    queryFn: async () => {
      const { data, error } = await listRulesApiV1TenantsTenantIdCostingRulesGet({
        path: { tenant_id: tenantId! },
      });
      if (error || !data) throw error;
      return data;
    },
  });
}

export function useOvertimeRule(tenantId: number | null, ruleId: number | null) {
  return useQuery({
    queryKey: ["costing-rules", tenantId, ruleId],
    enabled: tenantId != null && ruleId != null,
    queryFn: async () => {
      const { data, error } = await getRuleApiV1TenantsTenantIdCostingRulesRuleIdGet({
        path: { tenant_id: tenantId!, rule_id: ruleId! },
      });
      if (error || !data) throw error;
      return data;
    },
  });
}

export function useCreateOvertimeRule(tenantId: number | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: OvertimeRuleIn) => {
      const { data, error } = await createRuleApiV1TenantsTenantIdCostingRulesPost({
        path: { tenant_id: tenantId! },
        body,
      });
      if (error || !data) throw error;
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["costing-rules", tenantId] }),
  });
}

export function useUpdateOvertimeRule(tenantId: number | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, body }: { id: number; body: OvertimeRuleUpdate }) => {
      const { data, error } = await updateRuleApiV1TenantsTenantIdCostingRulesRuleIdPut({
        path: { tenant_id: tenantId!, rule_id: id },
        body,
      });
      if (error || !data) throw error;
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["costing-rules", tenantId] }),
  });
}

export function useDeactivateOvertimeRule(tenantId: number | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      const { data, error } = await deactivateRuleApiV1TenantsTenantIdCostingRulesRuleIdDelete({
        path: { tenant_id: tenantId!, rule_id: id },
      });
      if (error || !data) throw error;
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["costing-rules", tenantId] }),
  });
}
