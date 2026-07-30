"use client";

import { Button } from "@/components/ui/Button";

import { useEffect, useState, useRef, type MouseEvent as ReactMouseEvent, type ReactNode, type KeyboardEvent } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import BackgroundJobCenter from "@/components/BackgroundJobCenter";
import DataDensityToggle from "@/components/DataDensityToggle";
import KeyboardShortcutsHelp from "@/components/KeyboardShortcutsHelp";
import ThemeToggle from "@/components/ThemeToggle";
import { cn } from "@/lib/utils";
import type { PanelNavItem, PanelNavSection, PanelNavIcon } from "@/lib/panelNavigation";
import { ChevronLeft, ChevronRight, LogOut, Menu, X, Search, GripVertical } from "@/lib/icons";

interface PanelShellProps {
  children: ReactNode;
  title?: string;
  headerMode?: "default" | "compact";
  panelClassName: string;
  brandLabel: string;
  panelBadgeLabel: string;
  panelBadgeClassName: string;
  defaultTitle: string;
  defaultDescription: string;
  sections: PanelNavSection[];
  allItems: PanelNavItem[];
  isActiveItem: (item: PanelNavItem) => boolean;
  onLogout: () => void | Promise<void>;
  logoutLabel: string;
  userName?: string | null;
  fallbackUserLabel: string;
  userSecondaryLabel?: string;
  avatarIcon: PanelNavIcon;
  avatarClassName: string;
  shortcutScope: "admin" | "supplier" | "logistics";
  dir?: "ltr" | "rtl";
  isRtl?: boolean;
}

function NavItemIndicator({ active }: { active: boolean }) {
  return (
    <span className={cn(
      "absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 rounded-r-full transition-all duration-200",
      active ? "bg-primary opacity-100" : "bg-transparent opacity-0",
    )} />
  );
}

