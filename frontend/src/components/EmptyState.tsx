import { Sparkles } from "lucide-react";
import type { ComponentType, ReactNode } from "react";
import { Card, CardContent } from "@/components/shadcn/card";

type Props = {
  title: string;
  description: string;
  icon?: ComponentType<{ className?: string }>;
  action?: ReactNode;
};

export function EmptyState({ title, description, icon: Icon = Sparkles, action }: Props) {
  return (
    <Card className="border-dashed">
      <CardContent className="p-12 text-center">
        <div className="mx-auto size-12 rounded-full bg-primary/10 grid place-items-center mb-4">
          <Icon className="size-5 text-primary" />
        </div>
        <h3 className="font-semibold text-lg">{title}</h3>
        <p className="text-sm text-muted-foreground mt-1.5 max-w-md mx-auto">{description}</p>
        {action && <div className="mt-6">{action}</div>}
      </CardContent>
    </Card>
  );
}
