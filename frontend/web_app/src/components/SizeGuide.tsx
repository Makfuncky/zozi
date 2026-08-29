"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Ruler } from "lucide-react";

interface SizeGuideProps {
  isOpen: boolean;
  onClose: () => void;
  category?: string;
}

const SIZE_CHARTS: Record<string, { headers: string[]; rows: string[][] }> = {
  clothing: {
    headers: ["Size", "Chest (in)", "Waist (in)", "Hips (in)"],
    rows: [
      ["XS", "32-34", "26-28", "34-36"],
      ["S", "35-37", "29-31", "37-39"],
      ["M", "38-40", "32-34", "40-42"],
      ["L", "41-43", "35-37", "43-45"],
      ["XL", "44-46", "38-40", "46-48"],
      ["XXL", "47-49", "41-43", "49-51"],
    ],
  },
  shoes: {
    headers: ["US", "UK", "EU", "CM"],
    rows: [
      ["6", "5", "38", "24"],
      ["7", "6", "39", "25"],
      ["8", "7", "41", "26"],
      ["9", "8", "42", "27"],
      ["10", "9", "43", "28"],
      ["11", "10", "45", "29"],
    ],
  },
  default: {
    headers: ["Size", "Chest (in)", "Waist (in)", "Hips (in)"],
    rows: [
      ["XS", "32-34", "26-28", "34-36"],
      ["S", "35-37", "29-31", "37-39"],
      ["M", "38-40", "32-34", "40-42"],
      ["L", "41-43", "35-37", "43-45"],
      ["XL", "44-46", "38-40", "46-48"],
      ["XXL", "47-49", "41-43", "49-51"],
    ],
  },
};

export default function SizeGuide({ isOpen, onClose, category }: SizeGuideProps) {
  if (!isOpen) return null;

  const chart = SIZE_CHARTS[category ?? "default"] ?? SIZE_CHARTS.default;

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center p-4">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="relative z-10 w-full max-w-lg bg-surface-1 rounded-2xl border border-border shadow-2xl overflow-hidden"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-5 border-b border-border">
              <div className="flex items-center gap-3">
                <Ruler className="w-5 h-5 text-primary" />
                <h2 className="text-lg font-semibold text-text-primary">Size Guide</h2>
              </div>
              <button
                onClick={onClose}
                className="p-2 rounded-lg hover:bg-surface-2 transition-colors text-text-faint hover:text-text-primary"
                aria-label="Close size guide"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Content */}
            <div className="p-5 overflow-auto max-h-[60vh]">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border">
                      {chart.headers.map((header) => (
                        <th
                          key={header}
                          className="py-2 px-3 text-left font-semibold text-text-primary"
                        >
                          {header}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {chart.rows.map((row, rowIdx) => (
                      <tr key={rowIdx} className="border-b border-border/50 hover:bg-surface-2/50">
                        {row.map((cell, cellIdx) => (
                          <td
                            key={cellIdx}
                            className={`py-2.5 px-3 ${cellIdx === 0 ? "font-medium text-text-primary" : "text-text-secondary"}`}
                          >
                            {cell}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <p className="mt-4 text-xs text-text-faint">
                Measurements are approximate. If you are between sizes, we recommend ordering the larger size.
              </p>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
