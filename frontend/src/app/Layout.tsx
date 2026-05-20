import { AnimatePresence, motion } from "framer-motion";
import {
  Bell,
  Calculator,
  Check,
  CheckSquare,
  ChevronsUpDown,
  Clock,
  FolderKanban,
  LayoutDashboard,
  Leaf,
  LogOut,
  Moon,
  ScrollText,
  Search,
  Settings,
  Sun,
  Tag,
  User,
  Users,
} from "lucide-react";
import { useEffect, useState } from "react";
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
import { ProfileDialog } from "@/features/auth/components/ProfileDialog";
import { useLogout } from "@/features/auth/hooks";

import { useAuthStore } from "@/features/auth/store";
import { useTenants } from "@/features/tenants/hooks";
import { useTenantStore } from "@/features/tenants/store";
import { useTheme } from "@/hooks/use-theme";
import { cn } from "@/lib/utils";

type NavItem = {
  to: string;
  label: string;
  icon: typeof LayoutDashboard;
  end?: boolean;
};

export function Layout() {
  const location = useLocation();
  const { theme, toggle } = useTheme();
  const { i18n, t } = useTranslation();
  const user = useAuthStore((s) => s.user);
  const logout = useLogout();
  const nav: NavItem[] = [
    { to: "/", label: t("layout.nav.home"), icon: LayoutDashboard, end: true },
    { to: "/employees", label: t("layout.nav.employees"), icon: Users },
    { to: "/departments", label: t("layout.nav.departments"), icon: FolderKanban },
    { to: "/roles", label: t("layout.nav.roles"), icon: Tag },
    { to: "/periods", label: t("layout.nav.periods"), icon: Clock },
    { to: "/time", label: t("layout.nav.time"), icon: Clock },
    { to: "/reports", label: t("layout.nav.reports"), icon: Clock },
    { to: "/approvals", label: t("layout.nav.approvals"), icon: CheckSquare },
    { to: "/costing-rules", label: t("layout.nav.costingRules"), icon: Calculator },
    { to: "/costing", label: t("layout.nav.costing"), icon: Calculator },
    { to: "/audit", label: t("layout.nav.audit"), icon: ScrollText },
    { to: "/settings", label: t("layout.nav.settings"), icon: Settings },
  ];
  const { data: tenants = [] } = useTenants();
  const { currentTenantId, setCurrentTenantId } = useTenantStore();
  const currentTenant = tenants.find((t) => t.id === currentTenantId) ?? tenants[0] ?? null;
  const [collapsed, setCollapsed] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
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
        className={cn(
          "hidden md:flex flex-col border-r bg-sidebar text-sidebar-foreground transition-all duration-200",
          collapsed ? "w-[68px]" : "w-[244px]",
        )}
      >
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

        <nav className="flex-1 px-3 py-4 space-y-0.5">
          {nav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
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
                  <item.icon className={cn("size-4", isActive && "text-primary")} />
                  {!collapsed && <span>{item.label}</span>}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="p-3 border-t border-sidebar-border">
          <button
            type="button"
            onClick={() => setCollapsed((c) => !c)}
            className="text-xs text-muted-foreground hover:text-foreground w-full text-left px-2"
          >
            {collapsed ? t("layout.expand") : t("layout.collapse")}
          </button>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 border-b bg-background/80 backdrop-blur-md sticky top-0 z-10 flex items-center gap-3 px-4 lg:px-6">
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
              className="relative"
              aria-label={t("layout.notifications")}
            >
              <Bell className="size-4" />
              <span className="absolute top-2 right-2 size-1.5 rounded-full bg-primary" />
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
                <DropdownMenuLabel
                  className="cursor-pointer focus:bg-accent hover:bg-accent rounded-sm"
                  onClick={() => setProfileOpen(true)}
                >
                  <div className="text-sm font-medium">{user?.full_name}</div>
                  <div className="text-xs text-muted-foreground font-normal">{user?.email}</div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => setProfileOpen(true)}>
                  <User className="size-4 mr-2" />
                  {t("layout.profile")}
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => logout.mutate()}>
                  <LogOut className="size-4 mr-2" />
                  {t("layout.logout")}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>

        <ProfileDialog open={profileOpen} onOpenChange={setProfileOpen} />
        <CommandPalette open={palette.open} onOpenChange={palette.setOpen} />

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
