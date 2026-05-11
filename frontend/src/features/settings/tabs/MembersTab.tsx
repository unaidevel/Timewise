import { Plus } from "lucide-react";
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
  const rows = members.data ?? [];

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <div>
          <CardTitle className="text-base">Miembros y roles</CardTitle>
          <CardDescription>Personas con acceso a este workspace.</CardDescription>
        </div>
        <Button variant="outline" disabled>
          <Plus className="size-4 mr-1.5" />
          Invitar miembro
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
                <div className="font-medium truncate">Usuario #{m.user_id}</div>
                <div className="text-xs text-muted-foreground truncate">
                  Se unió {formatDate(m.joined_at)}
                </div>
              </div>
              <Badge variant="outline" className="capitalize">
                {m.role}
              </Badge>
              {m.left_at && (
                <Badge variant="outline" className="text-muted-foreground">
                  Inactivo
                </Badge>
              )}
            </div>
          ))}
          {rows.length === 0 && (
            <div className="p-12 text-center text-sm text-muted-foreground">
              {members.isLoading ? "Cargando…" : "Aún no hay miembros."}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
