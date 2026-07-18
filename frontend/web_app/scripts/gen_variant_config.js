const fs = require('fs');
const json = JSON.parse(fs.readFileSync(process.argv[2] || 'D:/Projects/10- E-COMMERCE WEBSITE/zozi/Working_API/zozi_ai_upload_session/zozi_variant_config.json', 'utf8'));
const variants = json.variants;

const catMap = {};
for (const [key, v] of Object.entries(variants)) {
  for (const cat of v.categories || []) {
    if (!catMap[cat]) catMap[cat] = [];
    catMap[cat].push(key);
  }
  for (const pt of v.product_types || []) {
    if (!catMap[pt]) catMap[pt] = [];
    catMap[pt].push(key);
  }
}

const defaultOptions = {
  color: ['Black', 'White', 'Red', 'Blue', 'Green', 'Yellow', 'Orange', 'Purple', 'Pink', 'Brown', 'Grey', 'Navy', 'Beige'],
  size: ['XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL'],
  material: ['Cotton', 'Polyester', 'Leather', 'Silk', 'Wool', 'Denim', 'Linen', 'Nylon', 'Spandex'],
  pattern: ['Solid', 'Striped', 'Floral', 'Plaid', 'Graphic', 'Polka Dot', 'Geometric', 'Abstract', 'Animal Print', 'Camouflage', 'Tie-Dye'],
  gender: ['Men', 'Women', 'Unisex', 'Boys', 'Girls', 'Kids', 'Baby'],
  sleeve_length: ['Short', 'Long', 'Sleeveless', 'Half', 'Three-Quarter'],
  neckline: ['Crew Neck', 'V-Neck', 'Polo', 'Round', 'Square', 'Turtleneck', 'Collared'],
  fit: ['Slim', 'Regular', 'Relaxed', 'Oversized', 'Skinny', 'Straight', 'Loose'],
  closure_type: ['Zipper', 'Button', 'Snap', 'Hook & Loop', 'Buckle', 'Drawstring', 'Lace-Up', 'Magnetic'],
  occasion: ['Casual', 'Formal', 'Sports', 'Party', 'Beach', 'Office', 'Traditional'],
  season: ['Spring', 'Summer', 'Fall', 'Winter', 'All-Season'],
  brand: ['Nike', 'Adidas', 'Samsung', 'Apple', 'Sony', 'Local Brand'],
  storage: ['32GB', '64GB', '128GB', '256GB', '512GB', '1TB'],
  ram: ['4GB', '8GB', '16GB', '32GB', '64GB'],
  screen_size: ['6.1', '6.5', '6.7', '10.2', '13', '15', '16'],
  processor: ['Intel Core i5', 'Intel Core i7', 'AMD Ryzen 5', 'AMD Ryzen 7', 'Apple M1', 'Apple M2'],
  operating_system: ['Windows 11', 'macOS', 'Android', 'iOS', 'Chrome OS'],
  connectivity: ['WiFi', 'Bluetooth', '4G', '5G', 'NFC', 'USB-C', 'HDMI'],
  color_temperature: ['Warm White (2700K)', 'Cool White (4000K)', 'Daylight (5000K)', 'RGB'],
  capacity: ['50L', '100L', '150L', '200L', '250L', '300L', '400L', '500L'],
  weight: ['50g', '100g', '200g', '250g', '500g', '1kg', '2kg', '5kg'],
  volume: ['50ml', '100ml', '150ml', '200ml', '250ml', '500ml', '750ml', '1L', '2L'],
  wattage: ['5W', '10W', '20W', '40W', '60W', '100W', '150W', '200W', '500W'],
  voltage: ['110V', '120V', '220V', '230V', '240V', 'Dual Voltage'],
  skin_type: ['All Skin Types', 'Oily', 'Dry', 'Sensitive', 'Combination', 'Normal'],
  spf: ['SPF 15', 'SPF 30', 'SPF 50', 'SPF 50+'],
  scent: ['Rose', 'Oud', 'Vanilla', 'Jasmine', 'Lavender', 'Citrus', 'Musk', 'Amber'],
  heel_height: ['Flat', 'Low (1-2 inch)', 'Medium (2-3 inch)', 'High (3-4 inch)', 'Extra High (4+)'],
  shoe_width: ['Narrow (A)', 'Medium (B/D)', 'Wide (C/E)', 'Extra Wide (EE/EEE)'],
  age_group: ['0-3 Months', '3-6 Months', '6-12 Months', '1-2 Years', '2-3 Years', '3-5 Years', '5-8 Years', '8-12 Years', 'Teens', 'Adults'],
  toy_type: ['Action Figures', 'Dolls', 'Building Blocks', 'Vehicles', 'Puzzles', 'Board Games', 'Plush Toys', 'Educational'],
  sport_type: ['Football', 'Basketball', 'Tennis', 'Swimming', 'Running', 'Cycling', 'Yoga', 'Gym'],
  car_fitment: ['Universal Fit', 'Custom Fit', 'Toyota', 'Nissan', 'Honda', 'BMW', 'Mercedes'],
  fuel_type: ['Gasoline', 'Diesel', 'Electric', 'Hybrid'],
  transmission: ['Manual', 'Automatic', 'CVT'],
  warranty: ['No Warranty', '30 Days', '90 Days', '6 Months', '1 Year', '2 Years', '3 Years', '5 Years', 'Lifetime'],
  certification: ['Organic', 'Non-GMO', 'Gluten-Free', 'Vegan', 'Halal', 'Kosher', 'CE', 'FCC', 'Energy Star'],
  dietary: ['Vegan', 'Vegetarian', 'Gluten-Free', 'Dairy-Free', 'Nut-Free', 'Sugar-Free', 'Keto', 'Paleo', 'Halal'],
  language: ['English', 'Arabic', 'French', 'Spanish', 'Chinese', 'German', 'Italian', 'Japanese', 'Korean', 'Russian', 'Portuguese', 'Hindi', 'Urdu', 'Turkish'],
  binding: ['Hardcover', 'Paperback', 'Spiral', 'eBook', 'Audiobook'],
  genre: ['Fiction', 'Non-Fiction', 'Mystery', 'Romance', 'Sci-Fi', 'Fantasy', 'Horror', 'Thriller', 'Biography', 'History', 'Self-Help', 'Business', 'Children'],
  power_source: ['Corded', 'Cordless', 'Battery-Operated', 'Rechargeable', 'Solar-Powered', 'Manual', 'USB-Powered'],
  assembly_required: ['No Assembly', 'Minimal Assembly', 'Full Assembly', 'Professional Assembly Required'],
  dimensions: ['Small', 'Medium', 'Large', 'Custom Size'],
  plating: ['Gold', 'Silver', 'Rose Gold', 'Platinum', 'Rhodium', 'Copper', 'Bronze'],
  karat: ['9K', '10K', '14K', '18K', '22K', '24K', '925', '950'],
  gemstone: ['Diamond', 'Ruby', 'Emerald', 'Sapphire', 'Pearl', 'Opal', 'Amethyst'],
  chain_length: ['14 inch', '16 inch', '18 inch', '20 inch', '22 inch', '24 inch'],
  ring_size: ['5', '6', '7', '8', '9', '10', '11', '12'],
  watch_strap: ['Leather', 'Metal', 'Silicone', 'Nylon', 'Rubber', 'Ceramic', 'Stainless Steel', 'Fabric'],
  watch_movement: ['Quartz', 'Automatic', 'Mechanical', 'Solar', 'Smart/Digital'],
  bracelet_size: ['Small', 'Medium', 'Large', 'Adjustable'],
  country_of_origin: ['Made in USA', 'Made in China', 'Made in Germany', 'Made in Italy', 'Made in Japan', 'Made in Oman', 'Made in UAE'],
  condition: ['New', 'Like New', 'Very Good', 'Good', 'Acceptable', 'Refurbished', 'Used', 'Pre-Owned', 'Open Box'],
  grade: ['Premium', 'Standard', 'Economy', 'Grade A', 'Grade B', 'Grade C'],
  quantity_per_pack: ['1', '2', '3', '6', '12', '24', '50', '100'],
  pack_size: ['Single', '2-Pack', '3-Pack', '6-Pack', '12-Pack', 'Family Size', 'Bulk', 'Travel Size'],
  flavor: ['Chocolate', 'Strawberry', 'Vanilla', 'Mint', 'Coffee', 'Original', 'Spicy', 'Sweet', 'Fruity', 'BBQ'],
  year: ['2022', '2023', '2024', '2025', '2026'],
  model: ['2024', '2025', '2026', 'Pro', 'Plus', 'Max', 'Ultra', 'Mini', 'Lite', 'Standard', 'Premium', 'Elite', 'Classic'],
};

