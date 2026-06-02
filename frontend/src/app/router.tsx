import { lazy, Suspense } from "react";
import { createBrowserRouter, Navigate } from "react-router";
import { AuthGuard } from "@/features/auth/AuthGuard";
import { Layout } from "./Layout";

// Pages are lazy-loaded so heavy per-page dependencies (e.g. recharts on the
// dashboard and costing views) are split out of the initial bundle.
const LoginPage = lazy(() => import("@/features/auth/pages/LoginPage"));
const RegisterPage = lazy(() => import("@/features/auth/pages/RegisterPage"));
const OnboardingPage = lazy(() => import("@/features/tenants/pages/OnboardingPage"));
const HomeRouter = lazy(() => import("@/features/dashboard/pages/HomeRouter"));
const EmployeesPage = lazy(() => import("@/features/employees/pages/EmployeesPage"));
const EmployeeDetailPage = lazy(() => import("@/features/employees/pages/EmployeeDetailPage"));
const DepartmentsPage = lazy(() => import("@/features/departments/pages/DepartmentsPage"));
const RolesPage = lazy(() => import("@/features/roles/pages/RolesPage"));
const PeriodsPage = lazy(() => import("@/features/periods/pages/PeriodsPage"));
const PeriodDetailPage = lazy(() => import("@/features/periods/pages/PeriodDetailPage"));
const TimeReportsPage = lazy(() => import("@/features/time-reports/pages/TimeReportsPage"));
const TimeReportDetailPage = lazy(() => import("@/features/time-reports/pages/TimeReportDetailPage"));
const ApprovalsPage = lazy(() => import("@/features/approvals/pages/ApprovalsPage"));
const CostingRuleDetailPage = lazy(
  () => import("@/features/costing-rules/pages/CostingRuleDetailPage"),
);
const CostingPage = lazy(() => import("@/features/costing/pages/CostingPage"));
const SettingsPage = lazy(() => import("@/features/settings/pages/SettingsPage"));
const ProfilePage = lazy(() => import("@/features/profile/pages/ProfilePage"));
const TimePage = lazy(() => import("@/features/time-tracking/pages/TimePage"));
const AuditPage = lazy(() => import("@/features/audit/pages/AuditPage"));

function lazyPage(element: React.ReactNode) {
  return <Suspense fallback={<div className="h-full w-full animate-pulse" />}>{element}</Suspense>;
}

export const router = createBrowserRouter([
  { path: "/login", element: lazyPage(<LoginPage />) },
  { path: "/register", element: lazyPage(<RegisterPage />) },
  {
    element: <AuthGuard />,
    children: [
      { path: "/onboarding", element: lazyPage(<OnboardingPage />) },
      {
        element: <Layout />,
        children: [
          { path: "/", element: lazyPage(<HomeRouter />) },
          { path: "/employees", element: lazyPage(<EmployeesPage />) },
          { path: "/employees/:id", element: lazyPage(<EmployeeDetailPage />) },
          { path: "/departments", element: lazyPage(<DepartmentsPage />) },
          { path: "/roles", element: lazyPage(<RolesPage />) },
          { path: "/periods", element: lazyPage(<PeriodsPage />) },
          { path: "/periods/:id", element: lazyPage(<PeriodDetailPage />) },
          { path: "/reports", element: lazyPage(<TimeReportsPage />) },
          { path: "/reports/:id", element: lazyPage(<TimeReportDetailPage />) },
          { path: "/approvals", element: lazyPage(<ApprovalsPage />) },
          { path: "/costing-rules/:id", element: lazyPage(<CostingRuleDetailPage />) },
          { path: "/costing", element: lazyPage(<CostingPage />) },
          { path: "/settings", element: lazyPage(<SettingsPage />) },
          { path: "/profile", element: lazyPage(<ProfilePage />) },
          { path: "/time", element: lazyPage(<TimePage />) },
          { path: "/audit", element: lazyPage(<AuditPage />) },
        ],
      },
    ],
  },
  { path: "*", element: <Navigate to="/" replace /> },
]);
