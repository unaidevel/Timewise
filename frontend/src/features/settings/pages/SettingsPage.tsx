import { Building2, Calculator, Layers, Users } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Link, useSearchParams } from "react-router";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/shadcn/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/shadcn/tabs";
import { CostRulesTab } from "@/features/settings/tabs/CostRulesTab";
import { DepartmentsTab } from "@/features/settings/tabs/DepartmentsTab";
import { MembersTab } from "@/features/settings/tabs/MembersTab";
import { OrganizationTab } from "@/features/settings/tabs/OrganizationTab";
import { useCurrentTenantId } from "@/features/tenants/hooks";

const TABS = ["org", "depts", "costRules", "members"] as const;
type TabValue = (typeof TABS)[number];

export default function SettingsPage() {
  const tenantId = useCurrentTenantId();
  const { t } = useTranslation();
  const [searchParams, setSearchParams] = useSearchParams();
  if (tenantId == null) return <NoTenantState />;

  const tabParam = searchParams.get("tab");
  const tab: TabValue = (TABS as readonly string[]).includes(tabParam ?? "")
    ? (tabParam as TabValue)
    : "org";

  function onTabChange(value: string) {
    const next = new URLSearchParams(searchParams);
    if (value === "org") next.delete("tab");
    else next.set("tab", value);
    if (value !== "members") next.delete("invite");
    setSearchParams(next, { replace: true });
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight">{t("settings.title")}</h1>
        <p className="text-sm text-muted-foreground mt-1">{t("settings.subtitle")}</p>
      </header>

      <Tabs value={tab} onValueChange={onTabChange}>
        <TabsList data-tour="settings-tabs">
          <TabsTrigger value="org" data-tour="settings-tab-org">
            <Building2 className="size-4 mr-1.5" />
            {t("settings.tabs.org")}
          </TabsTrigger>
          <TabsTrigger value="depts">
            <Layers className="size-4 mr-1.5" />
            {t("settings.tabs.depts")}
          </TabsTrigger>
          <TabsTrigger value="costRules">
            <Calculator className="size-4 mr-1.5" />
            {t("settings.tabs.costRules")}
          </TabsTrigger>
          <TabsTrigger value="members" data-tour="settings-tab-members">
            <Users className="size-4 mr-1.5" />
            {t("settings.tabs.members")}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="org" className="mt-6">
          <OrganizationTab tenantId={tenantId} />
        </TabsContent>
        <TabsContent value="depts" className="mt-6">
          <DepartmentsTab tenantId={tenantId} />
        </TabsContent>
        <TabsContent value="costRules" className="mt-6">
          <CostRulesTab tenantId={tenantId} />
        </TabsContent>
        <TabsContent value="members" className="mt-6">
          <MembersTab tenantId={tenantId} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

function NoTenantState() {
  const { t } = useTranslation();
  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("settings.noTenant.title")}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground mb-4">{t("settings.noTenant.description")}</p>
        <Link to="/onboarding" className="text-sm font-medium text-primary hover:underline">
          {t("settings.noTenant.cta")}
        </Link>
      </CardContent>
    </Card>
  );
}
