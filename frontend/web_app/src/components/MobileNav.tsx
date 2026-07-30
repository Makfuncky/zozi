"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Grid3X3, ShoppingCart, Package, User } from "lucide-react";
import { useCartStore } from "@/lib/cartStore";

const NAV_ITEMS = [
  { href: "/", label: "Home", icon: Home },
  { href: "/products", label: "Shop", icon: Grid3X3 },
  { href: "/cart", label: "Cart", icon: ShoppingCart, badge: true },
  { href: "/orders", label: "Orders", icon: Package },
  { href: "/profile", label: "Profile", icon: User },
] as const;

export default function MobileNav() {
  const pathname = usePathname();
  const itemCount = useCartStore((s) => s.items.reduce((n, i) => n + i.quantity, 0));

  // Hide on supplier and admin routes
  if (pathname?.startsWith("/supplier") || pathname?.startsWith("/admin")) return null;

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-40 md:hidden bg-surface-1/95 backdrop-blur-md border-t border-border safe-area-inset-bottom">
      <ul className="flex items-center justify-around h-14">
        {NAV_ITEMS.map((item) => {
          const { href, label, icon: Icon } = item;
          const badge = "badge" in item ? item.badge : false;
          const active = href === "/" ? pathname === "/" : pathname?.startsWith(href);
          return (
            <li key={href} className="flex-1">
              <Link
                href={href}
                className={`relative flex flex-col items-center justify-center gap-0.5 h-14 w-full transition-colors ${
                  active
                    ? "text-indigo-400"
                    : "text-text-faint hover:text-text-muted"
                }`}
                aria-current={active ? "page" : undefined}
              >
                <span className="relative">
                  <Icon className="w-5 h-5" />
                  {badge && itemCount > 0 && (
                    <span className="absolute -top-1.5 -right-2 min-w-[16px] h-4 px-0.5 bg-indigo-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center leading-none">
                      {itemCount > 99 ? "99+" : itemCount}
                    </span>
                  )}
                </span>
                <span className="text-[10px] font-medium">{label}</span>
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}


