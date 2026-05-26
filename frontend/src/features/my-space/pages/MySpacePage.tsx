import { motion } from "framer-motion";
import { Calendar, Clock, Coffee, Play, Square, TrendingUp } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { LiveClock, getHourInTimezone, useNow } from "@/components/LiveClock";
import { Badge } from "@/components/shadcn/badge";
import { Button } from "@/components/shadcn/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/shadcn/card";
import { Progress } from "@/components/shadcn/progress";
import { RecentActivity } from "@/features/activity/RecentActivity";
import { useAuthStore } from "@/features/auth/store";
import { useCurrentTenantId, useOrganizationProfile } from "@/features/tenants/hooks";

// Placeholder figures — backend doesn't yet expose per-user PTO / weekly summaries.
const WEEK_HOURS = 28.5;
const WEEK_TARGET = 40;
const PTO_USED = 6;
const PTO_TOTAL = 25;
const LAST_MONTH_HOURS = 152;

export default function MySpacePage() {
  const tenantId = useCurrentTenantId();
  const user = useAuthStore((s) => s.user);
  const { t, i18n } = useTranslation();
  const profile = useOrganizationProfile(tenantId);
  const locale = i18n.resolvedLanguage === "es" ? "es-ES" : "en-US";
  const timezone = user?.timezone || profile.data?.timezone || undefined;

  const now = useNow();
  const [clockedInAt, setClockedInAt] = useState<Date | null>(null);
  const [onBreak, setOnBreak] = useState(false);

  const firstName = user?.full_name?.split(" ")[0] ?? t("dashboard.greetingFallback");
  const hour = getHourInTimezone(now, timezone);
  const greeting =
    hour < 12
      ? t("dashboard.greetingMorning")
      : hour < 18
        ? t("dashboard.greetingAfternoon")
        : t("dashboard.greetingEvening");

  const elapsedMs = clockedInAt ? now.getTime() - clockedInAt.getTime() : 0;
  const eh = Math.floor(elapsedMs / 3600000);
  const em = Math.floor((elapsedMs % 3600000) / 60000);
  const es = Math.floor((elapsedMs % 60000) / 1000);
  const elapsed = `${String(eh).padStart(2, "0")}:${String(em).padStart(2, "0")}:${String(es).padStart(2, "0")}`;

  const headerDate = new Intl.DateTimeFormat(locale, {
    weekday: "long",
    month: "long",
    day: "numeric",
    timeZone: timezone,
  }).format(now);

  const upcoming = [
    {
      title: t("mySpace.upcoming.standup"),
      when: t("mySpace.upcoming.standupWhen"),
      tag: t("mySpace.upcoming.tagMeeting"),
    },
    {
      title: t("mySpace.upcoming.oneOnOne"),
      when: t("mySpace.upcoming.oneOnOneWhen"),
      tag: t("mySpace.upcoming.tagOneOnOne"),
    },
    {
      title: t("mySpace.upcoming.sprintReview"),
      when: t("mySpace.upcoming.sprintReviewWhen"),
      tag: t("mySpace.upcoming.tagMeeting"),
    },
  ];

  return (
    <div className="space-y-8">
      <header>
        <p className="text-sm text-muted-foreground capitalize">{headerDate}</p>
        <h1 className="text-3xl font-semibold tracking-tight mt-1">
          {greeting}, {firstName}
        </h1>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.4 }}
        >
          <LiveClock
            className="[&>div:first-child]:text-7xl lg:[&>div:first-child]:text-8xl"
            locale={locale}
            timezone={timezone}
            showSeconds
            showDate={false}
          />
          <div className="mt-4 flex items-center gap-2">
            <span
              className={
                clockedInAt
                  ? "size-2 rounded-full bg-success animate-pulse"
                  : "size-2 rounded-full bg-muted-foreground/40"
              }
            />
            <span className="text-sm text-muted-foreground">
              {clockedInAt
                ? onBreak
                  ? t("mySpace.status.onBreak")
                  : t("mySpace.status.working", { elapsed })
                : t("mySpace.status.notClocked")}
            </span>
          </div>
        </motion.div>

        <Card className="overflow-hidden border bg-gradient-to-br from-card via-card to-primary/5">
          <CardContent className="p-6 lg:p-8">
            <div className="flex flex-col items-stretch gap-3">
              {!clockedInAt ? (
                <Button
                  size="lg"
                  className="h-16 text-base gap-2"
                  onClick={() => setClockedInAt(new Date())}
                >
                  <Play className="size-5" /> {t("mySpace.actions.clockIn")}
                </Button>
              ) : (
                <>
                  <Button
                    size="lg"
                    variant="destructive"
                    className="h-16 text-base gap-2"
                    onClick={() => {
                      setClockedInAt(null);
                      setOnBreak(false);
                    }}
                  >
                    <Square className="size-5" /> {t("mySpace.actions.clockOut")}
                  </Button>
                  <Button
                    size="lg"
                    variant="outline"
                    className="h-12 gap-2"
                    onClick={() => setOnBreak((b) => !b)}
                  >
                    <Coffee className="size-4" />{" "}
                    {onBreak ? t("mySpace.actions.endBreak") : t("mySpace.actions.startBreak")}
                  </Button>
                </>
              )}
              <p className="text-xs text-muted-foreground text-center">
                {t("mySpace.actions.hint")}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm text-muted-foreground font-medium">
                {t("mySpace.week.title")}
              </CardTitle>
              <Clock className="size-4 text-muted-foreground" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-semibold tracking-tight">
              {WEEK_HOURS}
              <span className="text-base text-muted-foreground font-normal"> / {WEEK_TARGET}h</span>
            </div>
            <Progress value={(WEEK_HOURS / WEEK_TARGET) * 100} className="mt-3 h-1.5" />
            <p className="text-xs text-muted-foreground mt-2">
              {t("mySpace.week.remaining", {
                hours: (WEEK_TARGET - WEEK_HOURS).toFixed(1),
              })}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm text-muted-foreground font-medium">
                {t("mySpace.pto.title")}
              </CardTitle>
              <Calendar className="size-4 text-muted-foreground" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-semibold tracking-tight">
              {PTO_TOTAL - PTO_USED}
              <span className="text-base text-muted-foreground font-normal">
                {" "}
                {t("mySpace.pto.daysLeft")}
              </span>
            </div>
            <Progress value={(PTO_USED / PTO_TOTAL) * 100} className="mt-3 h-1.5" />
            <p className="text-xs text-muted-foreground mt-2">
              {t("mySpace.pto.usedThisYear", { used: PTO_USED, total: PTO_TOTAL })}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm text-muted-foreground font-medium">
                {t("mySpace.lastMonth.title")}
              </CardTitle>
              <TrendingUp className="size-4 text-muted-foreground" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-semibold tracking-tight">{LAST_MONTH_HOURS}h</div>
            <Badge
              variant="secondary"
              className="mt-3 bg-success/15 text-success hover:bg-success/15 font-normal"
            >
              {t("mySpace.lastMonth.approved")}
            </Badge>
          </CardContent>
        </Card>
      </section>

      <section>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{t("mySpace.activity.title")}</CardTitle>
            <p className="text-xs text-muted-foreground">{t("mySpace.activity.subtitle")}</p>
          </CardHeader>
          <CardContent>
            <RecentActivity tenantId={tenantId} actorId={user?.id ?? null} />
          </CardContent>
        </Card>
      </section>

      <section>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{t("mySpace.upcoming.title")}</CardTitle>
            <p className="text-xs text-muted-foreground">{t("mySpace.upcoming.subtitle")}</p>
          </CardHeader>
          <CardContent className="space-y-2">
            {upcoming.map((u) => (
              <div
                key={u.title}
                className="flex items-center justify-between rounded-lg border p-3 hover:bg-muted/40 transition"
              >
                <div>
                  <div className="text-sm font-medium">{u.title}</div>
                  <div className="text-xs text-muted-foreground mt-0.5">{u.when}</div>
                </div>
                <Badge variant="outline" className="font-normal">
                  {u.tag}
                </Badge>
              </div>
            ))}
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
