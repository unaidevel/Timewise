import { AnimatePresence, motion } from "framer-motion";
import {
  BarChart2,
  Calculator,
  CalendarRange,
  Check,
  CheckSquare,
  ChevronsUpDown,
  Clock,
  Compass,
  FolderKanban,
  LayoutDashboard,
  Leaf,
  LogOut,
  Moon,
  PanelLeftClose,
  PanelLeftOpen,
  ScrollText,
  Search,
  Settings,
  Sun,
  Tag,
  User,
  Users,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, NavLink, Outlet, useLocation } from "react-router";
import { CommandPalette, useCommandPalette } from "@/components/CommandPalette";
import { Avatar, AvatarFallback } from "@/components/shadcn/avatar";
import { Button } from "@/components/shadcn/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/shadcn/dropdown-menu";
import { useLogout } from "@/features/auth/hooks";
import { useAuthStore } from "@/features/auth/store";
import { DemoDataBanner } from "@/features/onboarding/components/DemoDataBanner";
import { TourRunner } from "@/features/onboarding/components/TourRunner";
import { useTourStore } from "@/features/onboarding/store";
import { useIsTenantAdmin, useTenants } from "@/features/tenants/hooks";
import { useTenantStore } from "@/features/tenants/store";
import { useTheme } from "@/hooks/use-theme";
import { cn } from "@/lib/utils";

type NavItem = {
  to: string;
  label: string;
  icon: typeof LayoutDashboard;
  end?: boolean;
  adminOnly?: boolean;
  tourId?: string;
};

type NavGroup = {
  label?: string; // undefined → no header (standalone item or first group)
  items: NavItem[];
};

