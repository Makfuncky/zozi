"use client";

import React from "react";
import { Star, Quote } from "lucide-react";
import { motion } from "framer-motion";

const testimonials = [
  {
    name: "Alexander Voss",
    role: "Collector",
    content: "The curation here is unmatched. Finding authentic archival pieces used to be a chore, now it's a ritual.",
    rating: 5,
  },
  {
    name: "Elena Rossi",
    role: "Interior Designer",
    content: "ZOZI has become my primary source for unique architectural objects. The shipping is flawlessly handled.",
    rating: 5,
  },
  {
    name: "Marcus Thorne",
    role: "Supplier",
    content: "As a vendor, the infrastructure provided here allows me to reach global clients seamlessly. Highly recommended.",
    rating: 4.8,
  },
];

export default function TestimonialsWidget() {
  return (
    <section className="py-20 relative overflow-hidden bg-slate-900">
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 relative z-10">
        {/* Header */}
        <div className="flex flex-col items-center text-center mb-12">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-widest text-indigo-400 mb-4 bg-indigo-500/10 border border-indigo-500/20">
            <Star className="w-3 h-3 fill-current" /> 50,000+ Happy Customers
          </div>
          <h2 className="text-3xl md:text-4xl font-bold text-white tracking-tight mb-3">
            What People{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">Are Saying</span>
          </h2>
          <p className="text-slate-500 text-sm max-w-md">Trusted by customers and suppliers across 150+ countries worldwide.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {testimonials.map((t, i) => (
            <motion.div
              key={t.name}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1, duration: 0.5 }}
              className="relative rounded-3xl p-7 group overflow-hidden bg-slate-800 border border-slate-700/60 hover:border-slate-600 transition-colors"
            >
              <Quote className="absolute top-6 right-7 w-9 h-9 opacity-[0.06] group-hover:opacity-[0.12] text-indigo-400 transition-all duration-500" />

              {/* Stars */}
              <div className="flex gap-1 mb-5">
                {Array(5).fill(0).map((_, si) => (
                  <Star key={si} className={`w-3.5 h-3.5 ${si < Math.floor(t.rating) ? "text-amber-400 fill-current" : "text-slate-600"}`} />
                ))}
                <span className="text-[10px] font-bold text-slate-500 ml-1.5">{t.rating}</span>
              </div>

              <p className="text-sm leading-relaxed mb-7 italic text-slate-400">
                &ldquo;{t.content}&rdquo;
              </p>

              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl flex items-center justify-center font-bold text-sm text-white bg-gradient-to-br from-indigo-500 to-purple-500">
                  {t.name.charAt(0)}
                </div>
                <div>
                  <h4 className="text-sm font-bold text-white tracking-tight">{t.name}</h4>
                  <p className="text-[10px] text-slate-500 font-medium uppercase tracking-wider">{t.role}</p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}