export default function PanelShell({
  children,
  title,
  headerMode = "default",
  panelClassName,
  brandLabel,
  panelBadgeLabel,
  panelBadgeClassName,
  defaultTitle,
  defaultDescription,
  sections,
  allItems,
  isActiveItem,
  onLogout,
  logoutLabel,
  userName,
  fallbackUserLabel,
  userSecondaryLabel,
  avatarIcon: AvatarIcon,
  avatarClassName,
  shortcutScope,
  dir = "ltr",
  isRtl = false,
}: PanelShellProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [navSearch, setNavSearch] = useState("");
  const [focusedIdx, setFocusedIdx] = useState(-1);
  const navRef = useRef<HTMLDivElement>(null);
  const pathname = usePathname();

  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  useEffect(() => {
    if (!mobileOpen) return;
    const onKey = (event: globalThis.KeyboardEvent) => {
      if (event.key === "Escape") setMobileOpen(false);
    };
    window.addEventListener("keydown", onKey);
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = prevOverflow;
    };
  }, [mobileOpen]);

  // Keyboard navigation within sidebar
  useEffect(() => {
    const nav = navRef.current;
    if (!nav || collapsed) return;
    const links = nav.querySelectorAll<HTMLAnchorElement>("a");
    const handleKeyDown = (e: globalThis.KeyboardEvent) => {
      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        e.preventDefault();
        const dir = e.key === "ArrowDown" ? 1 : -1;
        setFocusedIdx((prev) => {
          const next = Math.max(0, Math.min(links.length - 1, prev + dir));
          links[next]?.focus();
          return next;
        });
      }
    };
    nav.addEventListener("keydown", handleKeyDown);
    return () => nav.removeEventListener("keydown", handleKeyDown);
  }, [collapsed]);

  const allNavItems = sections.flatMap((s) => s.items);
  const filteredNav = navSearch
    ? allNavItems.filter((item) =>
        item.name.toLowerCase().includes(navSearch.toLowerCase()) ||
        item.desc.toLowerCase().includes(navSearch.toLowerCase())
      )
    : null;

  const navItemClass = "theme-nav-item relative text-text-muted hover:text-text";
  const activeItem = allItems.find(isActiveItem);
  const activeSection = sections.find((section) => section.key === activeItem?.group);
  const quickLinks = headerMode === "compact"
    ? []
    : (activeSection?.items ?? []).filter((item) => !isActiveItem(item)).slice(0, 4);
  const resolvedTitle = title || activeItem?.name || defaultTitle;
  const resolvedDescription = activeItem?.desc || defaultDescription;

  const COLLAPSED_CLS = "w-0 lg:w-20";
  const EXPANDED_CLS = "w-0 lg:w-64 xl:w-[272px]";
  const sidebarClass = collapsed ? COLLAPSED_CLS : EXPANDED_CLS;
  const mainMarginCls = isRtl
    ? collapsed ? "lg:mr-20" : "lg:mr-64 xl:mr-[17rem]"
    : collapsed ? "lg:ml-20" : "lg:ml-64 xl:ml-[17rem]";

  const renderNavLink = (item: PanelNavItem, mobile = false) => {
    const active = isActiveItem(item);
    return (
      <Link
        key={item.href}
        href={item.href}
        prefetch
        title={collapsed && !mobile ? item.name : undefined}
        onClick={() => { if (mobile) setMobileOpen(false); }}
        className={cn(
          "flex items-center gap-2.5 rounded-lg px-2 py-2 text-xs transition-all duration-150 relative group",
          active ? "theme-nav-item-active text-on-brand bg-primary/10" : navItemClass,
          collapsed && !mobile && "justify-center px-0",
        )}
      >
        <NavItemIndicator active={active} />
        <item.icon className={cn(
          "h-4 w-4 shrink-0 transition-all duration-150",
          active ? "text-primary" : "text-text-muted",
        )} />
        {(!collapsed || mobile) && (
          <span className="font-medium leading-tight truncate">{item.name}</span>
        )}
      </Link>
    );
  };

  const renderNavGroup = (items: PanelNavItem[], mobile = false) => {
    return (
      <div className="space-y-0.5">
        {items.map((item) => renderNavLink(item, mobile))}
      </div>
    );
  };

  return (
    <div dir={dir} className={cn(panelClassName, "theme-layout-shell relative min-h-screen bg-surface-base")}>
      {/* Mobile drawer overlay */}
      <div
        className={cn(
          "fixed inset-0 z-50 transition-all duration-300 ease-out lg:hidden",
          mobileOpen ? "opacity-100" : "pointer-events-none opacity-0"
        )}
        aria-hidden={!mobileOpen}
      >
        <div className="theme-overlay absolute inset-0" onClick={() => setMobileOpen(false)} />
        <nav
          aria-label={`${brandLabel} navigation`}
          className={cn(
            "theme-sidebar-shell absolute top-0 z-50 flex h-full w-[min(19rem,85vw)] max-w-[280px] flex-col shadow-2xl transition-transform duration-300 ease-out",
            isRtl ? "right-0 border-l" : "left-0 border-r",
            mobileOpen ? "translate-x-0" : isRtl ? "translate-x-full" : "-translate-x-full"
          )}
          onClick={(event: ReactMouseEvent<HTMLDivElement>) => event.stopPropagation()}
        >
          <div className="flex items-center justify-between border-b border-border px-4 py-3">
            <span className="text-sm font-bold text-text">{brandLabel}</span>
            <button onClick={() => setMobileOpen(false)}
              className="rounded-lg bg-transparent p-1.5 text-text-muted hover:bg-surface-1 hover:text-text"
              aria-label="Close navigation">
              <X className="h-4 w-4" />
            </button>
          </div>
          <nav className="flex-1 overflow-y-auto px-3 py-2">
            {sections.map((section) => (
              <div key={section.key} className="mb-3 last:mb-0">
                <p className="px-2.5 pb-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-text-faint">
                  {section.label}
                </p>
                {renderNavGroup(section.items, true)}
              </div>
            ))}
          </nav>
          <div className="border-t border-border px-3 py-2">
            <Button variant="danger" className="flex w-full items-center gap-3 rounded-lg px-2.5 py-2.5 text-xs"
              onClick={() => void onLogout()}>
              <LogOut className="h-4 w-4" />
              <span>{logoutLabel}</span>
            </Button>
          </div>
        </nav>
      </div>

      {/* Desktop sidebar */}
      <aside ref={navRef}
        className={cn(
          "theme-sidebar-shell fixed top-0 z-40 hidden h-full flex-col overflow-hidden transition-all duration-300 ease-out lg:flex border-r border-border",
          sidebarClass,
          isRtl ? "right-0" : "left-0",
        )}
      >
        {/* Brand + collapse */}
        <div className="flex items-center justify-between border-b border-border p-3 min-h-[57px]">
          <span className={cn(
            "text-base font-bold text-text whitespace-nowrap overflow-hidden transition-opacity duration-200",
            collapsed ? "opacity-0 w-0" : "opacity-100",
          )}>{brandLabel}</span>
          <button onClick={() => setCollapsed((v) => !v)}
            className="rounded-lg bg-transparent p-1.5 text-text-muted hover:bg-surface-1 hover:text-text flex-shrink-0"
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}>
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </button>
        </div>

        {/* User info */}
        <div className={cn("border-b border-border flex items-center", collapsed ? "justify-center p-3" : "gap-3 p-3")}>
          <div className={cn("flex h-8 w-8 shrink-0 items-center justify-center rounded-full", avatarClassName)}>
            <AvatarIcon className="h-4 w-4 text-white" />
          </div>
          <div className={cn("min-w-0 overflow-hidden transition-all duration-200", collapsed ? "w-0 opacity-0" : "opacity-100")}>
            <p className="truncate text-xs font-medium text-text">{userName || fallbackUserLabel}</p>
            {userSecondaryLabel && <p className="text-[11px] text-text-faint truncate">{userSecondaryLabel}</p>}
          </div>
        </div>

        {/* Search */}
        <div className={cn("border-b border-border transition-all duration-200 overflow-hidden", collapsed ? "h-0 p-0" : "p-2")}>
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3 h-3 text-text-muted" />
            <input type="text" placeholder="Search nav..." value={navSearch}
              onChange={(e) => setNavSearch(e.target.value)}
              className="w-full pl-7 pr-2 py-1.5 rounded-lg bg-surface-1 border border-border text-xs text-text
                placeholder:text-text-faint focus:outline-none focus:ring-1 focus:ring-primary/30" />
          </div>
          {/* Search results dropdown */}
          {navSearch && filteredNav && filteredNav.length > 0 && (
            <div className="mt-1 rounded-lg border border-border bg-surface shadow-lg overflow-hidden">
              {filteredNav.slice(0, 5).map((item) => (
                <Link key={item.href} href={item.href} onClick={() => setNavSearch("")}
                  className="flex items-center gap-2 px-2.5 py-2 text-xs hover:bg-surface-2 transition-colors">
                  <item.icon className="w-3 h-3 text-text-muted" />
                  <span className="text-text font-medium">{item.name}</span>
                  <span className="text-text-faint ml-auto text-[10px]">{item.desc.slice(0, 30)}</span>
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Nav items */}
        <nav className="flex-1 overflow-y-auto p-2 space-y-1">
          {sections.map((section) => (
            <div key={section.key} className="mb-3 last:mb-0">
              {!collapsed && (
                <p className="px-2.5 pb-1 text-[10px] font-semibold uppercase tracking-[0.2em] text-text-faint">
                  {section.label}
                </p>
              )}
              {renderNavGroup(section.items)}
            </div>
          ))}
        </nav>

        {/* Logout */}
        <div className="border-t border-border p-2">
          <button onClick={() => void onLogout()}
            className={cn(
              "flex w-full items-center gap-3 rounded-lg px-2.5 py-2 text-xs text-danger hover:bg-danger/10 transition-colors",
              collapsed && "justify-center",
            )}>
            <LogOut className="h-4 w-4" />
            {!collapsed && <span>{logoutLabel}</span>}
          </button>
        </div>
      </aside>

      {/* Main content */}
      <div className={cn(
        "theme-main-content min-w-0 transition-all duration-300",
        mainMarginCls,
      )}>
        <header className="theme-topbar sticky top-0 z-30 border-b border-border bg-surface-base/95 backdrop-blur-md">
          <div className="flex flex-col gap-2 px-3 py-2 sm:px-4 lg:px-5">
            <div className="flex min-w-0 items-start gap-2 lg:items-center lg:justify-between">
              <div className="flex items-start gap-2 min-w-0">
                <button onClick={() => setMobileOpen(true)}
                  className="rounded-lg bg-transparent p-1.5 text-text-muted hover:bg-surface-1 hover:text-text lg:hidden"
                  aria-label="Open navigation">
                  <Menu className="h-5 w-5" />
                </button>
                <div className="min-w-0">
                  {headerMode === "default" && (
                    <div className="flex flex-wrap items-center gap-1.5">
                      <span className="rounded-full border px-2 py-0.5 text-[9px] font-semibold uppercase tracking-[0.16em]"
                        style={{ borderColor: "var(--color-border)", backgroundColor: "var(--color-glass-mid)" }}>
                        {panelBadgeLabel}
                      </span>
                      {activeSection && (
                        <span className="rounded-full border border-border bg-surface-1 px-2 py-0.5 text-[9px] font-semibold uppercase tracking-[0.16em] text-text-faint">
                          {activeSection.label}
                        </span>
                      )}
                    </div>
                  )}
                  <h1 className={cn(
                    headerMode === "compact" ? "text-sm font-semibold text-text sm:text-base" : "text-base font-semibold text-text sm:text-xl mt-0.5",
                  )}>{resolvedTitle}</h1>
                  <p className={cn(
                    "max-w-2xl text-[12px] text-text-muted",
                    headerMode === "compact" && "text-[11px] text-text-faint",
                  )}>{resolvedDescription}</p>
                </div>
              </div>

              <div className="flex items-center gap-1.5 flex-shrink-0">
                {quickLinks.length > 0 && (
                  <div className="hidden items-center gap-1.5 lg:flex">
                    {quickLinks.map((item) => (
                      <Link key={item.href} href={item.href} prefetch
                        className="theme-panel inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[10px] font-semibold
                          text-text-muted transition-colors hover:bg-surface-2 hover:text-text">
                        <item.icon className="h-3 w-3" />
                        {item.name}
                      </Link>
                    ))}
                  </div>
                )}
                {headerMode === "default" && (
                  <div className="hidden items-center gap-1.5 lg:flex ml-2 pl-2 border-l border-border">
                    <KeyboardShortcutsHelp scope={shortcutScope} />
                    <ThemeToggle />
                    <DataDensityToggle />
                    {userSecondaryLabel && (
                      <span className="rounded-full border border-border bg-surface-1 px-2 py-0.5 text-[9px] font-semibold uppercase tracking-[0.16em] text-text-faint">
                        {userSecondaryLabel}
                      </span>
                    )}
                    <span className="text-[11px] font-medium text-text-muted">{userName || fallbackUserLabel}</span>
                    <div className={cn("flex h-6 w-6 items-center justify-center rounded-full", avatarClassName)}>
                      <AvatarIcon className="h-3 w-3 text-white" />
                    </div>
                  </div>
                )}
              </div>
            </div>

            {quickLinks.length > 0 && (
              <div className="flex flex-wrap items-center gap-1.5 lg:hidden">
                {quickLinks.map((item) => (
                  <Link key={item.href} href={item.href} prefetch
                    className="theme-panel inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[10px] font-semibold
                      text-text-muted transition-colors hover:bg-surface-2 hover:text-text">
                    <item.icon className="h-3 w-3" />
                    {item.name}
                  </Link>
                ))}
              </div>
            )}
          </div>
        </header>

        <main className="mx-auto w-full min-w-0 max-w-450 p-2 sm:p-3 lg:p-5">{children}</main>
      </div>
      <BackgroundJobCenter />
    </div>
  );
}
