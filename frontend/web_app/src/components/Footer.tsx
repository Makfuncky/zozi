"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Sparkles, Crown } from "@/lib/icons";
import { useLocaleStore } from "@/lib/localeStore";
import NewsletterSignup from "./NewsletterSignup";

function shouldHideFooter(pathname: string | null): boolean {
  if (!pathname) return false;
  if (pathname.startsWith("/admin")) return true;
  if (pathname.startsWith("/logistics-partner")) return true;
  if (pathname === "/supplier") return false;
  if (pathname.startsWith("/supplier/")) return true;
  return false;
}

export default function Footer() {
  const tr = useLocaleStore((s) => s.t);
  const pathname = usePathname();

  if (shouldHideFooter(pathname)) return null;

  return (
    <footer className="relative border-t border-border bg-linear-to-b from-surface-1/58 via-surface-1/30 to-transparent backdrop-blur-[2px]">
      <div className="absolute inset-0 pointer-events-none bg-[radial-gradient(circle_at_top_left,rgba(47,180,61,0.1),transparent_32%),radial-gradient(circle_at_top_right,rgba(250,204,21,0.08),transparent_30%)]" />
      <div className="relative max-w-11xl mx-auto px-6 pt-12 pb-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 md:gap-12">
          {/* Brand */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <div className="w-7 h-7 rounded-2xl flex items-center justify-center bg-primary shadow-lg shadow-black/15">
                <Sparkles className="w-3.5 h-3.5 text-white" />
              </div>
              <span className="text-sm font-semibold tracking-[0.4em] text-text font-heading">
                ZOZI
              </span>
            </div>
            <p className="max-w-xs text-xs leading-relaxed text-text-muted">
              {tr("footerTagline")}
            </p>
            <div className="mt-5 space-y-2">
              <Link
                href="/supplier/register"
                className="inline-flex items-center rounded-lg border border-primary/35 bg-primary/10 px-3 py-2 text-xs font-semibold text-primary transition-colors hover:border-primary/50 hover:bg-primary/15"
              >
                {tr("becomeSupplier")}
              </Link>
              <Link
                href="/logistics-partner/login"
                className="inline-flex items-center rounded-lg border border-primary/35 bg-primary/10 px-3 py-2 text-xs font-semibold text-primary transition-colors hover:border-primary/50 hover:bg-primary/15"
              >
                {tr("becomeLogisticsPartner")}
              </Link>
            </div>
          </div>


          {/* Newsletter */}
          <div>
            <h5 className="mb-3 text-[10px] font-semibold uppercase tracking-[0.25em] text-text-faint">
              {tr("marketDispatch")}
            </h5>
            <NewsletterSignup variant="footer" />
          </div>
        </div>
      </div>

      {/* Bottom bar */}
      <div className="border-t border-border bg-surface-2/28 backdrop-blur-[2px]">
        <div className="max-w-[350px] mx-auto px-6 py-3 flex flex-col sm:flex-row items-center justify-between gap-3">
          <p className="text-[11px] text-text-faint">
            &copy; {new Date().getFullYear()} ZOZI. {tr("allRightsReserved")}
          </p>
          <div className="flex items-center gap-4 text-[11px] text-text-faint">
            {(["terms", "privacy", "cookies"] as const).map((key) => (
              <Link
                key={key}
                href={`/${key}`}
                className="transition-colors hover:text-text-muted"
              >
                {tr(key)}
              </Link>
            ))}
            <Link
              href="/admin/login"
              className="opacity-20 hover:opacity-100 transition-opacity"
              title={tr("adminPortal")}
              aria-label={tr("adminPortal")}
            >
              <Crown className="w-2.5 h-2.5 text-accent" />
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}


