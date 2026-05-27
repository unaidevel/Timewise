import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { ACTIONS, EVENTS, type EventData, Joyride, STATUS, type Step } from "react-joyride";
import { useNavigate } from "react-router";
import { useMarkTourCompleted } from "@/features/auth/hooks";
import { useTourStore } from "@/features/onboarding/store";

type TourStep = Step & {
  /** Route to navigate to before this step is shown */
  route: string;
  /** Optional query string to set (e.g. for settings tabs) */
  search?: string;
};

export function TourRunner() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const shouldRun = useTourStore((s) => s.shouldRun);
  const stopTour = useTourStore((s) => s.stopTour);
  const markCompleted = useMarkTourCompleted();
  const [stepIndex, setStepIndex] = useState(0);
  const pendingAdvance = useRef<number | null>(null);

  const steps: TourStep[] = useMemo(
    () => [
      // ── 1. Home nav ───────────────────────────────────────────────────────
      {
        target: '[data-tour="nav-home"]',
        title: t("onboarding.tour.steps.home.title"),
        content: t("onboarding.tour.steps.home.body"),
        route: "/",
        placement: "right",
        disableBeacon: true,
        skipScroll: true,
      },
      // ── 2. Dashboard KPIs ─────────────────────────────────────────────────
      {
        target: '[data-tour="dashboard-kpis"]',
        title: t("onboarding.tour.steps.dashboardKpis.title"),
        content: t("onboarding.tour.steps.dashboardKpis.body"),
        route: "/",
        placement: "bottom",
        skipScroll: true,
      },
      // ── 3. Cost trend chart ───────────────────────────────────────────────
      {
        target: '[data-tour="dashboard-cost-trend"]',
        title: t("onboarding.tour.steps.dashboardCost.title"),
        content: t("onboarding.tour.steps.dashboardCost.body"),
        route: "/",
        placement: "top",
        skipScroll: true,
      },
      // ── 4. Dashboard — recent activity ───────────────────────────────────
      {
        target: '[data-tour="dashboard-activity"]',
        title: t("onboarding.tour.steps.dashboardActivity.title"),
        content: t("onboarding.tour.steps.dashboardActivity.body"),
        route: "/",
        placement: "left",
        skipScroll: true,
      },
      // ── 5. Employees nav ──────────────────────────────────────────────────
      {
        target: '[data-tour="nav-employees"]',
        title: t("onboarding.tour.steps.employees.title"),
        content: t("onboarding.tour.steps.employees.body"),
        route: "/employees",
        placement: "right",
        skipScroll: true,
      },
      // ── 6. Employees — search & filters ──────────────────────────────────
      {
        target: '[data-tour="employees-filters"]',
        title: t("onboarding.tour.steps.employeesFilters.title"),
        content: t("onboarding.tour.steps.employeesFilters.body"),
        route: "/employees",
        placement: "bottom",
        skipScroll: true,
      },
      // ── 7. Employees — table ─────────────────────────────────────────────
      {
        target: '[data-tour="employees-table"]',
        title: t("onboarding.tour.steps.employeesTable.title"),
        content: t("onboarding.tour.steps.employeesTable.body"),
        route: "/employees",
        placement: "top",
        skipScroll: true,
      },
      // ── 8. Departments nav ────────────────────────────────────────────────
      {
        target: '[data-tour="nav-departments"]',
        title: t("onboarding.tour.steps.departments.title"),
        content: t("onboarding.tour.steps.departments.body"),
        route: "/departments",
        placement: "right",
        skipScroll: true,
      },
      // ── 9. Departments — table ────────────────────────────────────────────
      {
        target: '[data-tour="departments-table"]',
        title: t("onboarding.tour.steps.departmentsTable.title"),
        content: t("onboarding.tour.steps.departmentsTable.body"),
        route: "/departments",
        placement: "top",
        skipScroll: true,
      },
      // ── 10. Roles nav ─────────────────────────────────────────────────────
      {
        target: '[data-tour="nav-roles"]',
        title: t("onboarding.tour.steps.roles.title"),
        content: t("onboarding.tour.steps.roles.body"),
        route: "/roles",
        placement: "right",
        skipScroll: true,
      },
      // ── 11. Roles — table ─────────────────────────────────────────────────
      {
        target: '[data-tour="roles-table"]',
        title: t("onboarding.tour.steps.rolesTable.title"),
        content: t("onboarding.tour.steps.rolesTable.body"),
        route: "/roles",
        placement: "top",
        skipScroll: true,
      },
      // ── 12. Periods nav ───────────────────────────────────────────────────
      {
        target: '[data-tour="nav-periods"]',
        title: t("onboarding.tour.steps.periods.title"),
        content: t("onboarding.tour.steps.periods.body"),
        route: "/periods",
        placement: "right",
        skipScroll: true,
      },
      // ── 13. Periods — table ───────────────────────────────────────────────
      {
        target: '[data-tour="periods-table"]',
        title: t("onboarding.tour.steps.periodsTable.title"),
        content: t("onboarding.tour.steps.periodsTable.body"),
        route: "/periods",
        placement: "top",
        skipScroll: true,
      },
      // ── 14. Time nav ──────────────────────────────────────────────────────
      {
        target: '[data-tour="nav-time"]',
        title: t("onboarding.tour.steps.time.title"),
        content: t("onboarding.tour.steps.time.body"),
        route: "/time",
        placement: "right",
        skipScroll: true,
      },
      // ── 15. Time — grid ───────────────────────────────────────────────────
      {
        target: '[data-tour="time-grid"]',
        title: t("onboarding.tour.steps.timeGrid.title"),
        content: t("onboarding.tour.steps.timeGrid.body"),
        route: "/time",
        placement: "top",
        skipScroll: true,
      },
      // ── 16. Time — periods list ───────────────────────────────────────────
      {
        target: '[data-tour="time-periods-list"]',
        title: t("onboarding.tour.steps.timePeriodsList.title"),
        content: t("onboarding.tour.steps.timePeriodsList.body"),
        route: "/time",
        placement: "top",
        skipScroll: true,
      },
      // ── 17. Reports nav ───────────────────────────────────────────────────
      {
        target: '[data-tour="nav-reports"]',
        title: t("onboarding.tour.steps.reports.title"),
        content: t("onboarding.tour.steps.reports.body"),
        route: "/reports",
        placement: "right",
        skipScroll: true,
      },
      // ── 18. Reports — filters ─────────────────────────────────────────────
      {
        target: '[data-tour="reports-filters"]',
        title: t("onboarding.tour.steps.reportsFilters.title"),
        content: t("onboarding.tour.steps.reportsFilters.body"),
        route: "/reports",
        placement: "bottom",
        skipScroll: true,
      },
      // ── 19. Reports — table ───────────────────────────────────────────────
      {
        target: '[data-tour="reports-table"]',
        title: t("onboarding.tour.steps.reportsTable.title"),
        content: t("onboarding.tour.steps.reportsTable.body"),
        route: "/reports",
        placement: "top",
        skipScroll: true,
      },
      // ── 20. Approvals nav ─────────────────────────────────────────────────
      {
        target: '[data-tour="nav-approvals"]',
        title: t("onboarding.tour.steps.approvals.title"),
        content: t("onboarding.tour.steps.approvals.body"),
        route: "/approvals",
        placement: "right",
        skipScroll: true,
      },
      // ── 21. Approvals — status tabs ───────────────────────────────────────
      {
        target: '[data-tour="approvals-tabs"]',
        title: t("onboarding.tour.steps.approvalsTabs.title"),
        content: t("onboarding.tour.steps.approvalsTabs.body"),
        route: "/approvals",
        placement: "bottom",
        skipScroll: true,
      },
      // ── 22. Approvals — list ──────────────────────────────────────────────
      {
        target: '[data-tour="approvals-list"]',
        title: t("onboarding.tour.steps.approvalsList.title"),
        content: t("onboarding.tour.steps.approvalsList.body"),
        route: "/approvals",
        placement: "top",
        skipScroll: true,
      },
      // ── 23. Costing nav ───────────────────────────────────────────────────
      {
        target: '[data-tour="nav-costing"]',
        title: t("onboarding.tour.steps.costing.title"),
        content: t("onboarding.tour.steps.costing.body"),
        route: "/costing",
        placement: "right",
        skipScroll: true,
      },
      // ── 24. Costing — KPIs ────────────────────────────────────────────────
      {
        target: '[data-tour="costing-kpis"]',
        title: t("onboarding.tour.steps.costingKpis.title"),
        content: t("onboarding.tour.steps.costingKpis.body"),
        route: "/costing",
        placement: "bottom",
        skipScroll: true,
      },
      // ── 25. Costing — by department ───────────────────────────────────────
      {
        target: '[data-tour="costing-by-dept"]',
        title: t("onboarding.tour.steps.costingByDept.title"),
        content: t("onboarding.tour.steps.costingByDept.body"),
        route: "/costing",
        placement: "top",
        skipScroll: true,
      },
      // ── 26. Costing — by employee ─────────────────────────────────────────
      {
        target: '[data-tour="costing-by-employee"]',
        title: t("onboarding.tour.steps.costingByEmployee.title"),
        content: t("onboarding.tour.steps.costingByEmployee.body"),
        route: "/costing",
        placement: "top",
        skipScroll: true,
      },
      // ── 27. Audit nav ─────────────────────────────────────────────────────
      {
        target: '[data-tour="nav-audit"]',
        title: t("onboarding.tour.steps.audit.title"),
        content: t("onboarding.tour.steps.audit.body"),
        route: "/audit",
        placement: "right",
        skipScroll: true,
      },
      // ── 28. Audit — filters ───────────────────────────────────────────────
      {
        target: '[data-tour="audit-filters"]',
        title: t("onboarding.tour.steps.auditFilters.title"),
        content: t("onboarding.tour.steps.auditFilters.body"),
        route: "/audit",
        placement: "bottom",
        skipScroll: true,
      },
      // ── 29. Audit — table ─────────────────────────────────────────────────
      {
        target: '[data-tour="audit-table"]',
        title: t("onboarding.tour.steps.auditTable.title"),
        content: t("onboarding.tour.steps.auditTable.body"),
        route: "/audit",
        placement: "top",
        skipScroll: true,
      },
      // ── 30. Settings nav ──────────────────────────────────────────────────
      {
        target: '[data-tour="nav-settings"]',
        title: t("onboarding.tour.steps.settings.title"),
        content: t("onboarding.tour.steps.settings.body"),
        route: "/settings",
        placement: "right",
        skipScroll: true,
      },
      // ── 31. Settings — tabs ───────────────────────────────────────────────
      {
        target: '[data-tour="settings-tabs"]',
        title: t("onboarding.tour.steps.settingsTabs.title"),
        content: t("onboarding.tour.steps.settingsTabs.body"),
        route: "/settings",
        placement: "bottom",
        skipScroll: true,
      },
      // ── 32. Settings — Org tab ────────────────────────────────────────────
      {
        target: '[data-tour="settings-tab-org"]',
        title: t("onboarding.tour.steps.settingsOrg.title"),
        content: t("onboarding.tour.steps.settingsOrg.body"),
        route: "/settings",
        placement: "bottom",
        skipScroll: true,
      },
      // ── 33. Settings — Depts tab ──────────────────────────────────────────
      {
        target: '[data-tour="settings-tab-depts"]',
        title: t("onboarding.tour.steps.settingsDepts.title"),
        content: t("onboarding.tour.steps.settingsDepts.body"),
        route: "/settings",
        search: "?tab=depts",
        placement: "bottom",
        skipScroll: true,
      },
      // ── 34. Settings — Cost Rules tab ─────────────────────────────────────
      {
        target: '[data-tour="settings-tab-costrules"]',
        title: t("onboarding.tour.steps.settingsCostRules.title"),
        content: t("onboarding.tour.steps.settingsCostRules.body"),
        route: "/settings",
        search: "?tab=costRules",
        placement: "bottom",
        skipScroll: true,
      },
      // ── 35. Settings — Members tab ────────────────────────────────────────
      {
        target: '[data-tour="settings-tab-members"]',
        title: t("onboarding.tour.steps.settingsMembers.title"),
        content: t("onboarding.tour.steps.settingsMembers.body"),
        route: "/settings",
        search: "?tab=members",
        placement: "bottom",
        skipScroll: true,
      },
    ],
    [t],
  );

  const finish = useCallback(() => {
    stopTour();
    setStepIndex(0);
    markCompleted.mutate();
  }, [stopTour, markCompleted]);

  const goToStep = useCallback(
    (index: number) => {
      if (index < 0 || index >= steps.length) {
        finish();
        return;
      }
      const step = steps[index];
      const targetPath = step.route + (step.search ?? "");
      navigate(targetPath);
      // Small delay to let React render the target element before Joyride tries to find it
      pendingAdvance.current = window.setTimeout(() => {
        setStepIndex(index);
        pendingAdvance.current = null;
      }, 120);
    },
    [steps, navigate, finish],
  );

  const handleEvent = useCallback(
    (data: EventData) => {
      const { action, index, status, type } = data;

      if (status === STATUS.FINISHED || status === STATUS.SKIPPED) {
        finish();
        return;
      }

      if (type === EVENTS.STEP_AFTER || type === EVENTS.TARGET_NOT_FOUND) {
        const nextIndex = index + (action === ACTIONS.PREV ? -1 : 1);
        goToStep(nextIndex);
      }
    },
    [goToStep, finish],
  );

  useEffect(() => {
    if (shouldRun) {
      setStepIndex(0);
      navigate("/");
    }
  }, [shouldRun, navigate]);

  useEffect(() => {
    return () => {
      if (pendingAdvance.current !== null) {
        clearTimeout(pendingAdvance.current);
      }
    };
  }, []);

  if (!shouldRun) return null;

  return (
    <Joyride
      steps={steps}
      stepIndex={stepIndex}
      run={shouldRun}
      continuous
      onEvent={handleEvent}
      locale={{
        back: t("onboarding.tour.back"),
        next: t("onboarding.tour.next"),
        skip: t("onboarding.tour.skip"),
        last: t("onboarding.tour.finish"),
      }}
      options={{
        primaryColor: "var(--primary)",
        zIndex: 10000,
        spotlightPadding: 8,
        overlayColor: "rgba(0, 0, 0, 0.55)",
      }}
    />
  );
}
