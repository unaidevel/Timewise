import { useCallback, useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";
import {
  ACTIONS,
  type EventData,
  EVENTS,
  Joyride,
  STATUS,
  type Step,
} from "react-joyride";
import { useMarkTourCompleted } from "@/features/auth/hooks";
import { useTourStore } from "@/features/onboarding/store";

type TourStep = Step & { route: string };

export function TourRunner() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const shouldRun = useTourStore((s) => s.shouldRun);
  const stopTour = useTourStore((s) => s.stopTour);
  const markCompleted = useMarkTourCompleted();
  const [stepIndex, setStepIndex] = useState(0);

  const steps: TourStep[] = useMemo(
    () => [
      {
        target: '[data-tour="nav-home"]',
        title: t("onboarding.tour.steps.home.title"),
        content: t("onboarding.tour.steps.home.body"),
        route: "/",
      },
      {
        target: '[data-tour="nav-employees"]',
        title: t("onboarding.tour.steps.employees.title"),
        content: t("onboarding.tour.steps.employees.body"),
        route: "/employees",
      },
      {
        target: '[data-tour="nav-periods"]',
        title: t("onboarding.tour.steps.periods.title"),
        content: t("onboarding.tour.steps.periods.body"),
        route: "/periods",
      },
      {
        target: '[data-tour="nav-reports"]',
        title: t("onboarding.tour.steps.reports.title"),
        content: t("onboarding.tour.steps.reports.body"),
        route: "/reports",
      },
      {
        target: '[data-tour="nav-approvals"]',
        title: t("onboarding.tour.steps.approvals.title"),
        content: t("onboarding.tour.steps.approvals.body"),
        route: "/approvals",
      },
      {
        target: '[data-tour="nav-settings"]',
        title: t("onboarding.tour.steps.settings.title"),
        content: t("onboarding.tour.steps.settings.body"),
        route: "/settings",
      },
    ],
    [t],
  );

  const finish = useCallback(() => {
    stopTour();
    setStepIndex(0);
    markCompleted.mutate();
  }, [stopTour, markCompleted]);

  const handleEvent = useCallback(
    (data: EventData) => {
      const { action, index, status, type } = data;

      if (status === STATUS.FINISHED || status === STATUS.SKIPPED) {
        finish();
        return;
      }

      if (type === EVENTS.STEP_AFTER || type === EVENTS.TARGET_NOT_FOUND) {
        const nextIndex = index + (action === ACTIONS.PREV ? -1 : 1);
        if (nextIndex >= 0 && nextIndex < steps.length) {
          navigate(steps[nextIndex].route);
          setStepIndex(nextIndex);
        }
      }
    },
    [navigate, steps, finish],
  );

  useEffect(() => {
    if (shouldRun) {
      setStepIndex(0);
      navigate("/");
    }
  }, [shouldRun, navigate]);

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
      }}
    />
  );
}
