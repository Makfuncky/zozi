"use client";

import { X, CheckCircle2, Edit3, Upload, ImageIcon } from '@/lib/icons';

interface ProductSummary {
  name: string;
  category: string;
  colors: string[];
  variants: string;
  totalStock: number;
  price: string;
  description: string;
  imagesCount: number;
  hasVideo: boolean;
  tags: string[];
}

interface VerificationPopupProps {
  summary: ProductSummary;
  onEditDetails: () => void;
  onUpload: () => void;
  onEditImages: () => void;
  onClose: () => void;
}

export default function VerificationPopup({
  summary,
  onEditDetails,
  onUpload,
  onEditImages,
  onClose,
}: VerificationPopupProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center theme-overlay" onClick={onClose} role="dialog" aria-modal="true" aria-label="Review your product">
      <div className="glass-panel relative w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto rounded-xl border shadow-2xl" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-border sticky top-0 bg-surface-1 z-10">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-success" />
            <h2 className="text-lg font-semibold text-text">Review Your Product</h2>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-surface-2 text-text-muted hover:text-text transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Summary card */}
        <div className="p-5 space-y-4">
          <div className="bg-gradient-to-br from-primary/5 to-accent/5 rounded-xl p-4 border border-primary/10">
            <h3 className="text-base font-semibold text-text mb-1">{summary.name || "Product"}</h3>
            <div className="flex flex-wrap items-center gap-1.5 mt-2">
              <span className="px-2 py-0.5 bg-primary/10 text-primary text-xs rounded-full">{summary.category || "General"}</span>
              {summary.colors.slice(0, 4).map(c => (
                <span key={c} className="px-2 py-0.5 bg-surface-2 text-text-muted text-xs rounded-full">{c}</span>
              ))}
              {summary.colors.length > 4 && (
                <span className="px-2 py-0.5 bg-surface-2 text-text-faint text-xs rounded-full">+{summary.colors.length - 4}</span>
              )}
            </div>
          </div>

          {/* Details grid */}
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 bg-surface-2 rounded-xl">
              <p className="text-xs text-text-faint">Variants</p>
              <p className="text-sm font-medium text-text mt-0.5">{summary.variants || "None"}</p>
            </div>
            <div className="p-3 bg-surface-2 rounded-xl">
              <p className="text-xs text-text-faint">Total Stock</p>
              <p className="text-sm font-medium text-text mt-0.5">{summary.totalStock} units</p>
            </div>
            <div className="p-3 bg-surface-2 rounded-xl">
              <p className="text-xs text-text-faint">Price</p>
              <p className="text-sm font-medium text-text mt-0.5">{summary.price || "Not set"}</p>
            </div>
            <div className="p-3 bg-surface-2 rounded-xl">
              <p className="text-xs text-text-faint">Media</p>
              <p className="text-sm font-medium text-text mt-0.5">
                {summary.imagesCount} images{summary.hasVideo ? ' + 1 video' : ''}
              </p>
            </div>
          </div>

          {/* Tags */}
          {summary.tags.length > 0 && (
            <div>
              <p className="text-xs font-medium text-text-faint mb-1.5">Tags</p>
              <div className="flex flex-wrap gap-1.5">
                {summary.tags.map(t => (
                  <span key={t} className="px-2 py-0.5 bg-surface-2 text-text-muted text-xs rounded-full">{t}</span>
                ))}
              </div>
            </div>
          )}

          {/* Description */}
          {summary.description && (
            <div>
              <p className="text-xs font-medium text-text-faint mb-1">Description</p>
              <p className="text-xs text-text-muted leading-relaxed">{summary.description}</p>
            </div>
          )}
        </div>

        {/* Action buttons */}
        <div className="p-5 pt-0 flex flex-col gap-2.5">
          <button onClick={onUpload}
            className="w-full theme-btn-primary py-3 text-sm font-medium">
            <Upload className="w-4 h-4" /> Upload Product
          </button>

          <div className="grid grid-cols-2 gap-2.5">
            <button onClick={onEditDetails}
              className="theme-btn-secondary px-4 py-2.5 text-sm">
              <Edit3 className="w-4 h-4" /> Edit Details
            </button>
            <button onClick={onEditImages}
              className="theme-btn-secondary px-4 py-2.5 text-sm">
              <ImageIcon className="w-4 h-4" /> Edit Images
            </button>
          </div>

          <p className="text-xs text-text-faint text-center mt-1">
            Thank you for using ZOZI!
          </p>
        </div>
      </div>
    </div>
  );
}
