import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/shadcn/dialog";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyRow, Table, Td, Th } from "@/components/ui/Table";
import { useCurrentTenantId } from "@/features/tenants/hooks";
import { formatDate } from "@/lib/format";
import { useCreateRole, useDeactivateRole, useRoles } from "../hooks";

export default function RolesPage() {
  const tenantId = useCurrentTenantId();
  const { data, isLoading } = useRoles(tenantId);
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);

  return (
    <Card>
      <CardHeader
        title={t("workforce.roles.title")}
        description={t("workforce.roles.subtitle")}
        action={<Button onClick={() => setOpen(true)}>{t("workforce.roles.new")}</Button>}
      />
      <CardBody className="p-0">
        {isLoading ? (
          <div className="flex justify-center p-8">
            <Spinner />
          </div>
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>{t("workforce.roles.columns.name")}</Th>
                <Th>{t("workforce.roles.columns.status")}</Th>
                <Th>{t("workforce.roles.columns.created")}</Th>
                <Th></Th>
              </tr>
            </thead>
            <tbody>
              {(!data || data.length === 0) && (
                <EmptyRow colSpan={4} message={t("workforce.roles.empty")} />
              )}
              {data?.map((r) => (
                <RoleRow
                  key={r.id}
                  id={r.id}
                  name={r.name}
                  isActive={r.is_active}
                  createdAt={r.created_at}
                />
              ))}
            </tbody>
          </Table>
        )}
      </CardBody>

      <CreateRoleModal open={open} onClose={() => setOpen(false)} />
    </Card>
  );
}

function RoleRow({
  id,
  name,
  isActive,
  createdAt,
}: {
  id: number;
  name: string;
  isActive: boolean;
  createdAt: string;
}) {
  const tenantId = useCurrentTenantId();
  const deactivate = useDeactivateRole(tenantId);
  const { t } = useTranslation();
  return (
    <tr>
      <Td className="font-medium">{name}</Td>
      <Td>
        <Badge status={isActive ? "active" : "inactive"}>
          {isActive ? t("common.active") : t("common.inactive")}
        </Badge>
      </Td>
      <Td>{formatDate(createdAt)}</Td>
      <Td className="text-right">
        {isActive && (
          <Button
            variant="ghost"
            onClick={() => deactivate.mutate(id)}
            disabled={deactivate.isPending}
          >
            {t("common.deactivate")}
          </Button>
        )}
      </Td>
    </tr>
  );
}

function CreateRoleModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const tenantId = useCurrentTenantId();
  const create = useCreateRole(tenantId);
  const { t } = useTranslation();
  const [name, setName] = useState("");

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    create.mutate(
      { name },
      {
        onSuccess: () => {
          setName("");
          onClose();
        },
      },
    );
  }

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{t("workforce.roles.createTitle")}</DialogTitle>
        </DialogHeader>
        <form onSubmit={onSubmit} className="space-y-4">
          <Input
            label={t("common.name")}
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={onClose}>
              {t("common.cancel")}
            </Button>
            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? t("common.creating") : t("common.create")}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
