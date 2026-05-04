import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { RejectApprovalIn } from "@/client";
import {
  approveReportApiV1TenantsTenantIdApprovalsApprovalIdApprovePost,
  getApprovalApiV1TenantsTenantIdApprovalsApprovalIdGet,
  listApprovalEventsApiV1TenantsTenantIdApprovalsApprovalIdEventsGet,
  listApprovalsApiV1TenantsTenantIdApprovalsGet,
  rejectReportApiV1TenantsTenantIdApprovalsApprovalIdRejectPost,
} from "@/client";

export function useApprovals(tenantId: number | null) {
  return useQuery({
    queryKey: ["approvals", tenantId],
    enabled: tenantId != null,
    queryFn: async () => {
      const { data, error } = await listApprovalsApiV1TenantsTenantIdApprovalsGet({
        path: { tenant_id: tenantId! },
      });
      if (error || !data) throw error;
      return data;
    },
  });
}

export function useApproval(tenantId: number | null, approvalId: number | null) {
  return useQuery({
    queryKey: ["approvals", tenantId, approvalId],
    enabled: tenantId != null && approvalId != null,
    queryFn: async () => {
      const { data, error } = await getApprovalApiV1TenantsTenantIdApprovalsApprovalIdGet({
        path: { tenant_id: tenantId!, approval_id: approvalId! },
      });
      if (error || !data) throw error;
      return data;
    },
  });
}

export function useApprovalEvents(tenantId: number | null, approvalId: number | null) {
  return useQuery({
    queryKey: ["approvals", tenantId, approvalId, "events"],
    enabled: tenantId != null && approvalId != null,
    queryFn: async () => {
      const { data, error } =
        await listApprovalEventsApiV1TenantsTenantIdApprovalsApprovalIdEventsGet({
          path: { tenant_id: tenantId!, approval_id: approvalId! },
        });
      if (error || !data) throw error;
      return data;
    },
  });
}

export function useApproveApproval(tenantId: number | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (approvalId: number) => {
      const { data, error } = await approveReportApiV1TenantsTenantIdApprovalsApprovalIdApprovePost(
        {
          path: { tenant_id: tenantId!, approval_id: approvalId },
        },
      );
      if (error || !data) throw error;
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["approvals", tenantId] }),
  });
}

export function useRejectApproval(tenantId: number | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, body }: { id: number; body: RejectApprovalIn }) => {
      const { data, error } = await rejectReportApiV1TenantsTenantIdApprovalsApprovalIdRejectPost({
        path: { tenant_id: tenantId!, approval_id: id },
        body,
      });
      if (error || !data) throw error;
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["approvals", tenantId] }),
  });
}
