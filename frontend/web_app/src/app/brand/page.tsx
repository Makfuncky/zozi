"use client";

import { Button } from "@/components/ui/Button";

import { useState, useCallback, useEffect, useId } from "react";
import { motion, AnimatePresence } from "framer-motion";

/* ═══════════════════════════════════════════════════════
   STANDALONE ZOZI LOGO ANIMATION PAGE
   — Full‑viewport, cinematic reveal with replay support.
   — Record this page for video / promo / splash usage.
   ═══════════════════════════════════════════════════════ */

/* ── SVG path constants ── */
const UPPER_SWOOSH =
  "M 4,38 C 6,24 18,10 36,5 C 46,2 55,4 58,10 C 50,6 40,7 32,11 C 18,19 8,31 6,40 Z";
const LOWER_SWOOSH =
  "M 8,30 C 14,16 28,4 46,2 C 36,14 24,28 18,40 C 15,47 18,52 24,55 L 20,55 C 8,50 4,40 6,32 Z";
const PIN_PATH =
  "M 27,32 C 22.6,32 19,35.5 19,40 C 19,46.2 27,52 27,52 C 27,52 35,46.2 35,40 C 35,35.5 31.4,32 27,32 Z";

/* ── Floating particle component ── */
function Particle({ delay, x, y, size }: { delay: number; x: number; y: number; size: number }) {
  return (
    <motion.div
      className="absolute rounded-full bg-success/20 dark:bg-success/15"
      style={{ width: size, height: size, left: `${x}%`, top: `${y}%` }}
      initial={{ opacity: 0, scale: 0 }}
      animate={{
        opacity: [0, 0.6, 0],
        scale: [0, 1.2, 0.8],
        y: [0, -40, -80],
      }}
      transition={{ duration: 3, delay, repeat: Infinity, repeatDelay: 2 }}
    />
  );
}

