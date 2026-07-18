"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import React from "react";
import { ArrowRight, Sparkles } from "lucide-react";

interface HeroProps {
  backgroundImage: string;
  title: React.ReactNode;
  subtitle?: React.ReactNode;
  pillTag?: React.ReactNode;
  primaryCta?: { href: string; label: string };
  secondaryCta?: { href: string; label: string };
  children?: React.ReactNode;
}

function fadeUp(delay = 0) {
  return {
    initial: { opacity: 0, y: 28 },
    whileInView: { opacity: 1, y: 0 },
    transition: { duration: 0.65, delay, ease: [0.16, 1, 0.3, 1] as const },
    viewport: { once: true },
  };
}

export default function Hero({
  backgroundImage,
  title,
  subtitle,
  pillTag,
  primaryCta,
  secondaryCta,
}: HeroProps) {
  return (
    <section className="relative min-h-[92vh] flex items-center justify-center overflow-hidden">
      {/* Background image */}
      <div
        className="absolute inset-0 z-0 bg-cover bg-center"
        style={{ backgroundImage: `url('${backgroundImage}')` }}
      />
      {/* Gradient overlay */}
      <div className="absolute inset-0 z-0 bg-gradient-hero" />

      {/* Content */}
      <div className="relative z-10 max-w-7xl mx-auto px-6 grid grid-cols-12 gap-8 items-center">
        <div className="col-span-12 lg:col-span-8">
          {pillTag && (
            <motion.div {...fadeUp(0)} className="mb-8">
              <span className="pill-tag flex items-center gap-2">
                {pillTag}
              </span>
            </motion.div>
          )}

          <motion.h1 {...fadeUp(0.1)} className="hero-display text-[clamp(3.5rem,9vw,8.5rem)] text-white mb-6">
            {title}
          </motion.h1>

          {subtitle && (
            <motion.p {...fadeUp(0.2)} className="text-lg text-white/50 max-w-lg leading-relaxed mb-10">
              {subtitle}
            </motion.p>
          )}

          {(primaryCta || secondaryCta) && (
            <motion.div {...fadeUp(0.3)} className="flex flex-wrap gap-4 items-center">
              {primaryCta && (
                <Link href={primaryCta.href} passHref>
                  <motion.button
                    whileHover={{ scale: 1.04, y: -2 }}
                    whileTap={{ scale: 0.97 }}
                    className="btn btn-primary flex items-center gap-3 px-8 py-4 text-sm tracking-wide"
                  >
                    <Sparkles className="w-4 h-4" />
                    {primaryCta.label}
                    <ArrowRight className="w-4 h-4" />
                  </motion.button>
                </Link>
              )}
              {secondaryCta && (
                <Link href={secondaryCta.href} passHref>
                  <motion.button
                    whileHover={{ scale: 1.04, y: -2 }}
                    whileTap={{ scale: 0.97 }}
                    className="btn btn-secondary flex items-center gap-3 px-8 py-4 text-sm tracking-wide"
                  >
                    {secondaryCta.label}
                  </motion.button>
                </Link>
              )}
            </motion.div>
          )}
        </div>
      </div>
    </section>
  );
}


