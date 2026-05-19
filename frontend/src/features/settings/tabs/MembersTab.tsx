import { Plus } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Avatar, AvatarFallback } from "@/components/shadcn/avatar";
import { Badge } from "@/components/shadcn/badge";
import { Button } from "@/components/shadcn/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/shadcn/card";
import { useMembers } from "@/features/tenants/hooks";
import { formatDate } from "@/lib/format";

export function MembersTab({ tenantId }: { tenantId: number }) {
  const members = useMembers(tenantId);
  const { t } = useTranslation();
  const rows = members.data ?? [];

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <div>
          <CardTitle className="text-base">{t("settings.members.title")}</CardTitle>
          <CardDescription>{t("settings.members.subtitle")}</CardDescription>
        </div>
        <Button variant="outline" disabled>
          <Plus className="size-4 mr-1.5" />
          {t("settings.members.invite")}
        </Button>
      </CardHeader>
      <CardContent className="p-0">
        <div className="divide-y">
          {rows.map((m) => (
            <div key={m.id} className="flex items-center gap-3 px-6 py-3">
              <Avatar className="size-9">
                <AvatarFallback className="bg-primary/10 text-primary text-xs font-semibold">
                  #{m.user_id}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1 min-w-0">
                <div className="font-medium truncate">
                  {t("settings.members.userLabel", { id: m.user_id })}
                </div>
                <div className="text-xs text-muted-foreground truncate">
                  {t("settings.members.joined", { date: formatDate(m.joined_at) })}
                </div>
              </div>
              <Badge variant="outline" className="capitalize">
                {m.role}
              </Badge>
              {m.left_at && (
                <Badge variant="outline" className="text-muted-foreground">
                  {t("settings.members.inactive")}
                </Badge>
              )}
            </div>
          ))}
          {rows.length === 0 && (
            <div className="p-12 text-center text-sm text-muted-foreground">
              {members.isLoading ? t("settings.members.loading") : t("settings.members.empty")}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
