import { useId, type CSSProperties } from "react";
import { motion } from "motion/react";
import { tokens, type ZoziBaseProps } from "./shared";

export type ZoziLogoProps = ZoziBaseProps;

const viewBoxWidth = 200;
const viewBoxHeight = 170;

export default function ZoziLogo({
  size = 190,
  className,
  animated = true,
  theme = "light",
}: ZoziLogoProps) {
  const t = tokens[theme];
  const svgId = useId().replace(/:/g, "");
  const ids = {
    greenGradient: `greenGradient-${svgId}`,
    pinGradient: `pinGradient-${svgId}`,
    shadow: `shadow-${svgId}`,
    flareGradient: `flareGradient-${svgId}`,
    pinReflection: `pinReflection-${svgId}`,
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
        initial={animated ? { opacity: 0, scale: 0.85 } : false}
        animate={{ opacity: 1, scale: 1 }}
        transition={animated ? { duration: 0.8, ease: [0.2, 0, 0.2, 1] } : { duration: 0 }}
        viewBox={`0 0 ${viewBoxWidth} ${viewBoxHeight}`}
        style={{ width: "100%", height: "100%", overflow: "visible" }}
        xmlns="http://www.w3.org/2000/svg"
        aria-label="Zozi logo"
        role="img"
      >
        <defs>
          <linearGradient id={ids.greenGradient} x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%"   stopColor={t.zTop}  />
            <stop offset="20%"  stopColor={t.zMid1} />
            <stop offset="50%"  stopColor={t.zMid2} />
            <stop offset="80%"  stopColor={t.zMid3} />
            <stop offset="100%" stopColor={t.zBot}  />
          </linearGradient>

          <linearGradient id={ids.pinGradient} x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%"   stopColor="#FFF550" />
            <stop offset="35%"  stopColor="#F0C800" />
            <stop offset="75%"  stopColor="#D08C00" />
            <stop offset="100%" stopColor="#A86000" />
          </linearGradient>

          <filter id={ids.shadow} x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="6" stdDeviation="5" floodOpacity={t.shadowOpacity} />
          </filter>

          <radialGradient id={ids.flareGradient} cx="50%" cy="50%" r="50%">
            <stop offset="0%"   stopColor={t.flareColor} stopOpacity={t.flareOpacity} />
            <stop offset="100%" stopColor={t.flareColor} stopOpacity={0} />
          </radialGradient>

          <linearGradient id={ids.pinReflection} x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%"   stopColor={t.pinReflStart} stopOpacity="0.4" />
            <stop offset="100%" stopColor={t.pinReflStart} stopOpacity="0" />
          </linearGradient>
        </defs>

        <motion.g
          filter={`url(#${ids.shadow})`}
          animate={animated ? { y: [0, -4, 0] } : { y: 0 }}
          transition={animated ? { duration: 4, repeat: Infinity, ease: "easeInOut" } : { duration: 0 }}
        >
          <motion.path
            initial={animated ? { opacity: 0, x: -30 } : false}
            animate={{ opacity: 1, x: 0 }}
            transition={animated ? { delay: 0.2, duration: 0.6, ease: "easeOut" } : { duration: 0 }}
            d="M 20,40 C 70,15 135,10 188,20 C 191,21 190,23 182,24 C 125,35 65,55 25,70 Z"
            fill={`url(#${ids.greenGradient})`}
          />

          <motion.path
            initial={animated ? { opacity: 0, scale: 0 } : false}
            animate={{ opacity: 1, scale: 1 }}
            transition={animated ? { delay: 0.5, duration: 0.6, ease: "easeOut" } : { duration: 0 }}
            style={{ transformOrigin: "100px 85px" }}
            d="M 182,24 C 110,65 52,115 40,140 C 22,148 20,120 40,102 C 40,100 116,35 188,22 Z"
            fill={`url(#${ids.greenGradient})`}
          />

          <motion.path
            initial={animated ? { opacity: 0, x: 30 } : false}
            animate={{ opacity: 1, x: 0 }}
            transition={animated ? { delay: 0.8, duration: 0.6, ease: "easeOut" } : { duration: 0 }}
            d="M 38,126 C 68,127 115,123 134,121 L 134,124 C 98,135 68,140 38,140 C 24,140 24,126 38,126 Z"
            fill={`url(#${ids.greenGradient})`}
          />
        </motion.g>

        <motion.g
          initial={animated ? { opacity: 0, scale: 0 } : false}
          animate={{ opacity: 1, scale: 0.7 }}
          transition={animated ? { delay: 1.2, duration: 0.5 } : { duration: 0 }}
          style={{ transformOrigin: "155px 150px" }}
        >
          <motion.g
            animate={
              animated
                ? {
                    opacity: [1, 0.3, 1, 0.3, 1],
                    scale: [1, 0.6, 1, 0.6, 1],
                    x: [0, -18, 0, 18, 0],
                  }
                : { opacity: 1, scale: 1, x: 0 }
            }
            transition={animated ? { duration: 4, repeat: Infinity, ease: "easeInOut" } : { duration: 0 }}
          >
            <ellipse cx="155" cy="150" rx="24" ry="2.5" fill={`url(#${ids.flareGradient})`} />
            <path d="M 147,150 Q 155,166 163,150 Z" fill={`url(#${ids.pinReflection})`} />
          </motion.g>
        </motion.g>

        <motion.g
          initial={animated ? { y: -80, opacity: 0, scale: 0.5 } : false}
          animate={{ y: 0, opacity: 1, scale: 0.7 }}
          transition={
            animated
              ? {
                  delay: 1,
                  type: "spring",
                  stiffness: 240,
                  damping: 18,
                }
              : { duration: 0 }
          }
          style={{ transformOrigin: "155px 150px" }}
        >
          <motion.ellipse
            cx="155"
            cy="150"
            rx="16"
            ry="4"
            fill={t.pinShadowFill}
            opacity={t.pinShadowOpacity}
            animate={
              animated
                ? {
                    scale: [1, 0.6, 1, 0.6, 1],
                    opacity: t.pinShadowLoop,
                    x: [0, -18, 0, 18, 0],
                  }
                : { scale: 1, opacity: Number(t.pinShadowOpacity), x: 0 }
            }
            transition={animated ? { duration: 4, repeat: Infinity, ease: "easeInOut" } : { duration: 0 }}
          />

          <motion.g
            style={{ transformOrigin: "155px 148px" }}
            animate={
              animated
                ? {
                    y: [0, -28, 0, -28, 0],
                    x: [0, -18, 0, 18, 0],
                    rotate: [0, -8, 0, 8, 0],
                    scale: [1, 1.1, 1, 1.1, 1],
                  }
                : { y: 0, x: 0, rotate: 0, scale: 1 }
            }
            transition={animated ? { duration: 4, repeat: Infinity, ease: "easeInOut" } : { duration: 0 }}
          >
            <path
              d="M 155,148 C 139,122 123,106 123,86 C 123,68 137,54 155,54 C 173,54 187,68 187,86 C 187,106 171,122 155,148 Z"
              fill={`url(#${ids.pinGradient})`}
              style={{ filter: "drop-shadow(0px 6px 8px rgba(160, 104, 0, 0.35))" }}
            />
            <path
              d="M 155,145 C 141,120 126,105 126,86 C 126,70 139,57 155,57 C 171,57 184,70 184,86 C 184,105 169,120 155,145 Z"
              fill="none"
              stroke="white"
              strokeWidth="1.5"
              opacity="0.35"
            />
            <circle cx="155" cy="86" r="14" fill="white" />
            <circle cx="155" cy="86" r="14" fill="none" stroke={t.pinHoleStroke} strokeWidth="1.5" />
          </motion.g>
        </motion.g>
      </motion.svg>
    </div>
  );
}