export function Layout() {
  const location = useLocation();
  const { theme, toggle } = useTheme();
  const { i18n, t } = useTranslation();
  const user = useAuthStore((s) => s.user);
  const logout = useLogout();
  const { data: tenants = [] } = useTenants();
  const { currentTenantId, setCurrentTenantId } = useTenantStore();
  const currentTenant = tenants.find((t) => t.id === currentTenantId) ?? tenants[0] ?? null;
  const isAdmin = useIsTenantAdmin(currentTenantId);
  const startTour = useTourStore((s) => s.startTour);
  const navGroups: NavGroup[] = [
    {
      items: [
        { to: "/", label: t("layout.nav.home"), icon: LayoutDashboard, end: true, tourId: "nav-home" },
      ],
    },
    {
      label: t("layout.nav.groups.people"),
      items: [
        { to: "/employees", label: t("layout.nav.employees"), icon: Users, adminOnly: true, tourId: "nav-employees" },
        { to: "/departments", label: t("layout.nav.departments"), icon: FolderKanban, adminOnly: true, tourId: "nav-departments" },
        { to: "/roles", label: t("layout.nav.roles"), icon: Tag, adminOnly: true, tourId: "nav-roles" },
      ],
    },
    {
      label: t("layout.nav.groups.time"),
      items: [
        { to: "/periods", label: t("layout.nav.periods"), icon: CalendarRange, adminOnly: true, tourId: "nav-periods" },
        { to: "/time", label: t("layout.nav.time"), icon: Clock, tourId: "nav-time" },
        { to: "/reports", label: t("layout.nav.reports"), icon: BarChart2, tourId: "nav-reports" },
      ],
    },
    {
      label: t("layout.nav.groups.finance"),
      items: [
        { to: "/approvals", label: t("layout.nav.approvals"), icon: CheckSquare, tourId: "nav-approvals" },
        { to: "/costing", label: t("layout.nav.costing"), icon: Calculator, adminOnly: true, tourId: "nav-costing" },
      ],
    },
    {
      label: t("layout.nav.groups.admin"),
      items: [
        { to: "/audit", label: t("layout.nav.audit"), icon: ScrollText, adminOnly: true, tourId: "nav-audit" },
        { to: "/settings", label: t("layout.nav.settings"), icon: Settings, adminOnly: true, tourId: "nav-settings" },
      ],
    },
  ];
  // Filter admin-only items; drop groups that end up empty after filtering.
  const visibleGroups = navGroups
    .map((g) => ({ ...g, items: g.items.filter((item) => !item.adminOnly || isAdmin) }))
    .filter((g) => g.items.length > 0);
  const SIDEBAR_MIN = 180;
  const SIDEBAR_MAX = 320;
  const SIDEBAR_COLLAPSED = 68;
  const COLLAPSE_THRESHOLD = 120; // drag below this → snap to icon-only

  const [sidebarWidth, setSidebarWidth] = useState(244);
  const collapsed = sidebarWidth === SIDEBAR_COLLAPSED;
  const isDragging = useRef(false);

  const toggleCollapse = useCallback(() => {
    setSidebarWidth((w) => (w === SIDEBAR_COLLAPSED ? 244 : SIDEBAR_COLLAPSED));
  }, []);

  const onDragHandleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    isDragging.current = true;
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";

    const onMouseMove = (ev: MouseEvent) => {
      if (!isDragging.current) return;
      const newWidth = ev.clientX;
      if (newWidth < COLLAPSE_THRESHOLD) {
        setSidebarWidth(SIDEBAR_COLLAPSED);
      } else {
        setSidebarWidth(Math.min(SIDEBAR_MAX, Math.max(SIDEBAR_MIN, newWidth)));
      }
    };

    const onMouseUp = () => {
      isDragging.current = false;
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
    };

    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
  }, []);

  const palette = useCommandPalette();

  useEffect(() => {
    if (currentTenantId == null && tenants.length > 0) {
      setCurrentTenantId(tenants[0].id);
    }
  }, [currentTenantId, tenants, setCurrentTenantId]);

  const initials =
    user?.full_name
      ?.split(" ")
      .map((n) => n[0])
      .join("")
      .slice(0, 2)
      .toUpperCase() ??
    user?.email?.[0]?.toUpperCase() ??
    "?";

  return (
    <div className="min-h-screen flex bg-background text-foreground">
      <aside
        style={{ width: sidebarWidth }}
        className="relative hidden md:flex flex-col border-r bg-sidebar text-sidebar-foreground shrink-0"
      >
        {/* Drag handle */}
        <div
          onMouseDown={onDragHandleMouseDown}
          className="absolute right-0 top-0 h-full w-1 cursor-col-resize hover:bg-primary/30 active:bg-primary/50 transition-colors z-10"
        />
        <div className="h-16 flex items-center px-4 border-b border-sidebar-border">
          <Link to="/" className="flex items-center gap-2">
            <div className="size-8 rounded-lg bg-primary text-primary-foreground grid place-items-center">
              <Leaf className="size-4" />
            </div>
            {!collapsed && <span className="font-semibold tracking-tight">TimeWise</span>}
          </Link>
        </div>

        {!collapsed && currentTenant && (
          <div className="px-3 pt-3">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button
                  type="button"
                  className="w-full flex items-center gap-2 rounded-lg px-2 py-2 hover:bg-sidebar-accent transition text-left"
                >
                  <div className="size-8 rounded-md bg-gradient-to-br from-primary to-[oklch(0.3_0.08_165)] text-primary-foreground grid place-items-center text-sm font-semibold">
                    {currentTenant.name[0]?.toUpperCase()}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium truncate">{currentTenant.name}</div>
                    <div className="text-xs text-muted-foreground truncate">
                      {currentTenant.slug}
                    </div>
                  </div>
                  <ChevronsUpDown className="size-4 text-muted-foreground" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start" className="w-56">
                <DropdownMenuLabel className="text-xs text-muted-foreground">
                  {t("layout.workspaces")}
                </DropdownMenuLabel>
                {tenants.map((t) => (
                  <DropdownMenuItem
                    key={t.id}
                    onClick={() => setCurrentTenantId(t.id)}
                    className="flex items-center justify-between"
                  >
                    <span>{t.name}</span>
                    {t.id === currentTenantId && <Check className="size-4 text-primary" />}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        )}

        <nav className="flex-1 px-3 py-4 space-y-4">
          {visibleGroups.map((group, gi) => (
            <div key={gi}>
              {group.label ? (
                collapsed ? (
                  <hr className="border-sidebar-border mx-1 mb-2" />
                ) : (
                  <p className="px-2.5 mb-1 text-[10px] font-semibold uppercase tracking-widest text-sidebar-foreground/40 select-none">
                    {group.label}
                  </p>
                )
              ) : null}
              <div className="space-y-0.5">
                {group.items.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end={item.end}
                    data-tour={item.tourId}
                    className={({ isActive }) =>
                      cn(
                        "group flex items-center gap-3 rounded-lg px-2.5 py-2 text-sm font-medium transition",
                        isActive
                          ? "bg-sidebar-accent text-sidebar-accent-foreground"
                          : "text-sidebar-foreground/70 hover:bg-sidebar-accent/60 hover:text-sidebar-foreground",
                      )
                    }
                  >
                    {({ isActive }) => (
                      <>
                        <item.icon className={cn("size-4 shrink-0", isActive && "text-primary")} />
                        {!collapsed && <span>{item.label}</span>}
                      </>
                    )}
                  </NavLink>
                ))}
              </div>
            </div>
          ))}
        </nav>

      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 border-b bg-background/80 backdrop-blur-md sticky top-0 z-10 flex items-center gap-3 px-4 lg:px-6">
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleCollapse}
            aria-label={collapsed ? t("layout.expand") : t("layout.collapse")}
            title={collapsed ? t("layout.expand") : t("layout.collapse")}
          >
            {collapsed ? <PanelLeftOpen className="size-4" /> : <PanelLeftClose className="size-4" />}
          </Button>
          <button
            type="button"
            onClick={() => palette.setOpen(true)}
            className="relative flex-1 max-w-md flex items-center gap-2 h-9 rounded-md border border-transparent bg-muted/40 hover:bg-muted/60 px-3 text-left text-sm text-muted-foreground transition"
          >
            <Search className="size-4" />
            <span className="flex-1 truncate">{t("layout.search")}</span>
            <kbd className="hidden sm:inline-flex text-[10px] border rounded px-1.5 py-0.5">⌘K</kbd>
          </button>
          <div className="ml-auto flex items-center gap-1">
            <Button
              variant="ghost"
              size="icon"
              onClick={toggle}
              aria-label={t("layout.themeToggle")}
            >
              {theme === "dark" ? <Sun className="size-4" /> : <Moon className="size-4" />}
            </Button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  className="font-medium uppercase"
                  aria-label={t("layout.languageMenu")}
                >
                  {i18n.resolvedLanguage ?? i18n.language}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-40">
                <DropdownMenuItem onClick={() => i18n.changeLanguage("en")}>
                  {t("language.english")}
                  {i18n.resolvedLanguage === "en" && <Check className="size-4 ml-auto" />}
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => i18n.changeLanguage("es")}>
                  {t("language.spanish")}
                  {i18n.resolvedLanguage === "es" && <Check className="size-4 ml-auto" />}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
            <Button
              variant="ghost"
              size="icon"
              data-tour="restart-tour"
              onClick={startTour}
              aria-label={t("layout.startTour")}
              title={t("layout.startTour")}
            >
              <Compass className="size-4" />
            </Button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button
                  type="button"
                  className="ml-1 flex items-center gap-2 rounded-full hover:bg-muted px-1 py-1 transition"
                >
                  <Avatar className="size-8">
                    <AvatarFallback className="bg-primary/10 text-primary text-xs font-semibold">
                      {initials}
                    </AvatarFallback>
                  </Avatar>
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel asChild>
                  <Link to="/profile" className="block focus:bg-accent hover:bg-accent rounded-sm">
                    <div className="text-sm font-medium">{user?.full_name}</div>
                    <div className="text-xs text-muted-foreground font-normal">{user?.email}</div>
                  </Link>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem asChild>
                  <Link to="/profile">
                    <User className="size-4 mr-2" />
                    {t("layout.profile")}
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => logout.mutate()}>
                  <LogOut className="size-4 mr-2" />
                  {t("layout.logout")}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>

        <CommandPalette open={palette.open} onOpenChange={palette.setOpen} />
        <DemoDataBanner />
        <TourRunner />

        <main className="flex-1 overflow-auto">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2 }}
              className="p-4 lg:p-8 max-w-[1400px] mx-auto w-full"
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}
