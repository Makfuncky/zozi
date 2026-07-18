"use client";

import { useEffectStore } from "@/lib/effectStore";

/* ─────────────────────────────────────────────────────────────────────────────
   Static data — computed once outside the component so React never re-creates
   these arrays on re-render.
   ───────────────────────────────────────────────────────────────────────────── */

const BALLOON_COLORS = [
  "var(--color-brand-light)", "var(--color-accent-light)", "#d4af37", "var(--color-teal)",
  "var(--color-accent)", "#fb923c", "#f87171", "var(--color-green)",
  "var(--color-brand)", "var(--color-accent-light)",
];

/* 16 balloons spread evenly across the full width */
const BALLOONS = Array.from({ length: 16 }, (_, i) => ({
  id: i,
  left: `${(i * 6.25 + 1).toFixed(1)}%`,
  width: 28 + (i % 5) * 10,
  color: BALLOON_COLORS[i % BALLOON_COLORS.length],
  duration: `${12 + (i % 6) * 2.5}s`,
  delay: `-${((i * 1.7) % 14).toFixed(1)}s`,
}));

const CONFETTI_COLORS = [
  "var(--color-accent)", "#d4af37", "var(--color-brand-light)", "var(--color-accent-light)",
  "var(--color-teal)", "#fb923c", "#86efac", "#f87171",
  "var(--color-yellow)", "var(--color-accent-light)",
];

/* 70 confetti pieces — heavy coverage top-to-bottom */
const CONFETTI = Array.from({ length: 70 }, (_, i) => ({
  id: i,
  left: `${(i * 1.43) % 99}%`,
  color: CONFETTI_COLORS[i % CONFETTI_COLORS.length],
  duration: `${3 + (i % 6) * 0.6}s`,
  delay: `${(i * 0.07) % 5}s`,
  w: 5 + (i % 4) * 3,
  h: i % 3 === 0 ? 5 + (i % 4) * 3 : 9 + (i % 5) * 4,
  isCircle: i % 4 === 0,
  rotation: 30 * (i % 6),
}));

const STAR_POSITIONS = Array.from({ length: 48 }, (_, i) => ({
  id: i,
  top: `${(i * 1.98) % 96}%`,
  left: `${(i * 2.1) % 97}%`,
  size: 2 + (i % 4) * 2,
  delay: `${(i * 0.22) % 5}s`,
  dur: `${2 + (i % 5) * 0.6}s`,
}));

/* 8 lanterns hanging from the top */
const LANTERNS = [
  { left: "4%", delay: "0s", color: "#d4af37" },
  { left: "16%", delay: "0.8s", color: "var(--color-brand-light)" },
  { left: "28%", delay: "1.6s", color: "#f472b6" },
  { left: "40%", delay: "0.4s", color: "#2dd4bf" },
  { left: "60%", delay: "1.2s", color: "#d4af37" },
  { left: "72%", delay: "0s", color: "var(--color-accent)" },
  { left: "84%", delay: "0.9s", color: "#f472b6" },
  { left: "96%", delay: "1.7s", color: "#d4af37" },
];

const EID_ORBS = Array.from({ length: 12 }, (_, i) => ({
  id: i,
  top: `${(i * 8) % 90}%`,
  left: `${5 + (i * 7.5) % 85}%`,
  size: 80 + (i % 4) * 50,
  color: BALLOON_COLORS[i % BALLOON_COLORS.length],
  dur: `${9 + i * 1.2}s`,
  delay: `${(i * 0.4).toFixed(2)}s`,
}));

/* 50 snowflakes — alternate left/right wobble for realism */
const SNOWFLAKES = Array.from({ length: 50 }, (_, i) => ({
  id: i,
  left: `${(i * 2.02) % 99}%`,
  size: 4 + (i % 4) * 3,
  duration: `${9 + (i % 5) * 2.5}s`,
  delay: `${(i * 0.12) % 7}s`,
  cls: i % 2 === 0 ? "snowflake-fall-l" : "snowflake-fall-r",
}));

/* Diwali: 16 diyas with flame glow */
const DIWALI_LAMPS = Array.from({ length: 16 }, (_, i) => ({
  id: i,
  top: `${(i * 5.8) % 90}%`,
  left: `${(i * 6.3) % 95}%`,
  color: ["#ff6b35", "#f7931e", "#ffb627", "#ff4500", "#ffd700"][i % 5],
  size: 18 + (i % 4) * 12,
  delay: `${(i * 0.4) % 4}s`,
  dur: `${5 + (i % 4) * 1.5}s`,
}));