/* ── Main animated logo (enlarged for showcase) ── */
function AnimatedShowcase({ run }: { run: number }) {
  const uid = useId().replace(/[^a-zA-Z0-9]/g, "");
  const topGrad  = `brand-tg-${uid}`;
  const botGrad  = `brand-bg-${uid}`;
  const pinGrad  = `brand-pg-${uid}`;
  const glowFilt = `brand-gf-${uid}`;
  const bgGlow   = `brand-bw-${uid}`;

  return (
    <motion.div
      key={run}
      className="relative flex flex-col items-center justify-center gap-6"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      {/* Background glow ring */}
      <motion.div
        className="absolute w-105 h-105 rounded-full bg-linear-to-br from-success/20 via-transparent to-yellow-300/10 blur-[80px]"
        initial={{ scale: 0, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 1.2, ease: "easeOut", delay: 0.0 }}
      />

      <svg
        viewBox="0 0 210 62"
        width={520}
        height={154}
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="relative z-10"
      >
        <defs>
          <linearGradient id={topGrad} x1="4" y1="38" x2="58" y2="5" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#2D6A04" />
            <stop offset="45%" stopColor="#76B900" />
            <stop offset="100%" stopColor="#AEEA00" />
          </linearGradient>

          <linearGradient id={botGrad} x1="46" y1="2" x2="20" y2="55" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#8BC34A" />
            <stop offset="50%" stopColor="#558B2F" />
            <stop offset="100%" stopColor="#1B5E20" />
          </linearGradient>

          <linearGradient id={pinGrad} x1="27" y1="30" x2="27" y2="52" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#FFF176" />
            <stop offset="50%" stopColor="#FFD600" />
            <stop offset="100%" stopColor="#F9A825" />
          </linearGradient>

          <filter id={glowFilt} x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur in="SourceAlpha" stdDeviation="2" />
            <feOffset dy="1.5" />
            <feComponentTransfer>
              <feFuncA type="linear" slope="0.2" />
            </feComponentTransfer>
            <feMerge>
              <feMergeNode />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>

          <filter id={bgGlow} x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="6" />
          </filter>
        </defs>

        {/* ── Pulsing glow behind icon ── */}
        <motion.circle
          cx="30"
          cy="30"
          r="28"
          fill="#76B900"
          opacity="0"
          filter={`url(#${bgGlow})`}
          animate={{ opacity: [0, 0.25, 0] }}
          transition={{ delay: 0.8, duration: 2, repeat: Infinity, repeatDelay: 1.5 }}
        />

        {/* ── Upper swoosh blade ── */}
        <motion.path
          d={UPPER_SWOOSH}
          fill={`url(#${topGrad})`}
          filter={`url(#${glowFilt})`}
          style={{ transformOrigin: "4px 38px" }}
          initial={{ scale: 0, opacity: 0, rotate: -40 }}
          animate={{ scale: 1, opacity: 1, rotate: 0 }}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1], delay: 0.2 }}
        />

        {/* ── Lower swoosh blade ── */}
        <motion.path
          d={LOWER_SWOOSH}
          fill={`url(#${botGrad})`}
          filter={`url(#${glowFilt})`}
          style={{ transformOrigin: "46px 2px" }}
          initial={{ scale: 0, opacity: 0, rotate: 30 }}
          animate={{ scale: 1, opacity: 1, rotate: 0 }}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1], delay: 0.4 }}
        />

        {/* ── Location pin ── */}
        <motion.g
          filter={`url(#${glowFilt})`}
          style={{ transformOrigin: "27px 42px" }}
          initial={{ scale: 0, opacity: 0, y: -20 }}
          animate={{ scale: 1, opacity: 1, y: 0 }}
          transition={{ type: "spring", stiffness: 420, damping: 12, delay: 0.75 }}
        >
          <path d={PIN_PATH} fill={`url(#${pinGrad})`} />
          <circle cx="27" cy="39.5" r="3.2" fill="white" fillOpacity="0.55" />

          {/* Pin continuous float */}
          <motion.g
            animate={{ y: [0, -1.5, 0] }}
            transition={{ duration: 2, repeat: Infinity, repeatDelay: 0.5, ease: "easeInOut", delay: 1.5 }}
          >
            <path d={PIN_PATH} fill={`url(#${pinGrad})`} opacity="0" />
          </motion.g>

          {/* Ground shadow */}
          <motion.ellipse
            cx="27"
            cy="53"
            rx="5"
            ry="1.5"
            fill="rgba(0,0,0,0.08)"
            initial={{ scaleX: 0, opacity: 0 }}
            animate={{ scaleX: 1, opacity: 1 }}
            transition={{ duration: 0.3, delay: 0.95 }}
            style={{ transformOrigin: "27px 53px" }}
          />
        </motion.g>

        {/* ── "Zozi" wordmark — per‑letter reveal ── */}
        {["Z", "o", "z", "i"].map((char, i) => (
          <motion.text
            key={`${char}${i}`}
            x={68 + i * 28}
            y={46}
            style={{
              fontFamily: "'Sora', 'Montserrat', system-ui, sans-serif",
              fontWeight: 700,
              fontSize: "36px",
              letterSpacing: "-0.5px",
            }}
            className="fill-slate-800 dark:fill-slate-100"
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{
              duration: 0.4,
              ease: [0.22, 1, 0.36, 1],
              delay: 0.65 + i * 0.1,
            }}
          >
            {char}
          </motion.text>
        ))}

        {/* ── Green accent dot on "i" ── */}
        <motion.circle
          cx="180"
          cy="19"
          r="3.5"
          fill="#76B900"
          initial={{ scale: 0, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: "spring", stiffness: 600, damping: 10, delay: 1.05 }}
        />
      </svg>

      {/* ── Tagline / subtitle ── */}
      <motion.p
        className="relative z-10 text-lg font-medium tracking-widest uppercase text-slate-400 dark:text-slate-500"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 1.3 }}
      >
        Delivering Everywhere
      </motion.p>
    </motion.div>
  );
}

/* ═══════════════════════════════════════════════════════ */

export default function BrandPage() {
  const [run, setRun] = useState(0);
  const [bg, setBg] = useState<"light" | "dark">("light");

  const replay = useCallback(() => setRun((r) => r + 1), []);

  /* Auto‑play on mount */
  useEffect(() => setRun(1), []);

  const particles = Array.from({ length: 12 }, (_, i) => ({
    delay: i * 0.5,
    x: Math.random() * 80 + 10,
    y: Math.random() * 60 + 20,
    size: Math.random() * 6 + 3,
  }));

  return (
    <div
      className={`relative flex flex-col items-center justify-center min-h-screen overflow-hidden transition-colors duration-500 ${
        bg === "dark"
          ? "bg-slate-950"
          : "bg-linear-to-br from-slate-50 via-white to-slate-100"
      }`}
    >
      {/* Floating particles */}
      {particles.map((p, i) => (
        <Particle key={i} {...p} />
      ))}

      {/* Animated Logo */}
      <AnimatePresence mode="wait">
        <AnimatedShowcase run={run} />
      </AnimatePresence>

      {/* Controls */}
      <motion.div
        className="absolute bottom-10 flex gap-4"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.8 }}
      >
        <Button variant="primary" onClick={replay}>
          Replay Animation
        </Button>
        <button
          onClick={() => setBg((b) => (b === "light" ? "dark" : "light"))}
          className="px-6 py-2.5 rounded-full text-sm font-semibold border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
        >
          {bg === "light" ? "Dark Background" : "Light Background"}
        </button>
      </motion.div>
    </div>
  );
}


