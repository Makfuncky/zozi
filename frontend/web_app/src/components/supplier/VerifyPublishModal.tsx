"use client";

import { X, CheckCircle2, Edit3, Upload, ImageIcon, Globe, Star, Package, DollarSign, Sparkles } from '@/lib/icons';

interface VerifyPublishModalProps {
  productName: string;
  category: string;
  colors: string[];
  variantsSummary: string;
  totalStock: number;
  price: string;
  description: string;
  imagesCount: number;
  hasVideo: boolean;
  tags: string[];
  imagePreview: string | null;
  processedImageUrl: string | null;
  publishing: boolean;
  onEditDetails: () => void;
  onEditImages: () => void;
  onPublish: () => void;
  onClose: () => void;
}

export default function VerifyPublishModal({
  productName,
  category,
  colors,
  variantsSummary,
  totalStock,
  price,
  description,
  imagesCount,
  hasVideo,
  tags,
  imagePreview,
  processedImageUrl,
  publishing,
  onEditDetails,
  onEditImages,
  onPublish,
  onClose,
}: VerifyPublishModalProps) {
  const colorCount = colors.length;
  const previewSrc = processedImageUrl || imagePreview;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center theme-overlay" onClick={onClose} role="dialog" aria-modal="true" aria-label="Review and publish product">
      <div className="glass-panel relative w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto rounded-xl border shadow-2xl" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-border sticky top-0 bg-surface-1 z-10">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-success" />
            <h2 className="text-lg font-semibold text-text">Review &amp; Publish</h2>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-surface-2 text-text-muted hover:text-text transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-5 space-y-4">
          {/* Product preview card */}
          <div className="flex items-start gap-4 p-4 bg-gradient-to-br from-primary/5 to-accent/5 rounded-xl border border-primary/10">
            {previewSrc && (
              <img src={previewSrc} alt="Product" className="w-20 h-20 rounded-lg object-cover border border-border shrink-0" />
            )}
            <div className="flex-1 min-w-0">
              <h3 className="text-base font-semibold text-text truncate">{productName || 'Product'}</h3>
              <p className="text-xs text-text-muted mt-0.5">{category || 'Uncategorized'}</p>
              <div className="flex flex-wrap gap-1.5 mt-2">
                {colors.slice(0, 4).map(c => (
                  <span key={c} className="inline-flex items-center gap-1 px-2 py-0.5 bg-surface-2 text-text-muted text-[10px] rounded-full border border-border/50">
                    <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: c.toLowerCase() }} />
                    {c}
                  </span>
                ))}
                {colorCount > 4 && (
                  <span className="px-2 py-0.5 bg-surface-2 text-text-faint text-[10px] rounded-full">+{colorCount - 4}</span>
                )}
              </div>
            </div>
          </div>

          {/* Stats grid */}
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 bg-surface-2 rounded-xl">
              <div className="flex items-center gap-1.5 text-xs text-text-faint mb-1">
                <Package className="w-3.5 h-3.5" />
                <span>Variants</span>
              </div>
              <p className="text-sm font-semibold text-text">{variantsSummary || 'None'}</p>
            </div>
            <div className="p-3 bg-surface-2 rounded-xl">
              <div className="flex items-center gap-1.5 text-xs text-text-faint mb-1">
                <DollarSign className="w-3.5 h-3.5" />
                <span>Price</span>
              </div>
              <p className="text-sm font-semibold text-text">{price || 'Not set'}</p>
            </div>
            <div className="p-3 bg-surface-2 rounded-xl">
              <div className="flex items-center gap-1.5 text-xs text-text-faint mb-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Total Stock</span>
              </div>
              <p className="text-sm font-bold text-text">{totalStock} units</p>
            </div>
            <div className="p-3 bg-surface-2 rounded-xl">
              <div className="flex items-center gap-1.5 text-xs text-text-faint mb-1">
                <ImageIcon className="w-3.5 h-3.5" />
                <span>Media</span>
              </div>
              <p className="text-sm font-semibold text-text">{imagesCount} image{imagesCount !== 1 ? 's' : ''}{hasVideo ? ' + video' : ''}</p>
            </div>
          </div>

          {/* Tags */}
          {tags.length > 0 && (
            <div>
              <p className="text-xs font-medium text-text-faint mb-1.5">Tags</p>
              <div className="flex flex-wrap gap-1.5">
                {tags.map(t => (
                  <span key={t} className="px-2 py-0.5 bg-accent/5 text-accent text-[10px] rounded-full border border-accent/20">{t}</span>
                ))}
              </div>
            </div>
          )}

          {/* Description */}
          {description && (
            <div>
              <p className="text-xs font-medium text-text-faint mb-1">Description</p>
              <p className="text-xs text-text-muted leading-relaxed line-clamp-3">{description}</p>
            </div>
          )}

          {/* Listing quality */}
          <div className="p-3 bg-amber/5 rounded-xl border border-amber/10 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Star className="w-4 h-4 text-amber-500" />
              <span className="text-xs font-medium text-text-muted">Listing Quality</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="h-1.5 w-20 bg-surface-3 rounded-full overflow-hidden">
                <div className="h-full bg-amber-500 rounded-full"
                  style={{ width: `${Math.min(100, 40 + (productName ? 15 : 0) + (description ? 10 : 0) + (category ? 10 : 0) + (tags.length > 0 ? 5 : 0) + (colors.length > 0 ? 5 : 0) + (previewSrc ? 10 : 0) + (price ? 5 : 0))}%` }}
                />
              </div>
              <span className="text-[10px] font-bold text-text">
                {Math.min(100, 40 + (productName ? 15 : 0) + (description ? 10 : 0) + (category ? 10 : 0) + (tags.length > 0 ? 5 : 0) + (colors.length > 0 ? 5 : 0) + (previewSrc ? 10 : 0) + (price ? 5 : 0))}/100
              </span>
            </div>
          </div>
        </div>

        {/* Action buttons */}
        <div className="p-5 pt-0 flex flex-col gap-2.5">
          <button
            onClick={onPublish}
            disabled={publishing}
            className="w-full theme-btn-primary py-3 text-sm font-medium flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {publishing ? (
              <>
                <span className="w-4 h-4 rounded-full border-2 border-white/30 border-t-white animate-spin" />
                Publishing...
              </>
            ) : (
              <>
                <Upload className="w-4 h-4" />
                Publish Product
              </>
            )}
          </button>

          <div className="grid grid-cols-2 gap-2.5">
            <button onClick={onEditDetails} disabled={publishing}
              className="theme-btn-secondary px-4 py-2.5 text-sm flex items-center justify-center gap-1.5 disabled:opacity-50">
              <Edit3 className="w-4 h-4" /> Edit Details
            </button>
            <button onClick={onEditImages} disabled={publishing}
              className="theme-btn-secondary px-4 py-2.5 text-sm flex items-center justify-center gap-1.5 disabled:opacity-50">
              <ImageIcon className="w-4 h-4" /> Edit Images
            </button>
          </div>

          <p className="text-xs text-text-faint text-center pt-1">
            <Sparkles className="w-3 h-3 inline mr-1" />
            Thank you for using ZOZI!
          </p>
        </div>
      </div>
    </div>
  );
}