/* New Year: 60 sparkler bits */
const NEWYEAR_SPARKS = Array.from({ length: 60 }, (_, i) => ({
  id: i,
  left: `${(i * 1.68) % 98}%`,
  color: ["#d4af37", "#ffffff", "var(--color-accent)", "var(--color-brand-light)", "var(--color-teal)"][i % 5],
  size: 3 + (i % 3) * 2,
  duration: `${2 + (i % 4) * 0.8}s`,
  delay: `${(i * 0.06) % 4}s`,
}));

export default function BackgroundEffect() {
  const effect = useEffectStore((s) => s.effect);

  if (!effect || effect === "none") return null;

  if (effect === "aurora") {
    return (
      <div
        className="pointer-events-none fixed inset-0 overflow-hidden aurora-bg"
        style={{ zIndex: 0 }}
        aria-hidden="true"
      />
    );
  }

  return (
    <div
      className="pointer-events-none fixed inset-0 overflow-hidden"
      style={{ zIndex: 0 }}
      aria-hidden="true"
    >
      {effect === "balloons" &&
        BALLOONS.map((b) => {
          const h = Math.round(b.width * 1.18);
          const glintW = Math.round(b.width * 0.28);
          const glintH = Math.round(b.width * 0.21);
          const cx = b.width / 2;
          const wobble = b.id % 2 === 0 ? 7 : -7;
          const strH = b.width * 1.8;
          return (
            <div
              key={b.id}
              className="balloon-rise absolute"
              style={{
                left: b.left,
                bottom: "0",
                animationDuration: b.duration,
                animationDelay: b.delay,
              }}
            >
              <div style={{ position: "relative", width: b.width, margin: "0 auto" }}>
                <div
                  style={{
                    width: b.width,
                    height: h,
                    borderRadius: "50% 50% 50% 50% / 58% 58% 42% 42%",
                    background: b.color,
                    opacity: 0.75,
                    position: "relative",
                    boxShadow: `inset ${Math.round(b.width * 0.14)}px ${Math.round(b.width * 0.11)}px 0 rgba(255,255,255,0.38), inset -${Math.round(b.width * 0.09)}px -${Math.round(b.width * 0.09)}px 0 rgba(0,0,0,0.12)`,
                  }}
                >
                  <div
                    style={{
                      position: "absolute",
                      top: "16%",
                      left: "16%",
                      width: glintW,
                      height: glintH,
                      borderRadius: "50%",
                      background: "rgba(255,255,255,0.5)",
                    }}
                  />
                </div>
                <div
                  style={{
                    width: 7,
                    height: 8,
                    background: b.color,
                    opacity: 0.85,
                    borderRadius: "0 0 4px 4px",
                    margin: "0 auto",
                  }}
                />
              </div>
              <svg
                width={b.width}
                height={strH}
                style={{ display: "block", overflow: "visible", margin: "0 auto" }}
              >
                <path
                  d={`M${cx},0 Q${cx + wobble},${strH * 0.45} ${cx},${strH}`}
                  stroke={b.color}
                  strokeWidth="1.4"
                  fill="none"
                  opacity="0.55"
                />
              </svg>
            </div>
          );
        })}

      {effect === "poppers" &&
        CONFETTI.map((c) => (
          <div
            key={c.id}
            className="confetti-fall absolute"
            style={{
              left: c.left,
              top: `-${6 + (c.id % 12)}%`,
              width: c.w,
              height: c.isCircle ? c.w : c.h,
              background: c.color,
              borderRadius: c.isCircle ? "50%" : "3px",
              opacity: 0.85,
              transform: `rotate(${c.rotation}deg)`,
              animationDuration: c.duration,
              animationDelay: c.delay,
            }}
          />
        ))}

      {effect === "ramadan" && (
        <>
          <div style={{ position: "absolute", top: 0, left: "50%", transform: "translateX(-50%)" }}>
            <div className="pendulum-swing" style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
              <div
                style={{
                  width: 2,
                  height: 90,
                  background: "linear-gradient(to bottom, rgba(212,175,55,0.65), rgba(212,175,55,0.15))",
                }}
              />
              <div style={{ position: "relative", width: 100, height: 100 }}>
                <div
                  style={{
                    position: "absolute",
                    inset: 0,
                    borderRadius: "50%",
                    background: "radial-gradient(circle at 38% 38%, rgba(212,175,55,0.4) 0%, rgba(212,175,55,0.08) 100%)",
                    border: "3px solid rgba(212,175,55,0.8)",
                    boxShadow: "0 0 50px rgba(212,175,55,0.4), 0 0 100px rgba(212,175,55,0.2)",
                  }}
                />
                <div
                  className="bg-surface-base"
                  style={{
                    position: "absolute",
                    width: 82,
                    height: 82,
                    borderRadius: "50%",
                    top: -5,
                    left: 22,
                    opacity: 0.97,
                  }}
                />
              </div>
            </div>
          </div>

          {STAR_POSITIONS.map((s) => (
            <div
              key={s.id}
              className="sparkle-pulse absolute"
              style={{
                top: s.top,
                left: s.left,
                width: s.size,
                height: s.size,
                borderRadius: "50%",
                background: "rgba(212,175,55,0.85)",
                boxShadow: "0 0 4px rgba(212,175,55,0.5)",
                animationDelay: s.delay,
                animationDuration: s.dur,
              }}
            />
          ))}

          {LANTERNS.map((l, i) => (
            <div key={`lantern-${i}`} style={{ position: "absolute", top: 0, left: l.left }}>
              <div
                className="lantern-hang"
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  transformOrigin: "50% 0",
                  animationDelay: l.delay,
                }}
              >
                <div
                  style={{
                    width: 1,
                    height: 50,
                    background: `linear-gradient(to bottom, ${l.color}75, ${l.color}15)`,
                  }}
                />
                <div
                  style={{
                    width: 28,
                    height: 6,
                    borderRadius: "3px 3px 0 0",
                    background: `${l.color}60`,
                    border: `1px solid ${l.color}80`,
                  }}
                />
                <div
                  style={{
                    width: 24,
                    height: 44,
                    borderRadius: "3px 3px 14px 14px",
                    background: `radial-gradient(ellipse at 40% 30%, ${l.color}38 0%, ${l.color}10 100%)`,
                    border: `1px solid ${l.color}70`,
                    boxShadow: `0 0 28px ${l.color}55, 0 0 8px ${l.color}30`,
                    position: "relative",
                    overflow: "hidden",
                  }}
                >
                  {[20, 40, 60, 80].map((pct) => (
                    <div
                      key={pct}
                      style={{
                        position: "absolute",
                        left: 0,
                        right: 0,
                        top: `${pct}%`,
                        height: 1,
                        background: `${l.color}35`,
                      }}
                    />
                  ))}
                </div>
                <div style={{ width: 8, height: 12, background: `${l.color}60`, borderRadius: "0 0 4px 4px" }} />
              </div>
            </div>
          ))}
        </>
      )}

      {effect === "eid" && (
        <>
          {STAR_POSITIONS.map((s) => (
            <div
              key={s.id}
              className="sparkle-pulse absolute"
              style={{
                top: s.top,
                left: s.left,
                width: s.size * 1.5,
                height: s.size * 1.5,
                borderRadius: s.id % 5 === 0 ? "0" : "50%",
                transform: s.id % 5 === 0 ? "rotate(45deg) scale(0.7)" : "none",
                background:
                  s.id % 3 === 0
                    ? "rgba(212,175,55,0.8)"
                    : s.id % 3 === 1
                      ? "rgba(255,255,255,0.65)"
                      : "rgba(167,139,250,0.7)",
                boxShadow: s.id % 3 === 0 ? "0 0 6px rgba(212,175,55,0.5)" : "none",
                animationDelay: s.delay,
                animationDuration: s.dur,
              }}
            />
          ))}
          {EID_ORBS.map((o) => (
            <div
              key={o.id}
              className="float-orb absolute"
              style={{
                top: o.top,
                left: o.left,
                width: o.size,
                height: o.size,
                borderRadius: "50%",
                background: o.color,
                opacity: 0.12,
                filter: "blur(30px)",
                animationDuration: o.dur,
                animationDelay: o.delay,
              }}
            />
          ))}
        </>
      )}

      {effect === "christmas" && (
        <>
          {SNOWFLAKES.map((s) => (
            <div
              key={s.id}
              className={`${s.cls} absolute`}
              style={{
                left: s.left,
                top: `-${s.size + 4}px`,
                width: s.size,
                height: s.size,
                borderRadius: "50%",
                background: "rgba(255,255,255,0.88)",
                boxShadow: `0 0 ${s.size}px rgba(255,255,255,0.65)`,
                animationDuration: s.duration,
                animationDelay: s.delay,
              }}
            />
          ))}
          {[
            { color: "#c0392b", top: "15%", left: "5%", size: 220, dur: "14s" },
            { color: "#2ecc71", top: "55%", left: "78%", size: 180, dur: "18s" },
            { color: "#c0392b", top: "75%", left: "30%", size: 240, dur: "12s" },
            { color: "#2ecc71", top: "10%", left: "72%", size: 160, dur: "16s" },
          ].map((o, i) => (
            <div
              key={i}
              className="float-orb absolute"
              style={{
                top: o.top,
                left: o.left,
                width: o.size,
                height: o.size,
                borderRadius: "50%",
                background: o.color,
                opacity: 0.09,
                filter: "blur(45px)",
                animationDuration: o.dur,
              }}
            />
          ))}
        </>
      )}

      {effect === "diwali" && (
        <>
          {DIWALI_LAMPS.map((l) => (
            <div
              key={l.id}
              className="diya-glow absolute"
              style={{
                top: l.top,
                left: l.left,
                animationDuration: l.dur,
                animationDelay: l.delay,
              }}
            >
              <div
                style={{
                  width: l.size * 2.5,
                  height: l.size * 2.5,
                  borderRadius: "50%",
                  background: l.color,
                  opacity: 0.12,
                  filter: "blur(20px)",
                }}
              />
              <div
                style={{
                  position: "absolute",
                  top: "20%",
                  left: "50%",
                  transform: "translateX(-50%)",
                  width: l.size * 0.4,
                  height: l.size * 0.7,
                  borderRadius: "50% 50% 30% 30% / 60% 60% 40% 40%",
                  background: `radial-gradient(ellipse at 50% 80%, ${l.color} 0%, rgba(255,180,0,0.4) 65%, transparent 100%)`,
                  opacity: 0.75,
                }}
              />
            </div>
          ))}
          {[
            { top: "0%", left: "0%", size: 320, color: "#ff6b35" },
            { top: "50%", left: "100%", size: 260, color: "var(--color-accent)" },
            { top: "100%", left: "50%", size: 300, color: "#ff4500" },
          ].map((o, i) => (
            <div
              key={i}
              className="float-orb absolute"
              style={{
                top: o.top,
                left: o.left,
                transform: "translate(-50%,-50%)",
                width: o.size,
                height: o.size,
                borderRadius: "50%",
                background: o.color,
                opacity: 0.08,
                filter: "blur(60px)",
              }}
            />
          ))}
        </>
      )}

      {effect === "newyear" && (
        <>
          {NEWYEAR_SPARKS.map((s) => (
            <div
              key={s.id}
              className="confetti-fall absolute"
              style={{
                left: s.left,
                top: `-${s.size * 2}px`,
                width: s.size,
                height: s.size,
                borderRadius: "50%",
                background: s.color,
                opacity: 0.9,
                boxShadow: `0 0 ${s.size * 2}px ${s.color}`,
                animationDuration: s.duration,
                animationDelay: s.delay,
              }}
            />
          ))}
          {[
            { color: "#d4af37", top: "5%", left: "15%", size: 300, dur: "10s" },
            { color: "var(--color-accent)", top: "5%", left: "75%", size: 260, dur: "13s" },
            { color: "var(--color-brand-light)", top: "70%", left: "5%", size: 220, dur: "11s" },
            { color: "var(--color-teal)", top: "70%", left: "80%", size: 240, dur: "15s" },
          ].map((o, i) => (
            <div
              key={i}
              className="float-orb absolute"
              style={{
                top: o.top,
                left: o.left,
                width: o.size,
                height: o.size,
                borderRadius: "50%",
                background: o.color,
                opacity: 0.1,
                filter: "blur(50px)",
                animationDuration: o.dur,
              }}
            />
          ))}
        </>
      )}
    </div>
  );
}
