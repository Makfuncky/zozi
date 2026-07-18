/**
 * /logo-animation  –  Standalone Zozi logo animation page
 *
 * Use cases:
 *   • Screen-record this page to produce a logo intro video
 *   • Embed the LogoAnimation component anywhere as a splash / loading screen
 *
 * The ?theme=light query parameter switches to light mode.
 * The ?tagline=... query parameter shows a tagline beneath "Zozi".
 */
import type { Metadata } from "next";
import LogoAnimationClient from "./LogoAnimationClient";

export const metadata: Metadata = {
  title: "Zozi — Logo Animation",
  description: "Brand logo animation for Zozi.",
  robots: { index: false, follow: false },
};

export default function LogoAnimationPage() {
  return <LogoAnimationClient />;
}


