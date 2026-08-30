"use client";
import { motion } from "framer-motion";

/* eslint-disable @typescript-eslint/no-explicit-any */
type FMVariants = Record<string, any>;

export const ENTER_VARIANTS: FMVariants = {
  hidden: { opacity: 0, y: 12 },
  visible: (i: number = 0) => ({ opacity: 1, y: 0, transition: { duration: 0.28, delay: i * 0.04, ease: [0.22, 1, 0.36, 1] } }),
};
export const FADE_SCALE: FMVariants = {
  hidden: { opacity: 0, scale: 0.96 },
  visible: { opacity: 1, scale: 1, transition: { duration: 0.2, ease: "easeOut" } },
  exit: { opacity: 0, scale: 0.96, transition: { duration: 0.15, ease: "easeIn" } },
};
export function Reveal({ children, variant = ENTER_VARIANTS, custom, className }: {
  children: React.ReactNode; variant?: FMVariants; custom?: number; className?: string;
}) {
  return (
    <motion.div initial="hidden" animate="visible" exit="exit" variants={variant} custom={custom} className={className}>
      {children}
    </motion.div>
  );
}
