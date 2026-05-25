import { createBrowserRouter, Navigate } from "react-router";
import ApprovalsPage from "@/features/approvals/pages/ApprovalsPage";
import AuditPage from "@/features/audit/pages/AuditPage";
import { AuthGuard } from "@/features/auth/AuthGuard";
import LoginPage from "@/features/auth/pages/LoginPage";
import RegisterPage from "@/features/auth/pages/RegisterPage";
import CostingPage from "@/features/costing/pages/CostingPage";
import CostingRuleDetailPage from "@/features/costing-rules/pages/CostingRuleDetailPage";
import HomeRouter from "@/features/dashboard/pages/HomeRouter";
import DepartmentsPage from "@/features/departments/pages/DepartmentsPage";
import EmployeeDetailPage from "@/features/employees/pages/EmployeeDetailPage";
import EmployeesPage from "@/features/employees/pages/EmployeesPage";
import PeriodDetailPage from "@/features/periods/pages/PeriodDetailPage";
import PeriodsPage from "@/features/periods/pages/PeriodsPage";
import RolesPage from "@/features/roles/pages/RolesPage";
import SettingsPage from "@/features/settings/pages/SettingsPage";
import OnboardingPage from "@/features/tenants/pages/OnboardingPage";
import TimeReportDetailPage from "@/features/time-reports/pages/TimeReportDetailPage";
import TimeReportsPage from "@/features/time-reports/pages/TimeReportsPage";
import TimePage from "@/features/time-tracking/pages/TimePage";
import { Layout } from "./Layout";

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  { path: "/register", element: <RegisterPage /> },
  {
    element: <AuthGuard />,
    children: [
      {
        element: <Layout />,
        children: [
          { path: "/", element: <HomeRouter /> },
          { path: "/onboarding", element: <OnboardingPage /> },
          { path: "/employees", element: <EmployeesPage /> },
          { path: "/employees/:id", element: <EmployeeDetailPage /> },
          { path: "/departments", element: <DepartmentsPage /> },
          { path: "/roles", element: <RolesPage /> },
          { path: "/periods", element: <PeriodsPage /> },
          { path: "/periods/:id", element: <PeriodDetailPage /> },
          { path: "/reports", element: <TimeReportsPage /> },
          { path: "/reports/:id", element: <TimeReportDetailPage /> },
          { path: "/approvals", element: <ApprovalsPage /> },
          { path: "/costing-rules/:id", element: <CostingRuleDetailPage /> },
          { path: "/costing", element: <CostingPage /> },
          { path: "/settings", element: <SettingsPage /> },
          { path: "/time", element: <TimePage /> },
          { path: "/audit", element: <AuditPage /> },
        ],
      },
    ],
  },
  { path: "*", element: <Navigate to="/" replace /> },
]);
