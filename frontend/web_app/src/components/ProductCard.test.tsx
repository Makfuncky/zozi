import { Product } from '@shared/types';
import { mapProductToCardModel } from '@shared/productCardModel';

const defaultProduct: Product = {
  id: 42,
  name: 'Test Product',
  description: 'A great item',
  price: 39.99,
  category: 'general',
  image_url: 'https://placehold.co/400x400',
  stock: 5,
  supplier: 'Test Supplier',
  color: 'blue',
  isNew: true,
  isFeatured: false,
};

describe('ProductCard helper mapping', () => {
  it('returns rich model fields for web/mobile adaptation', () => {
    const model = mapProductToCardModel(defaultProduct, (p) => `$${p.toFixed(2)}`, (p) => p.supplier || 'ZOZI CURATED');

    expect(model.name).toBe('Test Product');
    expect(model.formattedPrice).toBe('$39.99');
    expect(model.inStock).toBe(true);
    expect(model.badges).toContain('NEW');
  });
});


