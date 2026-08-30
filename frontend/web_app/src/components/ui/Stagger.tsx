"use client";
import { motion } from "framer-motion";

/* eslint-disable @typescript-eslint/no-explicit-any */
type FMVariants = Record<string, any>;

export function staggerItems(delay: number = 0.04): FMVariants {
  return { hidden: {}, visible: { transition: { staggerChildren: delay } } };
}
export function Stagger({ children, stagger = 0.04, className }: {
  children: React.ReactNode; stagger?: number; className?: string;
}) {
  return (
    <motion.div initial="hidden" animate="visible" variants={staggerItems(stagger)} className={className}>
      {children}
    </motion.div>
  );
}
