"use client";

import { Button } from "@/components/ui/Button";

import { useEffect, useState, type MouseEvent as ReactMouseEvent, type ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import BackgroundJobCenter from "@/components/BackgroundJobCenter";
import DataDensityToggle from "@/components/DataDensityToggle";
import KeyboardShortcutsHelp from "@/components/KeyboardShortcutsHelp";
import ThemeToggle from "@/components/ThemeToggle";
import { cn } from "@/lib/utils";
import type { PanelNavItem, PanelNavSection, PanelNavIcon } from "@/lib/panelNavigation";
import { ChevronLeft, ChevronRight, LogOut, Menu, X } from "@/lib/icons";

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
  const pathname = usePathname();

  // Close the mobile slide-out drawer on route changes and Escape key.
  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  useEffect(() => {
    if (!mobileOpen) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setMobileOpen(false);
    };
    window.addEventListener("keydown", onKey);
    // Lock background scroll while the drawer is open (jank-free mobile UX).
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = prevOverflow;
    };
  }, [mobileOpen]);

  const navItemClass = "theme-nav-item text-text-muted hover:text-text";
  const activeItem = allItems.find(isActiveItem);
  const activeSection = sections.find((section) => section.key === activeItem?.group);
  const quickLinks = headerMode === "compact"
    ? []
    : (activeSection?.items ?? []).filter((item) => !isActiveItem(item)).slice(0, 3);
  const resolvedTitle = title || activeItem?.name || defaultTitle;
  const resolvedDescription = activeItem?.desc || defaultDescription;

  // Single source of truth for widths so the main content offset always matches
  // the sidebar width at every breakpoint (previously duplicated magic numbers).
  const COLLAPSED_WIDTH = { base: "w-20", lg: "lg:pl-20", lgRtl: "lg:pr-20" };
  const EXPANDED_WIDTH = { base: "w-64 xl:w-[272px]", lg: "lg:pl-64 xl:pl-[17rem]", lgRtl: "lg:pr-64 xl:pr-[17rem]" };
  const sidebarSideClass = isRtl ? "right-0 border-l" : "left-0 border-r";
  const mainOffsetClass = isRtl
    ? collapsed
      ? COLLAPSED_WIDTH.lgRtl
      : EXPANDED_WIDTH.lgRtl
    : collapsed
      ? COLLAPSED_WIDTH.lg
      : EXPANDED_WIDTH.lg;

  const renderNavLink = (item: PanelNavItem, mobile = false) => {
    const isActive = isActiveItem(item);
    return (
      <Link
        key={item.href}
        href={item.href}
        prefetch
        title={collapsed && !mobile ? item.name : undefined}
        onClick={() => {
          if (mobile) setMobileOpen(false);
        }}
        className={cn(
          "flex items-center gap-2.5 rounded-lg px-2 py-2 text-xs transition-colors",
          isActive ? "theme-nav-item-active text-on-brand" : navItemClass,
          collapsed && !mobile && "justify-center"
        )}
      >
        <item.icon className="h-3.5 w-3.5 shrink-0" />
        {(!collapsed || mobile) && <span className="font-medium leading-tight">{item.name}</span>}
      </Link>
    );
  };

  return (
    <div dir={dir} className={cn(panelClassName, "theme-layout-shell relative min-h-screen bg-surface-base")}>
      {/* Mobile slide-out drawer — kept mounted so the transition-transform
          actually animates on open AND close (previously mounted/unmounted,
          so it "popped" instead of sliding). Visibility + pointer-events toggle
          the interactivity without removing it from the DOM. */}
      <div
        className={cn(
          "fixed inset-0 z-50 transition-opacity duration-300 ease-out",
          mobileOpen ? "opacity-100" : "pointer-events-none opacity-0"
        )}
        aria-hidden={!mobileOpen}
      >
        <div
          className="theme-overlay absolute inset-0"
          onClick={() => setMobileOpen(false)}
        />
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
            <button
              onClick={() => setMobileOpen(false)}
              className="rounded-lg bg-transparent p-1.5 text-text-muted hover:bg-surface-1 hover:text-text"
              aria-label="Close navigation"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
          {/* Single scroll container — the logout footer stays pinned below. */}
          <nav className="flex-1 overflow-y-auto px-3 py-2">
            {sections.map((section) => (
              <div key={section.key} className="mb-3 last:mb-0">
                <p className="px-2.5 pb-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-text-faint">
                  {section.label}
                </p>
                <div className="space-y-0.5">{section.items.map((item) => renderNavLink(item, true))}</div>
              </div>
            ))}
          </nav>
          <div className="border-t border-border px-3 py-2">
            <Button
              variant="danger"
              className="flex w-full items-center gap-3 rounded-lg px-2.5 py-2.5 text-xs"
              onClick={() => void onLogout()}
            >
              <LogOut className="h-4 w-4" />
              <span>{logoutLabel}</span>
            </Button>
          </div>
        </nav>
      </div>

      <aside
        className={cn(
          "theme-sidebar-shell fixed top-0 z-40 hidden h-full flex-col overflow-hidden transition-[width] duration-300 ease-out lg:flex",
          collapsed ? "w-20" : "w-64 xl:w-[272px]",
          sidebarSideClass
        )}
      >
        <div className="flex items-center justify-between border-b border-border p-3">
          {!collapsed && (
            <span className="text-base font-bold text-text">{brandLabel}</span>
          )}
          <button
            onClick={() => setCollapsed((value) => !value)}
            className="rounded-lg bg-transparent p-1.5 text-text-muted hover:bg-surface-1 hover:text-text"
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </button>
        </div>

        <div className="border-b border-border p-3">
          <div className={cn("flex items-center", collapsed ? "justify-center" : "gap-3")}>
            <div className={cn("flex h-8 w-8 shrink-0 items-center justify-center rounded-full", avatarClassName)}>
              <AvatarIcon className="h-4 w-4 text-white" />
            </div>
            {!collapsed && (
              <div className="min-w-0">
                <p className="truncate text-xs font-medium text-text">{userName || fallbackUserLabel}</p>
                {userSecondaryLabel ? (
                  <p className="text-[11px] text-text-faint">{userSecondaryLabel}</p>
                ) : null}
              </div>
            )}
          </div>
        </div>

        <nav className="flex-1 overflow-y-auto p-3">
          {sections.map((section) => (
            <div key={section.key} className="mb-4 last:mb-0">
              {!collapsed && (
                <p className="px-2.5 pb-1.5 text-[10px] font-semibold uppercase tracking-[0.2em] text-text-faint">
                  {section.label}
                </p>
              )}
              <div className="space-y-0.5">{section.items.map((item) => renderNavLink(item))}</div>
            </div>
          ))}
        </nav>

        <div className="border-t border-border p-3">
          <button
            onClick={() => void onLogout()}
            className={cn(
              "flex w-full items-center gap-3 rounded-lg bg-transparent px-2.5 py-2.5 text-xs text-danger hover:bg-danger/10",
              collapsed && "justify-center"
            )}
          >
            <LogOut className="h-4 w-4" />
            {!collapsed && <span>{logoutLabel}</span>}
          </button>
        </div>
      </aside>

      <div className={cn("theme-main-content min-w-0 transition-all duration-300", mainOffsetClass)}>
        <header className="theme-topbar sticky top-0 z-30 border-b border-border px-3 py-2 sm:px-4 lg:px-5">
          <div className="flex flex-col gap-2 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex min-w-0 items-start gap-2">
               <button
                 onClick={() => setMobileOpen(true)}
                 className="rounded-lg bg-transparent p-1.5 text-text-muted hover:bg-surface-1 hover:text-text lg:hidden"
                 aria-label="Open navigation"
               >
                 <Menu className="h-5 w-5" />
               </button>
              <div className="min-w-0 flex-1">
                {headerMode === "default" ? (
                  <div className="flex flex-wrap items-center gap-1.5">
                    <span className={cn("rounded-full border px-2 py-0.5 text-[9px] font-semibold uppercase tracking-[0.16em]", panelBadgeClassName)}>
                      {panelBadgeLabel}
                    </span>
                    {activeSection ? (
                      <span className="rounded-full border border-border bg-surface-1 px-2 py-0.5 text-[9px] font-semibold uppercase tracking-[0.16em] text-text-faint">
                        {activeSection.label}
                      </span>
                    ) : null}
                  </div>
                ) : null}
                <h1 className={cn(
                  headerMode === "compact" ? "text-sm font-semibold text-text sm:text-base" : "text-base font-semibold text-text sm:text-xl",
                  headerMode === "default" ? "mt-1" : "mt-0"
                )}>{resolvedTitle}</h1>
                <p className={cn(
                  "max-w-2xl",
                  headerMode === "compact" ? "mt-0 text-[11px] text-text-faint" : "mt-0.5 text-[12px] text-text-muted"
                )}>{resolvedDescription}</p>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-1.5 lg:justify-end">
              {quickLinks.length > 0 ? (
                  <div className="hidden flex-wrap items-center gap-1.5 lg:flex">
                   {quickLinks.map((item) => (
                    <Link
                      key={item.href}
                      href={item.href}
                      prefetch
                      className="theme-panel inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[10px] font-semibold text-text-muted transition-colors hover:bg-surface-2 hover:text-text"
                    >
                      <item.icon className="h-3 w-3" />
                      {item.name}
                    </Link>
                  ))}
                </div>
              ) : null}

              {headerMode === "default" ? (
                <div className="hidden items-center gap-1.5 lg:flex">
                  <KeyboardShortcutsHelp scope={shortcutScope} />
                  <ThemeToggle />
                  <DataDensityToggle />
                  {userSecondaryLabel ? (
                    <span className="rounded-full border border-border bg-surface-1 px-2 py-0.5 text-[9px] font-semibold uppercase tracking-[0.16em] text-text-faint">
                      {userSecondaryLabel}
                    </span>
                  ) : null}
                  <span className="text-[11px] font-medium text-text-muted">{userName || fallbackUserLabel}</span>
                  <div className={cn("flex h-6 w-6 items-center justify-center rounded-full", avatarClassName)}>
                    <AvatarIcon className="h-3 w-3 text-white" />
                  </div>
                </div>
              ) : null}
            </div>
          </div>

          {quickLinks.length > 0 ? (
            <div className="mt-2 flex flex-wrap items-center gap-1.5 lg:hidden">
              {quickLinks.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  prefetch
                  className="theme-panel inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[10px] font-semibold text-text-muted transition-colors hover:bg-surface-2 hover:text-text"
                >
                  <item.icon className="h-3 w-3" />
                  {item.name}
                </Link>
              ))}
            </div>
          ) : null}
        </header>

        <main className="mx-auto w-full min-w-0 max-w-450 p-2 sm:p-3 lg:p-5">{children}</main>
      </div>

      <BackgroundJobCenter />
    </div>
  );
}