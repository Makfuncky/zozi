"use client";

import { useState } from 'react';
import { X } from '@/lib/icons';
import { getSpecGroupsForCategory, SpecGroup } from '@/lib/categoryVariantBridge';

interface SpecOption {
  id: string;
  label: string;
  category: string;
}

const SPEC_GROUPS: Record<string, { label: string; options: SpecOption[] }> = {
  fabric: {
    label: 'Fabric Type',
    options: [
      { id: 'cotton', label: 'Cotton', category: 'fabric' },
      { id: 'polyester', label: 'Polyester', category: 'fabric' },
      { id: 'blend', label: 'Cotton-Poly Blend', category: 'fabric' },
      { id: 'silk', label: 'Silk', category: 'fabric' },
      { id: 'linen', label: 'Linen', category: 'fabric' },
      { id: 'wool', label: 'Wool', category: 'fabric' },
      { id: 'denim', label: 'Denim', category: 'fabric' },
      { id: 'leather', label: 'Leather', category: 'fabric' },
      { id: 'velvet', label: 'Velvet', category: 'fabric' },
      { id: 'lace', label: 'Lace', category: 'fabric' },
      { id: 'nylon', label: 'Nylon', category: 'fabric' },
      { id: 'spandex', label: 'Spandex', category: 'fabric' },
      { id: 'rayon', label: 'Rayon', category: 'fabric' },
      { id: 'jersey', label: 'Jersey', category: 'fabric' },
      { id: 'other_fabric', label: 'Other', category: 'fabric' },
    ],
  },
  fit: {
    label: 'Fit Type',
    options: [
      { id: 'regular', label: 'Regular', category: 'fit' },
      { id: 'slim', label: 'Slim', category: 'fit' },
      { id: 'oversized', label: 'Oversized', category: 'fit' },
      { id: 'relaxed', label: 'Relaxed', category: 'fit' },
      { id: 'skinny', label: 'Skinny', category: 'fit' },
      { id: 'tapered', label: 'Tapered', category: 'fit' },
      { id: 'straight', label: 'Straight', category: 'fit' },
      { id: 'loose', label: 'Loose', category: 'fit' },
    ],
  },
  sleeve: {
    label: 'Sleeve Length',
    options: [
      { id: 'short', label: 'Short Sleeve', category: 'sleeve' },
      { id: 'long', label: 'Long Sleeve', category: 'sleeve' },
      { id: 'sleeveless', label: 'Sleeveless', category: 'sleeve' },
      { id: 'three_quarter', label: '3/4 Sleeve', category: 'sleeve' },
      { id: 'dolman', label: 'Dolman/Batwing', category: 'sleeve' },
      { id: 'raglan', label: 'Raglan', category: 'sleeve' },
    ],
  },
  care: {
    label: 'Care Instructions',
    options: [
      { id: 'machine_wash', label: 'Machine Wash', category: 'care' },
      { id: 'hand_wash', label: 'Hand Wash', category: 'care' },
      { id: 'dry_clean', label: 'Dry Clean Only', category: 'care' },
      { id: 'tumble_dry', label: 'Tumble Dry Low', category: 'care' },
      { id: 'line_dry', label: 'Line Dry', category: 'care' },
      { id: 'iron_low', label: 'Iron on Low', category: 'care' },
      { id: 'do_not_bleach', label: 'Do Not Bleach', category: 'care' },
      { id: 'wash_cold', label: 'Wash Cold', category: 'care' },
    ],
  },
  gender: {
    label: 'Gender',
    options: [
      { id: 'unisex', label: 'Unisex', category: 'gender' },
      { id: 'men', label: 'Men', category: 'gender' },
      { id: 'women', label: 'Women', category: 'gender' },
      { id: 'kids', label: 'Kids', category: 'gender' },
      { id: 'baby', label: 'Baby', category: 'gender' },
    ],
  },
  occasion: {
    label: 'Occasion',
    options: [
      { id: 'casual', label: 'Casual', category: 'occasion' },
      { id: 'formal', label: 'Formal', category: 'occasion' },
      { id: 'sport', label: 'Sports/Athletic', category: 'occasion' },
      { id: 'party', label: 'Party', category: 'occasion' },
      { id: 'beach', label: 'Beach', category: 'occasion' },
      { id: 'office', label: 'Office Wear', category: 'occasion' },
      { id: 'traditional', label: 'Traditional', category: 'occasion' },
      { id: 'sleepwear', label: 'Sleepwear', category: 'occasion' },
    ],
  },
};

interface ProductSpecsSelectorProps {
  category?: string;
  preselected?: Record<string, string[]>;
  onChange: (specs: Record<string, string[]>) => void;
  onClose?: () => void;
}

export default function ProductSpecsSelector({ category, preselected, onChange }: ProductSpecsSelectorProps) {
  const [selected, setSelected] = useState<Record<string, string[]>>(preselected || {});
  const specGroups: SpecGroup[] = (category ? getSpecGroupsForCategory(category) : []);
  const groups: Record<string, { label: string; options: SpecOption[] }> =
    specGroups.length > 0
      ? Object.fromEntries(specGroups.map(g => [g.key, { label: g.label, options: g.options }]))
      : SPEC_GROUPS;

  const toggle = (group: string, id: string) => {
    setSelected(prev => {
      const current = prev[group] || [];
      const next = current.includes(id)
        ? current.filter(x => x !== id)
        : [...current, id];
      const updated = { ...prev, [group]: next };
      onChange(updated);
      return updated;
    });
  };

  const clearGroup = (group: string) => {
    setSelected(prev => {
      const updated = { ...prev, [group]: [] };
      onChange(updated);
      return updated;
    });
  };

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-text">Product Specifications</h3>
      <p className="text-xs text-text-muted">Tap to select — no typing needed</p>

      <div className="space-y-3">
        {Object.entries(groups).map(([key, group]) => (
          <div key={key} className="p-3 bg-surface-2 rounded-xl border border-border/40">
            <div className="flex items-center justify-between mb-2">
              <p className="text-xs font-medium text-text-muted">{group.label}</p>
              {(selected[key]?.length || 0) > 0 && (
                <button onClick={() => clearGroup(key)}
                  className="text-xs text-gray-400 hover:text-danger transition-colors">
                  Clear
                </button>
              )}
            </div>
            <div className="flex flex-wrap gap-1.5">
              {group.options.map(opt => {
                const isSelected = selected[key]?.includes(opt.id);
                return (
                  <button key={opt.id} onClick={() => toggle(key, opt.id)}
                    className={`px-3 py-1.5 text-xs rounded-lg border transition-all ${
                      isSelected
                        ? 'bg-primary text-white border-primary shadow-sm'
                        : 'bg-surface-1 text-text border-border hover:border-primary/40 hover:text-primary'
                    }`}>
                    {opt.label}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      <div className="p-3 bg-primary/5 rounded-xl border border-primary/10">
        <p className="text-xs text-text-muted">
          Selected: {Object.values(selected).reduce((sum, arr) => sum + arr.length, 0)} options
        </p>
      </div>
    </div>
  );
}
