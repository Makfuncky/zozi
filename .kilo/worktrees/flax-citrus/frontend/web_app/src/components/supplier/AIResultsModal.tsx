"use client";

import { X, CheckCircle2, Edit3, Plus, ChevronRight, Sparkles } from '@/lib/icons';
import { useState } from 'react';
import type { UploadState } from '@/lib/uploadOrchestrator';

interface AIResultsModalProps {
  state: UploadState;
  onUpdateField: <K extends keyof UploadState>(key: K, value: UploadState[K]) => void;
  onNext: () => void;
  onPhotoEdit: () => void;
  onClose: () => void;
}

const CATEGORIES = [
  'Electronics', 'Clothing', 'Home & Garden', 'Sports & Outdoors',
  'Books', 'Beauty & Personal Care', 'Toys & Games', 'Automotive',
  'Health & Household', 'Industrial & Scientific', 'Other',
];

export default function AIResultsModal({
  state,
  onUpdateField,
  onNext,
  onPhotoEdit,
  onClose,
}: AIResultsModalProps) {
  const [newTag, setNewTag] = useState('');
  const [showCategoryPicker, setShowCategoryPicker] = useState(false);

  const tags = state.tags || [];
  const addTag = () => {
    if (newTag.trim() && !tags.includes(newTag.trim())) {
      onUpdateField('tags', [...tags, newTag.trim()]);
      setNewTag('');
    }
  };
  const removeTag = (tag: string) => {
    onUpdateField('tags', tags.filter(t => t !== tag));
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center theme-overlay" onClick={onClose} role="dialog" aria-modal="true">
      <div className="glass-panel relative w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto rounded-xl border shadow-2xl" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-border sticky top-0 bg-surface-1 z-10">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-primary" />
            <h2 className="text-lg font-semibold text-text">Review Product Details</h2>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-text-faint bg-surface-2 px-2 py-1 rounded-full">
              AI-filled ✓
            </span>
            <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-surface-2 text-text-muted transition-colors">
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        <div className="p-5 space-y-4">
          {/* Image preview */}
          {(state.processedImageUrl || state.imagePreview) && (
            <div className="flex items-center gap-3 p-3 bg-surface-2 rounded-xl">
              <img
                src={state.processedImageUrl || state.imagePreview!}
                alt="Product"
                className="w-16 h-16 rounded-lg object-cover border border-border"
              />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-text truncate">{state.name || 'Product'}</p>
                <p className="text-xs text-text-faint">{state.category || 'Select category'}</p>
              </div>
              <button onClick={onPhotoEdit}
                className="px-3 py-1.5 text-xs font-medium theme-btn-secondary flex items-center gap-1">
                <Edit3 className="w-3 h-3" /> Edit Photo
              </button>
            </div>
          )}

          {/* Product Name */}
          <div>
            <label className="text-xs font-medium text-text-faint mb-1 block">Product Name</label>
            <input type="text" value={state.name}
              onChange={(e) => onUpdateField('name', e.target.value)}
              className="theme-input w-full px-3 py-2 text-sm" placeholder="Enter product name" />
          </div>

          {/* Category */}
          <div>
            <label className="text-xs font-medium text-text-faint mb-1 block">Category</label>
            <div className="relative">
              <button onClick={() => setShowCategoryPicker(!showCategoryPicker)}
                className="theme-input w-full px-3 py-2 text-sm text-left flex items-center justify-between">
                <span className={state.category ? 'text-text' : 'text-text-faint'}>
                  {state.category || 'Select category...'}
                </span>
                <ChevronRight className={`w-4 h-4 text-text-muted transition-transform ${showCategoryPicker ? 'rotate-90' : ''}`} />
              </button>
              {showCategoryPicker && (
                <div className="absolute top-full left-0 right-0 mt-1 bg-surface-1 border border-border rounded-xl shadow-lg z-20 max-h-48 overflow-y-auto">
                  {CATEGORIES.map(cat => (
                    <button key={cat}
                      onClick={() => { onUpdateField('category', cat); setShowCategoryPicker(false); }}
                      className={`w-full px-3 py-2 text-xs text-left hover:bg-surface-2 transition-colors ${
                        state.category === cat ? 'bg-primary/5 text-primary font-medium' : 'text-text-muted'
                      }`}>
                      {cat}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Description */}
          <div>
            <label className="text-xs font-medium text-text-faint mb-1 block">Description</label>
            <textarea value={state.description}
              onChange={(e) => onUpdateField('description', e.target.value)}
              rows={3} className="theme-input w-full px-3 py-2 text-sm resize-none"
              placeholder="Product description..." />
          </div>

          {/* Price */}
          <div>
            <label className="text-xs font-medium text-text-faint mb-1 block">
              Price {state.aiResult?.price_suggestion ? `(AI suggests ${state.aiResult.price_suggestion} OMR)` : ''}
            </label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-text-faint">OMR</span>
              <input type="number" step="0.001" min="0" value={state.price}
                onChange={(e) => onUpdateField('price', e.target.value)}
                className="theme-input w-full pl-14 pr-4 py-2 text-sm" placeholder="0.000" />
            </div>
          </div>

          {/* Colors */}
          {state.colors.length > 0 && (
            <div>
              <label className="text-xs font-medium text-text-faint mb-1.5 block">Colors</label>
              <div className="flex flex-wrap gap-1.5">
                {state.colors.map(c => (
                  <span key={c} className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-primary/5 text-primary text-xs rounded-full border border-primary/20">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: c.toLowerCase() }} />
                    {c}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Sizes */}
          {state.sizes.length > 0 && (
            <div>
              <label className="text-xs font-medium text-text-faint mb-1.5 block">Sizes</label>
              <div className="flex flex-wrap gap-1.5">
                {state.sizes.map(s => (
                  <span key={s} className="px-2.5 py-1 bg-surface-2 text-text text-xs rounded-full border border-border">
                    {s}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Tags */}
          <div>
            <label className="text-xs font-medium text-text-faint mb-1.5 block">Tags</label>
            <div className="flex flex-wrap gap-1.5 mb-2">
              {tags.map(tag => (
                <span key={tag} className="inline-flex items-center gap-1 px-2.5 py-1 bg-accent/5 text-accent text-xs rounded-full border border-accent/20">
                  {tag}
                  <button onClick={() => removeTag(tag)} className="text-accent/60 hover:text-danger">
                    <X className="w-2.5 h-2.5" />
                  </button>
                </span>
              ))}
            </div>
            <div className="flex gap-1.5">
              <input type="text" value={newTag} onChange={(e) => setNewTag(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') addTag(); }}
                placeholder="Add tag..." className="theme-input flex-1 px-2.5 py-1.5 text-xs" />
              <button onClick={addTag}
                className="px-2.5 py-1.5 text-xs theme-btn-secondary flex items-center gap-1">
                <Plus className="w-3 h-3" /> Add
              </button>
            </div>
          </div>

          {/* Total Stock indicator */}
          <div className="p-3 bg-surface-2 rounded-xl flex items-center justify-between">
            <span className="text-xs text-text-muted">Total Stock</span>
            <span className="text-sm font-bold text-text">{state.stockTotal} units</span>
          </div>
        </div>

        {/* Footer action */}
        <div className="p-5 pt-0">
          <button onClick={onNext}
            className="w-full theme-btn-primary py-3 text-sm font-medium flex items-center justify-center gap-2">
            Set Quantities <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
