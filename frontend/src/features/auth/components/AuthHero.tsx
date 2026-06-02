import { m } from "framer-motion";
import { CheckCircle2, Clock, TrendingUp, Users } from "lucide-react";
import { useTranslation } from "react-i18next";

export function AuthHero() {
  const { t } = useTranslation();
  const kpis = [
    { icon: Users, label: t("auth.hero.kpi.people"), value: "284" },
    { icon: Clock, label: t("auth.hero.kpi.hoursPeriod"), value: "11.420" },
    { icon: CheckCircle2, label: t("auth.hero.kpi.approvals"), value: "98%" },
    { icon: TrendingUp, label: t("auth.hero.kpi.costVariance"), value: "−2.4%" },
  ];

  return (
    <div className="hidden lg:flex relative overflow-hidden bg-gradient-to-br from-primary via-primary to-[oklch(0.3_0.08_165)] items-center justify-center p-12">
      <div
        className="absolute inset-0 opacity-20"
        style={{ backgroundImage: "radial-gradient(circle at 30% 20%, white, transparent 50%)" }}
      />
      <div
        className="absolute inset-0 opacity-10"
        style={{ backgroundImage: "radial-gradient(circle at 80% 70%, white, transparent 40%)" }}
      />

      <div className="relative max-w-md text-primary-foreground">
        <m.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <h2 className="text-4xl font-semibold tracking-tight leading-tight">
            {t("auth.hero.title")}
          </h2>
          <p className="mt-4 text-primary-foreground/80 leading-relaxed">
            {t("auth.hero.subtitle")}
          </p>
        </m.div>

        <div className="mt-10 grid grid-cols-2 gap-3">
          {kpis.map((kpi, i) => (
            <m.div
              key={kpi.label}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 + i * 0.07 }}
              className="rounded-xl border border-white/15 bg-white/5 backdrop-blur-sm p-4"
            >
              <kpi.icon className="size-4 opacity-80" />
              <div className="mt-3 text-2xl font-semibold tracking-tight">{kpi.value}</div>
              <div className="text-xs opacity-70">{kpi.label}</div>
            </m.div>
          ))}
        </div>
      </div>
    </div>
  );
}
