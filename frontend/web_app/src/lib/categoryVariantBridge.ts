// Bridge between the supplier UI picker categories and the variant config slugs.
// DO NOT edit variantConfig.ts (auto-generated). Import from it here only.
import { getSuggestedVariants, VARIANT_CONFIG } from './variantConfig';

// Picker display name (page.tsx CATEGORIES) -> variant config slug.
export const PICKER_CATEGORY_TO_SLUG: Record<string, string> = {
  'Electronics': 'electronics',
  'Clothing': 'clothing',
  'Home & Garden': 'home',
  'Sports & Outdoors': 'sports',
  'Books': 'books',
  'Beauty & Personal Care': 'beauty',
  'Toys & Games': 'toys',
  'Automotive': 'automotive',
  'Health & Household': 'health',
  'Industrial & Scientific': 'industrial',
  'Other': 'other',
};

// Extra config slugs that should map to a picker category when the slug does not
// exist directly (used to expand coverage for broad picker buckets).
const PICKER_EXTRA_SLUGS: Record<string, string[]> = {
  'Clothing': ['apparel', 'fashion'],
  'Home & Garden': ['furniture', 'kitchen', 'appliances', 'garden'],
  'Sports & Outdoors': ['outdoor'],
  'Beauty & Personal Care': ['cosmetics', 'skincare', 'fragrances'],
  'Automotive': ['automotive_parts'],
};

export function resolveCategorySlug(pickerCategory: string): string {
  if (!pickerCategory) return 'other';
  if (PICKER_CATEGORY_TO_SLUG[pickerCategory]) return PICKER_CATEGORY_TO_SLUG[pickerCategory];
  // Fallback: slugify the picker name and try to match a known config key.
  const slug = pickerCategory.toLowerCase().replace(/[^a-z0-9]/g, '_');
  if (VARIANT_CONFIG[slug]) return slug;
  return 'other';
}

// Axes that are descriptive specs (not physical stock axes like color/size).
// Used to build the tick-box spec selector from the variant config baseline.
const SPEC_AXES = new Set([
  'material', 'pattern', 'gender', 'sleeve_length', 'neckline', 'fit',
  'occasion', 'season', 'closure_type', 'fabric_type', 'weave_type',
  'scent', 'scent_strength', 'volume', 'capacity', 'thread_count',
  'firmness', 'finish_type', 'lighting_type', 'furniture_style', 'room_type',
  'spf', 'skin_type', 'hair_type', 'age_group', 'power_source',
  'screen_size', 'connectivity', 'operating_system', 'storage', 'ram',
]);

export interface SpecGroup {
  key: string;
  label: string;
  options: { id: string; label: string; category: string }[];
}

// Build spec groups for a picker category from the variant config baseline.
// This replaces the hardcoded SPEC_GROUPS in ProductSpecsSelector so every
// category gets meaningful, config-driven spec options.
export function getSpecGroupsForCategory(pickerCategory: string): SpecGroup[] {
  const slug = resolveCategorySlug(pickerCategory);
  const extra = PICKER_EXTRA_SLUGS[pickerCategory] || [];
  const slugs = Array.from(new Set([slug, ...extra]));

  const groups: SpecGroup[] = [];
  const seenGroups = new Set<string>();

  for (const s of slugs) {
    const variants = getSuggestedVariants(s);
    for (const v of variants) {
      if (!SPEC_AXES.has(v.key) || seenGroups.has(v.key)) continue;
      seenGroups.add(v.key);
      groups.push({
        key: v.key,
        label: v.name,
        options: (v.default_options || []).map(o => ({
          id: o.toLowerCase().replace(/[^a-z0-9]+/g, '_'),
          label: o,
          category: v.key,
        })),
      });
    }
  }

  // Guarantee at least the universal spec axes so the selector is never empty.
  if (groups.length === 0) {
    for (const v of getSuggestedVariants('other')) {
      if (!SPEC_AXES.has(v.key) || seenGroups.has(v.key)) continue;
      seenGroups.add(v.key);
      groups.push({
        key: v.key,
        label: v.name,
        options: (v.default_options || []).map(o => ({
          id: o.toLowerCase().replace(/[^a-z0-9]+/g, '_'),
          label: o,
          category: v.key,
        })),
      });
    }
  }

  return groups;
}

// Get the suggested sellable variant axes (color/size/etc.) for a picker category.
// Used to seed the SmartVariantMatrix baseline immediately when a category is known.
export function getBaselineVariants(pickerCategory: string): { key: string; name: string; default_options: string[] }[] {
  return getSuggestedVariants(resolveCategorySlug(pickerCategory)).map(v => ({
    key: v.key,
    name: v.name,
    default_options: v.default_options,
  }));
}

// Derive the initial color×size axes for the matrix from the config baseline.
// Falls back to a single Default×One Size cell when the category has no axes.
export function getMatrixAxes(pickerCategory: string): { colors: string[]; sizes: string[] } {
  const variants = getBaselineVariants(pickerCategory);
  const colorsAxis = variants.find(v => v.key === 'color');
  const sizesAxis = variants.find(v => v.key === 'size');
  const colors = (colorsAxis?.default_options && colorsAxis.default_options.length > 0)
    ? colorsAxis.default_options.slice(0, 6)
    : [];
  const sizes = (sizesAxis?.default_options && sizesAxis.default_options.length > 0)
    ? sizesAxis.default_options.slice(0, 6)
    : [];
  return {
    colors: colors.length ? colors : ['Default'],
    sizes: sizes.length ? sizes : ['One Size'],
  };
}
