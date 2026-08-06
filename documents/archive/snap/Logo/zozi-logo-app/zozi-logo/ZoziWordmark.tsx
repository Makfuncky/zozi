import { useId, type CSSProperties } from "react";
import { motion } from "motion/react";
import { tokens, type ZoziBaseProps } from "./shared";

export type ZoziWordmarkProps = ZoziBaseProps;

const viewBoxWidth = 430;
const viewBoxHeight = 170;

export default function ZoziWordmark({
  size = 320,
  className,
  animated = true,
  theme = "light",
}: ZoziWordmarkProps) {
  const t = tokens[theme];
  const svgId = useId().replace(/:/g, "");
  const ids = {
    greenGradient: `greenGradient-${svgId}`,
    shadow: `shadow-${svgId}`,
  };

  const wrapperStyle = {
    position: "relative",
    width: `${size}px`,
    height: `${(size * viewBoxHeight) / viewBoxWidth}px`,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0,
  } satisfies CSSProperties;

  return (
    <div className={className} style={wrapperStyle}>
      <motion.svg
        initial={animated ? { opacity: 0, scale: 0.92 } : false}
        animate={{ opacity: 1, scale: 1 }}
        transition={animated ? { duration: 0.8, ease: [0.2, 0, 0.2, 1] } : { duration: 0 }}
        viewBox={`0 0 ${viewBoxWidth} ${viewBoxHeight}`}
        style={{ width: "100%", height: "100%", overflow: "visible" }}
        xmlns="http://www.w3.org/2000/svg"
        aria-label="Zozi wordmark"
        role="img"
      >
        <defs>
          <linearGradient id={ids.greenGradient} x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor={t.zTop} />
            <stop offset="20%" stopColor={t.zMid1} />
            <stop offset="50%" stopColor={t.zMid2} />
            <stop offset="80%" stopColor={t.zMid3} />
            <stop offset="100%" stopColor={t.zBot} />
          </linearGradient>

          <filter id={ids.shadow} x="-20%" y="-30%" width="160%" height="180%">
            <feDropShadow dx="0" dy="8" stdDeviation="7" floodColor={t.wordmarkShadow} />
          </filter>
        </defs>

        {/* One shared group: floats together, casts one shadow */}
        <motion.g
          filter={`url(#${ids.shadow})`}
          animate={animated ? { y: [0, -3, 0] } : { y: 0 }}
          transition={animated ? { duration: 4, repeat: Infinity, ease: "easeInOut" } : { duration: 0 }}
        >
          {/* ── Z icon — gentle ongoing rock after entrance ──────────── */}
          <motion.g
            style={{ transformOrigin: "96px 82px" }}
            animate={animated ? { rotate: [-0.6, 0.6, -0.6] } : {}}
            transition={animated ? { delay: 1.8, duration: 5.5, repeat: Infinity, ease: "easeInOut" } : { duration: 0 }}
          >
            <g transform="translate(18 16) scale(0.78)">
              <motion.path
                initial={animated ? { opacity: 0, x: -24 } : false}
                animate={{ opacity: 1, x: 0 }}
                transition={animated ? { delay: 0.15, duration: 0.55, ease: "easeOut" } : { duration: 0 }}
                d="M 20,40 C 70,15 135,10 188,20 C 191,21 190,23 182,24 C 125,35 65,55 25,70 Z"
                fill={`url(#${ids.greenGradient})`}
              />
              <motion.path
                initial={animated ? { opacity: 0, scale: 0 } : false}
                animate={{ opacity: 1, scale: 1 }}
                transition={animated ? { delay: 0.42, duration: 0.55, ease: "easeOut" } : { duration: 0 }}
                style={{ transformOrigin: "100px 85px" }}
                d="M 182,24 C 110,65 52,115 40,140 C 22,148 20,120 40,102 C 40,100 116,35 188,22 Z"
                fill={`url(#${ids.greenGradient})`}
              />
              <motion.path
                initial={animated ? { opacity: 0, x: 24 } : false}
                animate={{ opacity: 1, x: 0 }}
                transition={animated ? { delay: 0.68, duration: 0.55, ease: "easeOut" } : { duration: 0 }}
                d="M 38,126 C 68,127 115,123 134,121 L 134,124 C 98,135 68,140 38,140 C 24,140 24,126 38,126 Z"
                fill={`url(#${ids.greenGradient})`}
              />
            </g>
          </motion.g>

          {/* ── ozi — translate(-10 0) stays ─────────────────────────── */}
          <g transform="translate(-10 0)">

            {/* o: entrance coin-flip → idle slow breathe (3.2s, scale 1↔1.04) */}
            <motion.g
              style={{ transformOrigin: "200px 85px" }}
              initial={animated ? { opacity: 0, scale: 0.15, rotate: -135 } : false}
              animate={{ opacity: 1, scale: 1, rotate: 0 }}
              transition={animated ? { delay: 0.9, duration: 0.7, ease: [0.34, 1.56, 0.64, 1] } : { duration: 0 }}
            >
              <motion.g
                style={{ transformOrigin: "200px 85px" }}
                animate={animated ? { scale: [1, 1.04, 1] } : {}}
                transition={animated ? { delay: 2.0, duration: 3.2, repeat: Infinity, ease: "easeInOut" } : { duration: 0 }}
              >
                <path
                  fillRule="evenodd"
                  d="M 162,85 A 38,41 0 1 1 238,85 A 38,41 0 1 1 162,85 Z M 177,85 A 23,26 0 1 0 223,85 A 23,26 0 1 0 177,85 Z"
                  fill={`url(#${ids.greenGradient})`}
                />
              </motion.g>
            </motion.g>

            {/* z: entrance slide-left → idle subtle x sway (3.8s, ±1.5px) */}
            <motion.g
              initial={animated ? { opacity: 0, x: -20 } : false}
              animate={{ opacity: 1, x: 0 }}
              transition={animated ? { delay: 1.1, duration: 0.5, ease: [0.2, 0, 0.2, 1] } : { duration: 0 }}
            >
              <motion.g
                animate={animated ? { x: [0, 1.5, 0] } : {}}
                transition={animated ? { delay: 2.2, duration: 3.8, repeat: Infinity, ease: "easeInOut" } : { duration: 0 }}
              >
                <path
                  d="M 248,49 Q 248,44 253,44 L 318,44 Q 323,44 323,49
                     L 323,55 Q 323,60 319,64 L 275,107 Q 271,110 276,110
                     L 318,110 Q 323,110 323,115 L 323,121 Q 323,126 318,126
                     L 253,126 Q 248,126 248,121 L 248,115 Q 248,110 252,107
                     L 296,64 Q 300,60 295,60 L 253,60 Q 248,60 248,55 Z"
                  fill={`url(#${ids.greenGradient})`}
                />
              </motion.g>
            </motion.g>

            {/* i stem: entrance scaleY grow → idle scaleY breathe (4.0s, 1↔1.03) */}
            <motion.g
              style={{ transformOrigin: "345px 68px" }}
              initial={animated ? { opacity: 0, scaleY: 0 } : false}
              animate={{ opacity: 1, scaleY: 1 }}
              transition={animated ? { delay: 1.28, duration: 0.42, ease: [0.2, 0, 0.2, 1] } : { duration: 0 }}
            >
              <motion.g
                style={{ transformOrigin: "345px 97px" }}
                animate={animated ? { scaleY: [1, 1.03, 1] } : {}}
                transition={animated ? { delay: 2.4, duration: 4.0, repeat: Infinity, ease: "easeInOut" } : { duration: 0 }}
              >
                <rect x="336" y="68" width="18" height="58" rx="4" fill={`url(#${ids.greenGradient})`} />
              </motion.g>
            </motion.g>

            {/* i dot: entrance spring drop → idle bounce (2.5s, y 0↔-3) — most lively */}
            <motion.g
              style={{ transformOrigin: "345px 52px" }}
              initial={animated ? { opacity: 0, scale: 0, y: -14 } : false}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              transition={animated ? { delay: 1.5, type: "spring", stiffness: 450, damping: 12 } : { duration: 0 }}
            >
              <motion.g
                animate={animated ? { y: [0, -3, 0] } : {}}
                transition={animated ? { delay: 2.0, duration: 2.5, repeat: Infinity, ease: "easeInOut" } : { duration: 0 }}
              >
                <circle cx="345" cy="52" r="10" fill={`url(#${ids.greenGradient})`} />
              </motion.g>
            </motion.g>

          </g>
        </motion.g>
      </motion.svg>
    </div>
  );
}