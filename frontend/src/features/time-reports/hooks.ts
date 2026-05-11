import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { RejectReportRequest, TimeEntryIn, TimeEntryUpdate } from "@/client";
import {
  approveTimeReportApiV1TenantsTenantIdReportsReportIdApprovePost,
  calculateReportCostApiV1TenantsTenantIdCostingReportsReportIdCalculatePost,
  createTimeEntryApiV1TenantsTenantIdReportsReportIdEntriesPost,
  deleteTimeEntryApiV1TenantsTenantIdReportsReportIdEntriesEntryIdDelete,
  getTimeReportApiV1TenantsTenantIdReportsReportIdGet,
  listReportCalculationsApiV1TenantsTenantIdCostingReportsReportIdCalculationsGet,
  listReportHistoryApiV1TenantsTenantIdReportsReportIdHistoryGet,
  listTimeEntriesApiV1TenantsTenantIdReportsReportIdEntriesGet,
  rejectTimeReportApiV1TenantsTenantIdReportsReportIdRejectPost,
  submitTimeReportApiV1TenantsTenantIdReportsReportIdSubmitPost,
  updateTimeEntryApiV1TenantsTenantIdReportsReportIdEntriesEntryIdPut,
} from "@/client";

export function useTimeReport(tenantId: number | null, reportId: number | null) {
  return useQuery({
    queryKey: ["time-report", tenantId, reportId],
    enabled: tenantId != null && reportId != null,
    queryFn: async () => {
      const { data, error } = await getTimeReportApiV1TenantsTenantIdReportsReportIdGet({
        path: { tenant_id: tenantId!, report_id: reportId! },
      });
      if (error || !data) throw error;
      return data;
    },
  });
}

export function useReportHistory(tenantId: number | null, reportId: number | null) {
  return useQuery({
    queryKey: ["time-report", tenantId, reportId, "history"],
    enabled: tenantId != null && reportId != null,
    queryFn: async () => {
      const { data, error } = await listReportHistoryApiV1TenantsTenantIdReportsReportIdHistoryGet({
        path: { tenant_id: tenantId!, report_id: reportId! },
      });
      if (error || !data) throw error;
      return data;
    },
  });
}

export function useSubmitReport(tenantId: number | null, reportId: number | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const { data, error } = await submitTimeReportApiV1TenantsTenantIdReportsReportIdSubmitPost({
        path: { tenant_id: tenantId!, report_id: reportId! },
      });
      if (error || !data) throw error;
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["time-report", tenantId, reportId] });
      qc.invalidateQueries({ queryKey: ["approvals", tenantId] });
    },
  });
}

export function useApproveReport(tenantId: number | null, reportId: number | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const { data, error } = await approveTimeReportApiV1TenantsTenantIdReportsReportIdApprovePost(
        {
          path: { tenant_id: tenantId!, report_id: reportId! },
        },
      );
      if (error || !data) throw error;
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["time-report", tenantId, reportId] }),
  });
}

export function useRejectReport(tenantId: number | null, reportId: number | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: RejectReportRequest) => {
      const { data, error } = await rejectTimeReportApiV1TenantsTenantIdReportsReportIdRejectPost({
        path: { tenant_id: tenantId!, report_id: reportId! },
        body,
      });
      if (error || !data) throw error;
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["time-report", tenantId, reportId] }),
  });
}

export function useTimeEntries(tenantId: number | null, reportId: number | null) {
  return useQuery({
    queryKey: ["time-entries", tenantId, reportId],
    enabled: tenantId != null && reportId != null,
    queryFn: async () => {
      const { data, error } = await listTimeEntriesApiV1TenantsTenantIdReportsReportIdEntriesGet({
        path: { tenant_id: tenantId!, report_id: reportId! },
      });
      if (error || !data) throw error;
      return data;
    },
  });
}

export function useCreateTimeEntry(tenantId: number | null, reportId: number | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: TimeEntryIn) => {
      const { data, error } = await createTimeEntryApiV1TenantsTenantIdReportsReportIdEntriesPost({
        path: { tenant_id: tenantId!, report_id: reportId! },
        body,
      });
      if (error || !data) throw error;
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["time-entries", tenantId, reportId] }),
  });
}

export function useUpdateTimeEntry(tenantId: number | null, reportId: number | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, body }: { id: number; body: TimeEntryUpdate }) => {
      const { data, error } =
        await updateTimeEntryApiV1TenantsTenantIdReportsReportIdEntriesEntryIdPut({
          path: { tenant_id: tenantId!, report_id: reportId!, entry_id: id },
          body,
        });
      if (error || !data) throw error;
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["time-entries", tenantId, reportId] }),
  });
}

export function useDeleteTimeEntry(tenantId: number | null, reportId: number | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      const { error } =
        await deleteTimeEntryApiV1TenantsTenantIdReportsReportIdEntriesEntryIdDelete({
          path: { tenant_id: tenantId!, report_id: reportId!, entry_id: id },
        });
      if (error) throw error;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["time-entries", tenantId, reportId] }),
  });
}

export function useReportCostBreakdown(tenantId: number | null, reportId: number | null) {
  return useQuery({
    queryKey: ["cost-breakdown", tenantId, reportId],
    enabled: tenantId != null && reportId != null,
    queryFn: async () => {
      const { data, error } =
        await listReportCalculationsApiV1TenantsTenantIdCostingReportsReportIdCalculationsGet({
          path: { tenant_id: tenantId!, report_id: reportId! },
        });
      if (error || !data) throw error;
      return data;
    },
  });
}

export function useCalculateReportCost(tenantId: number | null, reportId: number | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const { data, error } =
        await calculateReportCostApiV1TenantsTenantIdCostingReportsReportIdCalculatePost({
          path: { tenant_id: tenantId!, report_id: reportId! },
        });
      if (error || !data) throw error;
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["cost-breakdown", tenantId, reportId] }),
  });
}
