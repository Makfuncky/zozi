// Auto-generated from zozi_variant_config.json
// Variant configuration data + utility functions.
// Data split into variantConfigData.ts for file-size hygiene.

export * from './variantConfigData';
export function getSuggestedVariants(category: string): Array<{ key: string; name: string; name_ar: string; default_options: string[] }> {
  const cat = category.toLowerCase().replace(/[^a-z0-9]/g, '_');
  const keys = CATEGORY_VARIANTS[cat] || [];
  const direct = VARIANT_CONFIG;
  const results: Array<{ key: string; name: string; name_ar: string; default_options: string[] }> = [];
  const seen = new Set<string>();
  for (const k of keys) {
    if (!seen.has(k) && direct[k]) {
      seen.add(k);
      results.push({ key: k, name: direct[k].name, name_ar: direct[k].name_ar, default_options: direct[k].default_options });
    }
  }
  if (results.length === 0) {
    for (const [vk, v] of Object.entries(direct)) {
      for (const c of v.categories) {
        if (cat.includes(c) || c.includes(cat)) {
          if (!seen.has(vk)) {
            seen.add(vk);
            results.push({ key: vk, name: v.name, name_ar: v.name_ar, default_options: v.default_options });
          }
        }
      }
    }
  }
  return results.slice(0, 8);
}
/**
 * Return applicable variant axes + their default options for a product category.
 * Drives the quantity modal to show correct axes for any product type.
 */
export function getAxesForCategory(
  category: string,
  subcategory?: string
): Array<{ key: string; label: string; options: string[] }> {
  const slug = category.toLowerCase().replace(/[^a-z0-9]/g, '_');
  const extra: Record<string, string[]> = {
    'clothing': ['apparel', 'fashion'],
    'home___garden': ['furniture', 'kitchen', 'appliances', 'garden'],
    'sports___outdoors': ['outdoor'],
    'beauty___personal_care': ['cosmetics', 'skincare', 'fragrances'],
    'automotive': ['automotive_parts'],
  };
  const slugs = [slug, ...(extra[slug] || [])];
  const axes: Array<{ key: string; label: string; options: string[] }> = [];
  const seen = new Set<string>();

  for (const s of slugs) {
    const suggested = getSuggestedVariants(s);
    for (const v of suggested) {
      if (!seen.has(v.key)) {
        seen.add(v.key);
        axes.push({
          key: v.key,
          label: v.name,
          options: v.default_options,
        });
      }
    }
  }
  return axes;
}

/** Return material/fabric options for a given product type. */
export function getMaterialOptions(productType?: string): string[] {
  const mat = VARIANT_CONFIG['material'];
  if (mat?.default_options?.length) return mat.default_options;
  return [
    'Cotton', 'Polyester', 'Leather', 'Silk', 'Wool',
    'Denim', 'Linen', 'Nylon', 'Spandex', 'Velvet',
  ];
}

/**
 * Detect variant axes from a voice extraction result.
 * Returns the axes that should be rendered as quantity pop-ups.
 */
export function detectAxesFromVoice(
  voiceResult: Record<string, any>
): Array<{ key: string; label: string; options: string[] }> {
  const axes: Array<{ key: string; label: string; options: string[] }> = [];
  const variants = voiceResult?.variants || {};
  for (const [key, options] of Object.entries(variants)) {
    const lower = key.toLowerCase();
    const def = VARIANT_CONFIG[lower];
    if (def && Array.isArray(options) && options.length > 0) {
      axes.push({
        key: lower,
        label: def.name,
        options: options as string[],
      });
    }
  }
  return axes;
}
