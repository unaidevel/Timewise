import { Building2, Clock, Layers, Users } from "lucide-react";
import { Link } from "react-router";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/shadcn/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/shadcn/tabs";
import { DepartmentsTab } from "@/features/settings/tabs/DepartmentsTab";
import { MembersTab } from "@/features/settings/tabs/MembersTab";
import { OrganizationTab } from "@/features/settings/tabs/OrganizationTab";
import { OvertimeTab } from "@/features/settings/tabs/OvertimeTab";
import { useCurrentTenantId } from "@/features/tenants/hooks";

export default function SettingsPage() {
  const tenantId = useCurrentTenantId();
  if (tenantId == null) return <NoTenantState />;

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight">Ajustes</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Gestiona el workspace, departamentos, reglas de horas extra y miembros.
        </p>
      </header>

      <Tabs defaultValue="org">
        <TabsList>
          <TabsTrigger value="org">
            <Building2 className="size-4 mr-1.5" />
            Organización
          </TabsTrigger>
          <TabsTrigger value="depts">
            <Layers className="size-4 mr-1.5" />
            Departamentos
          </TabsTrigger>
          <TabsTrigger value="ot">
            <Clock className="size-4 mr-1.5" />
            Horas extra
          </TabsTrigger>
          <TabsTrigger value="members">
            <Users className="size-4 mr-1.5" />
            Miembros
          </TabsTrigger>
        </TabsList>

        <TabsContent value="org" className="mt-6">
          <OrganizationTab tenantId={tenantId} />
        </TabsContent>
        <TabsContent value="depts" className="mt-6">
          <DepartmentsTab tenantId={tenantId} />
        </TabsContent>
        <TabsContent value="ot" className="mt-6">
          <OvertimeTab tenantId={tenantId} />
        </TabsContent>
        <TabsContent value="members" className="mt-6">
          <MembersTab tenantId={tenantId} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

function NoTenantState() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Selecciona un workspace</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground mb-4">
          Necesitas crear o seleccionar una organización para ver los ajustes.
        </p>
        <Link to="/onboarding" className="text-sm font-medium text-primary hover:underline">
          Crear primera organización →
        </Link>
      </CardContent>
    </Card>
  );
}
