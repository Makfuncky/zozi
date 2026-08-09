/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { motion } from "motion/react";
import ZoziLogo from "./zozi-logo";

type ThemeSectionProps = {
  dark?: boolean;
};

function LogoSection({ dark = false }: ThemeSectionProps) {
  const bg      = dark ? "#0D0D0D" : "#FCFCFC";
  const textClr = dark ? "#FFFFFF" : "#243454";
  const textShadow = dark
    ? "0px 4px 16px rgba(0,0,0,0.5)"
    : "0px 4px 16px rgba(36,52,84,0.12)";

  return (
    <div
      className="flex flex-col items-center justify-center gap-12 px-12 py-14 w-full"
      style={{ background: bg }}
    >
      {/* Label */}
      <span
        className="text-xs font-semibold uppercase tracking-widest"
        style={{ color: dark ? "rgba(255,255,255,0.35)" : "rgba(0,0,0,0.3)" }}
      >
        {dark ? "Dark Theme" : "Light Theme"}
      </span>

      {/* Full logo with Zozi text */}
      <div className="flex items-center select-none">
        <div className="relative w-47.5 h-42.5 flex items-center justify-center">
          <ZoziLogo size={190} animated theme={dark ? "dark" : "light"} />
        </div>

        <motion.h1
          initial={{ x: 30, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ delay: 0.5, duration: 0.7, ease: "easeOut" }}
          className="font-nunito font-black text-[116px] leading-none tracking-[-5px]"
          style={{ color: textClr, textShadow }}
        >
          Zozi
        </motion.h1>
      </div>

      {/* Standalone animated Z */}
      <ZoziLogo size={130} animated theme={dark ? "dark" : "light"} />
    </div>
  );
}

export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <LogoSection dark={false} />
      <LogoSection dark />
    </div>
  );
}
