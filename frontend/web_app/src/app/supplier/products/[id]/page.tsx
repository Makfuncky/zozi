"use client";

import { Button } from "@/components/ui/Button";

import { useState, useEffect, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { motion } from 'framer-motion';
import SupplierLayout from '@/components/SupplierLayout';
import { API_URL, apiFetch } from '@/lib/api';
import { useRequireSupplier } from '@/lib/useAuth';
import { Product } from '@/lib/types';
import {
  ArrowLeft,
  Package,
  Edit,
  Save,
  X,
  Image as ImageIcon,
  Upload,
  DollarSign,
  Hash,
  Tag,
  FileText,
  TrendingUp,
  ShoppingCart,
  Star,
  BarChart3,
  Trash2,
  Eye,
  EyeOff,
  Calendar,
  AlertTriangle
} from 'lucide-react';

export default function SupplierProductDetail() {
  useRequireSupplier();
  const params = useParams();
  const router = useRouter();
  const productId = params?.id as string;

  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [selectedImage, setSelectedImage] = useState<File | null>(null);

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    price: '',
    stock_quantity: '',
    category: '',
    is_active: true
  });

  const categories = [
    'Electronics',
    'Clothing',
    'Home & Garden',
    'Sports & Outdoors',
    'Books',
    'Beauty & Personal Care',
    'Toys & Games',
    'Automotive',
    'Health & Household',
    'Industrial & Scientific',
    'Other'
  ];

  const fetchProduct = useCallback(async () => {
    try {
      const response = await apiFetch(`/supplier/products/${productId}`);

      if (response.ok) {
        const data = await response.json();
        setProduct(data);
        setFormData({
          name: data.name,
          description: data.description,
          price: data.price.toString(),
          stock_quantity: (data.stock ?? 0).toString(),
          category: data.category,
          is_active: data.is_active
        });
        setImagePreview(data.image_url ? `${API_URL}/${data.image_url}` : null);
      } else if (response.status === 404) {
        router.push('/supplier/products');
      } else {
        console.error('Failed to fetch product');
      }
    } catch (error) {
      console.error('Error fetching product:', error);
    } finally {
      setLoading(false);
    }
  }, [productId, router]);

  useEffect(() => {
    fetchProduct();
  }, [fetchProduct]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value
    }));
  };

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedImage(file);
      const reader = new FileReader();
      reader.onload = (e) => {
        setImagePreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const removeImage = () => {
    setSelectedImage(null);
    setImagePreview(product?.image_url ? `${API_URL}/${product.image_url}` : null);
  };

  const handleSave = async () => {
    setSaving(true);

    try {
      const formDataToSend = new FormData();
      formDataToSend.append('name', formData.name);
      formDataToSend.append('description', formData.description);
      formDataToSend.append('price', formData.price);
      formDataToSend.append('stock_quantity', formData.stock_quantity);
      formDataToSend.append('category', formData.category);
      formDataToSend.append('is_active', formData.is_active.toString());

      if (selectedImage) {
        formDataToSend.append('image', selectedImage);
      }

      const response = await apiFetch(`/supplier/products/${productId}`, {
        method: 'PUT',
        body: formDataToSend,
      });

      if (response.ok) {
        const result = await response.json();
        setProduct(result);
        setEditing(false);
        setSelectedImage(null);
      } else {
        const err = await response.json().catch(() => null);
        setError(err?.detail || 'Failed to update product');
      }
    } catch (error) {
      console.error('Error updating product:', error);
      setError('Failed to update product. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this product? This action cannot be undone.')) {
      return;
    }

    setDeleting(true);

    try {
      const response = await apiFetch(`/supplier/products/${productId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        router.push('/supplier/products');
      } else {
        const err = await response.json().catch(() => null);
        setError(err?.detail || 'Failed to delete product');
      }
    } catch (error) {
      console.error('Error deleting product:', error);
      setError('Failed to delete product. Please try again.');
    } finally {
      setDeleting(false);
    }
  };

  const cancelEdit = () => {
    const normalizedPrice = Number(product?.price ?? 0);
    const normalizedStock = Number(product?.stock ?? 0);

    setFormData({
      name: product?.name || '',
      description: product?.description || '',
      price: normalizedPrice.toString(),
      stock_quantity: normalizedStock.toString(),
      category: product?.category || '',
      is_active: product?.is_active || true
    });
    setImagePreview(product?.image_url ? `${API_URL}/${product.image_url}` : null);
    setSelectedImage(null);
    setEditing(false);
  };

  if (loading) {
    return (
      <SupplierLayout>
        <div className="min-h-screen bg-gradient-to-br from-primary via-surface-2 to-accent">
          {/* header via layout */}
          <div className="flex items-center justify-center min-h-[60vh]">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          </div>
        </div>
      </SupplierLayout>
    );
  }

  if (!product) {
    return (
      <SupplierLayout>
        <div className="min-h-screen bg-gradient-to-br from-primary via-surface-2 to-accent">
          {/* header via layout */}
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="text-center">
              <h1 className="text-2xl font-bold text-text mb-4">Product Not Found</h1>
              <Link
                href="/supplier/products"
                className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-brand-dark transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Products
            </Link>
          </div>
        </div>
      </div>
    </SupplierLayout>
    );
  }

  const productPrice = Number(product.price ?? 0);
  const productStock = Number(product?.stock ?? 0);

  return (
    <SupplierLayout>
        <div className="min-h-screen bg-gradient-to-br from-primary via-surface-2 to-accent">
        {/* header via layout */}

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {error && (
            <div className="mb-6 p-3 rounded-xl bg-danger/10 border border-danger/30 text-sm text-danger">
              {error}
            </div>
          )}
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-4">
              <Link
              href="/supplier/products"
              className="flex items-center gap-2 px-4 py-2 bg-white/10 text-text rounded-lg hover:bg-white/20 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Products
            </Link>
            <div>
              <h1 className="text-3xl font-bold text-text">{editing ? 'Edit Product' : product.name}</h1>
              <p className="text-text-muted">
                {editing ? 'Update your product information' : 'Product details and performance'}
              </p>
            </div>
          </div>

          {!editing && (
            <div className="flex gap-3">
              <Button variant="primary" className="flex items-center gap-2 px-4 py-2 rounded-lg hover: transition-colors" onClick={() => setEditing(true)}
              >
                <Edit className="w-4 h-4" />
                Edit Product
              </Button>
              <Button variant="danger" onClick={handleDelete}
                disabled={deleting}>
                {deleting ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                ) : (
                  <Trash2 className="w-4 h-4" />
                )}
                Delete
              </Button>
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Product Information */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="theme-card rounded-2xl p-6"
            >
              <h2 className="text-xl font-bold text-text mb-6 flex items-center gap-2">
                <Package className="w-5 h-5 text-primary" />
                Product Information
              </h2>

              <div className="space-y-6">
                {/* Product Name */}
                <div>
                  <label className="block text-sm font-medium text-text mb-2">
                    Product Name
                  </label>
                  {editing ? (
                    <input
                      type="text"
                      name="name"
                      value={formData.name}
                      onChange={handleInputChange}
                      className="w-full px-4 py-3 rounded-lg theme-input"
                    />
                  ) : (
                    <div className="px-4 py-3 bg-surface-2 rounded-lg text-text">
                      {product.name}
                    </div>
                  )}
                </div>

                {/* Description */}
                <div>
                  <label className="block text-sm font-medium text-text mb-2">
                    Description
                  </label>
                  {editing ? (
                    <textarea
                      name="description"
                      value={formData.description}
                      onChange={handleInputChange}
                      rows={4}
                      className="w-full px-4 py-3 rounded-lg theme-input resize-vertical"
                    />
                  ) : (
                    <div className="px-4 py-3 bg-surface-2 rounded-lg text-text whitespace-pre-wrap">
                      {product.description}
                    </div>
                  )}
                </div>

                {/* Category */}
                <div>
                  <label className="block text-sm font-medium text-text mb-2">
                    Category
                  </label>
                  {editing ? (
                    <select
                      name="category"
                      value={formData.category}
                      onChange={handleInputChange}
                      className="w-full px-4 py-3 rounded-lg theme-input"
                    >
                      {categories.map(category => (
                        <option key={category} value={category}>{category}</option>
                      ))}
                    </select>
                  ) : (
                    <div className="px-4 py-3 bg-surface-2 rounded-lg text-text">
                      {product.category}
                    </div>
                  )}
                </div>

                {/* Price & Stock */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-text mb-2">
                      Price ($)
                    </label>
                    {editing ? (
                      <input
                        type="number"
                        name="price"
                        value={formData.price}
                        onChange={handleInputChange}
                        min="0"
                        step="0.01"
                        className="w-full px-4 py-3 rounded-lg theme-input"
                      />
                    ) : (
                      <div className="px-4 py-3 bg-surface-2 rounded-lg text-text">
                        ${productPrice.toFixed(2)}
                      </div>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-text mb-2">
                      Stock Quantity
                    </label>
                    {editing ? (
                      <input
                        type="number"
                        name="stock_quantity"
                        value={formData.stock_quantity}
                        onChange={handleInputChange}
                        min="0"
                        className="w-full px-4 py-3 rounded-lg theme-input"
                      />
                    ) : (
                      <div className={`px-4 py-3 bg-surface-2 rounded-lg ${
                        productStock <= 10 ? 'text-danger' : 'text-text'
                      }`}>
                        {productStock} units
                        {productStock <= 10 && (
                          <AlertTriangle className="w-4 h-4 inline ml-2" />
                        )}
                      </div>
                    )}
                  </div>
                </div>

                {/* Active Status */}
                <div>
                  <label className="flex items-center gap-3">
                    {editing ? (
                      <input
                        type="checkbox"
                        name="is_active"
                        checked={formData.is_active}
                        onChange={handleInputChange}
                        className="w-4 h-4 text-primary border-border/50 rounded focus:ring-primary"
                      />
                    ) : (
                      <div className={`w-4 h-4 rounded flex items-center justify-center ${
                        product.is_active ? 'bg-success' : 'bg-danger'
                      }`}>
                        {product.is_active ? <Eye className="w-3 h-3 text-white" /> : <EyeOff className="w-3 h-3 text-white" />}
                      </div>
                    )}
                    <span className="text-sm font-medium text-text">
                      {editing ? 'Product is active and visible to customers' : `Product is ${product.is_active ? 'active' : 'inactive'}`}
                    </span>
                  </label>
                </div>
              </div>
            </motion.div>

            {/* Edit Actions */}
            {editing && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="theme-card rounded-2xl p-6"
              >
                <div className="flex flex-col sm:flex-row gap-4 justify-end">
                  <Button variant="primary" onClick={cancelEdit}>
                    Cancel
                  </Button>
                  <Button variant="primary" onClick={handleSave}
                    disabled={saving}>
                    {saving ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                        Saving...
                      </>
                    ) : (
                      <>
                        <Save className="w-4 h-4" />
                        Save Changes
                      </>
                    )}
                  </Button>
                </div>
              </motion.div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Product Image */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="theme-card rounded-2xl p-6"
            >
              <h2 className="text-xl font-bold text-text mb-6 flex items-center gap-2">
                <ImageIcon className="w-5 h-5 text-primary" />
                Product Image
              </h2>

              <div className="space-y-4">
                <div className="border-2 border-dashed border-border/50 rounded-lg p-4">
                  {imagePreview ? (
                    <div className="relative">
                      <img
                        src={imagePreview}
                        alt={product.name}
                        className="w-full h-48 object-cover rounded-lg"
                      />
                      {editing && (
                        <Button variant="danger" type="button"
                          onClick={removeImage}>
                          <X className="w-4 h-4" />
                        </Button>
                      )}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <Package className="w-12 h-12 text-primary/50 mx-auto mb-4" />
                      <div className="text-sm text-text-muted">No image uploaded</div>
                    </div>
                  )}
                </div>

                {editing && (
                  <label className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-brand-dark transition-colors cursor-pointer w-full justify-center">
                    <Upload className="w-4 h-4" />
                    Change Image
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleImageChange}
                      className="hidden"
                    />
                  </label>
                )}
              </div>
            </motion.div>

            {/* Performance Metrics */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="theme-card rounded-2xl p-6"
            >
              <h2 className="text-xl font-bold text-text mb-6 flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-primary" />
                Performance
              </h2>

              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-2">
                    <ShoppingCart className="w-4 h-4 text-info" />
                    <span className="text-sm text-text-muted">Total Sales</span>
                  </div>
                  <span className="font-bold text-text">{product.sales_count || 0}</span>
                </div>

                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-2">
                    <DollarSign className="w-4 h-4 text-success" />
                    <span className="text-sm text-text-muted">Revenue</span>
                  </div>
                  <span className="font-bold text-text">${(product.revenue || 0).toFixed(2)}</span>
                </div>

                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-2">
                    <Star className="w-4 h-4 text-warning" />
                    <span className="text-sm text-text-muted">Rating</span>
                  </div>
                  <span className="font-bold text-text">
                    {product.rating ? `${product.rating.toFixed(1)}/5.0` : 'No ratings'}
                  </span>
                </div>

                <div className="pt-4 border-t border-primary/10">
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-2">
                      <Calendar className="w-4 h-4 text-primary" />
                      <span className="text-sm text-text-muted">Listed</span>
                    </div>
                    <span className="text-sm text-text">
                      {product.created_at ? new Date(product.created_at).toLocaleDateString() : ''}
                    </span>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
    </SupplierLayout>
  );
}