import { motion } from "framer-motion";
import { CheckCircle2, Clock, TrendingUp, Users } from "lucide-react";

export function AuthHero() {
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
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <h2 className="text-4xl font-semibold tracking-tight leading-tight">
            Personas, tiempo y coste — en un solo lugar.
          </h2>
          <p className="mt-4 text-primary-foreground/80 leading-relaxed">
            TimeWise reúne a tu equipo, sus horas y el coste laboral en una única fuente de verdad.
          </p>
        </motion.div>

        <div className="mt-10 grid grid-cols-2 gap-3">
          {[
            { icon: Users, label: "Personas", value: "284" },
            { icon: Clock, label: "Horas este periodo", value: "11.420" },
            { icon: CheckCircle2, label: "Aprobaciones", value: "98%" },
            { icon: TrendingUp, label: "Variación coste", value: "−2.4%" },
          ].map((kpi, i) => (
            <motion.div
              key={kpi.label}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 + i * 0.07 }}
              className="rounded-xl border border-white/15 bg-white/5 backdrop-blur-sm p-4"
            >
              <kpi.icon className="size-4 opacity-80" />
              <div className="mt-3 text-2xl font-semibold tracking-tight">{kpi.value}</div>
              <div className="text-xs opacity-70">{kpi.label}</div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}
