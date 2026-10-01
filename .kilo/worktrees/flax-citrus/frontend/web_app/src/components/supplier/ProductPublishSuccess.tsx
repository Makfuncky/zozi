"use client";

import { useRouter } from 'next/navigation';
import { CheckCircle2, BarChart3, Plus, Edit3, Home, Globe, Star } from '@/lib/icons';

interface ProductPublishSuccessProps {
  productId: number;
  productName: string;
  listingScore: number;
  countries: string[];
  onAddAnother: () => void;
  onClose: () => void;
}

export default function ProductPublishSuccess({
  productId,
  productName,
  listingScore,
  countries,
  onAddAnother,
  onClose,
}: ProductPublishSuccessProps) {
  const router = useRouter();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center theme-overlay" onClick={onClose} role="dialog" aria-modal="true">
      <div className="glass-panel rounded-2xl shadow-2xl w-full max-w-md mx-4 overflow-hidden border">
        {/* Success animation */}
        <div className="bg-gradient-to-br from-success/10 to-success/5 p-8 text-center">
          <div className="w-20 h-20 rounded-full bg-success/10 flex items-center justify-center mx-auto mb-4">
            <CheckCircle2 className="w-12 h-12 text-success" />
          </div>
          <h2 className="text-xl font-bold text-text mb-1">Product Published Successfully!</h2>
          <p className="text-sm text-text-muted">Thank you for using ZOZI</p>
        </div>

        <div className="p-5 space-y-4">
          {/* Product info */}
          <div className="p-4 bg-surface-2 rounded-xl">
            <p className="text-xs text-text-muted mb-1">Product ID</p>
            <p className="text-sm font-semibold text-text">#{productId}</p>
            <p className="text-sm text-text-muted mt-1">{productName}</p>
          </div>

          {/* Countries */}
          <div>
            <p className="text-xs font-medium text-text-muted mb-2 flex items-center gap-1.5">
              <Globe className="w-3.5 h-3.5" />
              Available in
            </p>
            <div className="flex flex-wrap gap-1.5">
              {countries.map(c => (
                <span key={c} className="px-2.5 py-0.5 bg-primary/5 text-primary text-xs rounded-full border border-primary/20">
                  {c}
                </span>
              ))}
            </div>
          </div>

          {/* Listing Score */}
          <div className="flex items-center justify-between p-3 bg-amber/5 rounded-xl border border-amber/10">
            <div className="flex items-center gap-2">
              <Star className="w-4 h-4 text-amber-500" />
              <span className="text-xs font-medium text-text-muted">Listing Score</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="h-2 w-24 bg-surface-3 rounded-full overflow-hidden">
                <div className="h-full bg-amber-500 rounded-full transition-all" style={{ width: `${listingScore}%` }} />
              </div>
              <span className="text-xs font-bold text-text">{listingScore}/100</span>
            </div>
          </div>

          {/* Action buttons */}
          <div className="grid grid-cols-2 gap-2.5 pt-2">
            <button onClick={() => router.push(`/supplier/products/${productId}`)}
              className="theme-btn-secondary px-4 py-2.5 text-sm">
              <BarChart3 className="w-4 h-4" /> View Analytics
            </button>
            <button onClick={onAddAnother}
              className="theme-btn-primary px-4 py-2.5 text-sm font-medium">
              <Plus className="w-4 h-4" /> Add Another
            </button>
            <button onClick={() => router.push(`/supplier/products/${productId}/edit`)}
              className="theme-btn-secondary px-4 py-2.5 text-sm">
              <Edit3 className="w-4 h-4" /> Edit Listing
            </button>
            <button onClick={() => router.push('/supplier/products')}
              className="theme-btn-secondary px-4 py-2.5 text-sm">
              <Home className="w-4 h-4" /> Dashboard
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
