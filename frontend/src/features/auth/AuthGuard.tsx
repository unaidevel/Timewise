import { Navigate, Outlet, useLocation } from "react-router";
import { useAuthStore } from "./store";

export function AuthGuard() {
  const token = useAuthStore((s) => s.accessToken);
  const location = useLocation();

  if (!token) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <Outlet />;
}