const keys = Object.keys(variants);
let out = '// Auto-generated from zozi_variant_config.json\n';
out += 'export interface VariantTypeDef {\n';
out += '  name: string;\n';
out += '  name_ar: string;\n';
out += '  prompt: string;\n';
out += '  categories: string[];\n';
out += '  mutually_exclusive_with: string[];\n';
out += '  default_options: string[];\n';
out += '}\n\n';
out += 'export const VARIANT_CONFIG: Record<string, VariantTypeDef> = {\n';

for (const key of keys) {
  const v = variants[key];
  const opts = JSON.stringify(defaultOptions[key] || []);
  out += '  "' + key + '": {\n';
  out += '    name: ' + JSON.stringify(v.name) + ',\n';
  out += '    name_ar: ' + JSON.stringify(v.name_ar) + ',\n';
  out += '    prompt: ' + JSON.stringify(v.prompt) + ',\n';
  out += '    categories: ' + JSON.stringify(v.categories) + ',\n';
  out += '    mutually_exclusive_with: ' + JSON.stringify(v.mutually_exclusive_with) + ',\n';
  out += '    default_options: ' + opts + ',\n';
  out += '  },\n';
}
out += '};\n\n';

out += 'export const CATEGORY_VARIANTS: Record<string, string[]> = {\n';
for (const [cat, vt] of Object.entries(catMap)) {
  const unique = [...new Set(vt)];
  out += '  "' + cat + '": ' + JSON.stringify(unique) + ',\n';
}
out += '};\n\n';

out += `export function getSuggestedVariants(category: string): Array<{ key: string; name: string; name_ar: string; default_options: string[] }> {
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
`;

const outPath = process.argv[3] || 'D:/Projects/10- E-COMMERCE WEBSITE/zozi/frontend/web_app/src/lib/variantConfig.ts';
fs.writeFileSync(outPath, out);
console.log('Written to ' + outPath);
console.log('Total variant types:', keys.length);
console.log('Total categories mapped:', Object.keys(catMap).length);
