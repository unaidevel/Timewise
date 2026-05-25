import MySpacePage from "@/features/my-space/pages/MySpacePage";
import { useCurrentTenantId, useIsTenantAdmin, useMembers } from "@/features/tenants/hooks";
import HomePage from "./HomePage";

export default function HomeRouter() {
  const tenantId = useCurrentTenantId();
  const members = useMembers(tenantId);
  const isAdmin = useIsTenantAdmin(tenantId);

  if (tenantId == null) return <HomePage />;
  if (!members.data) return null;
  return isAdmin ? <HomePage /> : <MySpacePage />;
}
