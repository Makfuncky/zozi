"use client";

import { Button } from "@/components/ui/Button";

import { useState, useEffect, useCallback } from 'react';
import dynamic from 'next/dynamic';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { motion } from 'framer-motion';
import SupplierLayout from '@/components/SupplierLayout';
import { API_URL, apiFetch } from '@/lib/api';

const MapView = dynamic(() => import("@/components/map/MapView"), {
  ssr: false,
  loading: () => (
    <div className="flex h-[200px] items-center justify-center rounded-xl border border-border bg-surface-2 text-xs text-text-faint">
      Loading map…
    </div>
  ),
});
import { useCurrencyStore } from '@/lib/currencyStore';
import { badgeClass } from '@/app/supplier/orders/shared';
import {
  ArrowLeft,
  Package,
  Truck,
  CheckCircle,
  Clock,
  AlertCircle,
  User,
  Mail,
  Phone,
  MapPin,
  Calendar,
  DollarSign,
  RefreshCw,
  MessageSquare,
  Printer,
  Download
} from '@/lib/icons';

interface OrderItem {
  id: number;
  product_id: number;
  quantity: number;
  price: number;
  product_name: string;
  product_image: string;
}

interface Order {
  id: number;
  user_id: number;
  total_amount: number;
  status: string;
  created_at: string;
  customer_name: string;
  customer_email: string;
  customer_phone?: string;
  shipping_address?: string;
  delivery_location?: string;
  delivery_note?: string;
  items: OrderItem[];
}

const statusConfig = {
  pending: { icon: Clock, label: 'Pending' },
  processing: { icon: RefreshCw, label: 'Processing' },
  shipped: { icon: Truck, label: 'Shipped' },
  delivered: { icon: CheckCircle, label: 'Delivered' },
  cancelled: { icon: AlertCircle, label: 'Cancelled' }
};

const statusSteps = [
  { key: 'pending', label: 'Order Received', description: 'Order has been placed' },
  { key: 'processing', label: 'Processing', description: 'Preparing your order' },
  { key: 'shipped', label: 'Shipped', description: 'Order is on the way' },
  { key: 'delivered', label: 'Delivered', description: 'Order completed' }
];

export default function SupplierOrderDetail() {
  const params = useParams();
  const router = useRouter();
  const formatMoney = useCurrencyStore((s) => s.format);
  const orderId = params?.id as string;

  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);
  const [updatingStatus, setUpdatingStatus] = useState(false);

  const fetchOrderDetail = useCallback(async () => {
    try {
      const response = await apiFetch(`/supplier/orders/${orderId}`);

      if (response.ok) {
        const data = await response.json();
        setOrder(data);
      } else if (response.status === 404) {
        router.push('/supplier/orders');
      } else {
        console.error('Failed to fetch order detail');
      }
    } catch (error) {
      console.error('Error fetching order detail:', error);
    } finally {
      setLoading(false);
    }
  }, [orderId, router]);

  useEffect(() => {
    fetchOrderDetail();
  }, [fetchOrderDetail]);

  const updateOrderStatus = async (newStatus: string) => {
    setUpdatingStatus(true);

    try {
      const response = await apiFetch(`/supplier/orders/${orderId}/status`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      });

      if (response.ok) {
        setOrder(prev => prev ? { ...prev, status: newStatus } : null);
      } else {
        console.error('Failed to update order status');
      }
    } catch (error) {
      console.error('Error updating order status:', error);
    } finally {
      setUpdatingStatus(false);
    }
  };

  const getCurrentStepIndex = (status: string) => {
    return statusSteps.findIndex(step => step.key === status);
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

  if (!order) {
    return (
      <SupplierLayout>
        <div className="min-h-screen bg-gradient-to-br from-primary via-surface-2 to-accent">
          {/* header via layout */}
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="text-center">
              <h1 className="text-2xl font-bold text-text mb-4">Order Not Found</h1>
              <Link
                href="/supplier/orders"
                className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-accent transition-colors"
              >
              <ArrowLeft className="w-4 h-4" />
              Back to Orders
            </Link>
          </div>
        </div>
      </div>
    </SupplierLayout>
    );
  }

  const StatusIcon = statusConfig[order.status as keyof typeof statusConfig]?.icon || Clock;
  const statusInfo = statusConfig[order.status as keyof typeof statusConfig] || statusConfig.pending;
  const currentStepIndex = getCurrentStepIndex(order.status);

  return (
    <SupplierLayout>
      <div className="min-h-screen bg-gradient-to-br from-primary via-surface-2 to-accent">
        {/* header via layout */}

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <Link
              href="/supplier/orders"
              className="flex items-center gap-2 px-4 py-2 bg-surface-2 text-text rounded-lg hover:bg-surface-1 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Orders
            </Link>
            <div>
              <h1 className="text-3xl font-bold text-text">Order #{order.id}</h1>
              <p className="text-text-muted">Order details and fulfillment</p>
            </div>
          </div>

          <div className={`px-4 py-2 rounded-full text-sm font-medium flex items-center gap-2 ${badgeClass(order.status)}`}>
            <StatusIcon className="w-4 h-4" />
            {statusInfo.label}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Order Progress */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="theme-card rounded-2xl p-6"
            >
              <h2 className="text-xl font-bold text-text mb-6">Order Progress</h2>

              <div className="relative">
                {/* Progress Line */}
                <div className="absolute top-5 left-5 right-5 h-0.5 bg-border">
                  <div
                    className="h-full bg-gradient-to-r from-primary to-accent transition-all duration-500"
                    style={{ width: `${((currentStepIndex + 1) / statusSteps.length) * 100}%` }}
                  ></div>
                </div>

                {/* Steps */}
                <div className="relative flex justify-between">
                  {statusSteps.map((step, index) => {
                    const isCompleted = index <= currentStepIndex;
                    const isCurrent = index === currentStepIndex;

                    return (
                      <div key={step.key} className="flex flex-col items-center">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all duration-300 ${
                          isCompleted
                            ? 'bg-primary border-primary text-on-brand'
                            : isCurrent
                            ? 'border-primary text-primary bg-surface'
                            : 'border-border text-text-faint bg-surface'
                        }`}>
                          {isCompleted ? <CheckCircle className="w-5 h-5" /> : <Clock className="w-5 h-5" />}
                        </div>
                        <div className="mt-3 text-center">
                          <div className={`text-sm font-medium ${isCompleted || isCurrent ? 'text-text' : 'text-text-muted'}`}>
                            {step.label}
                          </div>
                          <div className="text-xs text-text-muted mt-1 max-w-20">
                            {step.description}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Status Update */}
              <div className="mt-8 pt-6 border-t border-primary/10">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold text-text mb-1">Update Order Status</h3>
                    <p className="text-sm text-text-muted">Change the fulfillment status of this order</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <select
                      value={order.status}
                      onChange={(e) => updateOrderStatus(e.target.value)}
                      disabled={updatingStatus}
                      className="px-4 py-2 rounded-lg theme-input disabled:opacity-50"
                    >
                      <option value="pending">Pending</option>
                      <option value="processing">Processing</option>
                      <option value="shipped">Shipped</option>
                      <option value="delivered">Delivered</option>
                      <option value="cancelled">Cancelled</option>
                    </select>
                    {updatingStatus && (
                      <RefreshCw className="w-5 h-5 animate-spin text-primary" />
                    )}
                  </div>
                </div>
              </div>
            </motion.div>

            {/* Order Items */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="theme-card rounded-2xl p-6"
            >
              <h2 className="text-xl font-bold text-text mb-6">Your Products in this Order</h2>

              <div className="space-y-4">
                {order.items.map((item) => (
                  <div key={item.id} className="flex items-center gap-4 p-4 bg-surface-2 rounded-lg">
                    <div className="w-16 h-16 bg-surface-2 rounded-lg flex items-center justify-center flex-shrink-0">
                      {item.product_image ? (
                        <img
                          src={`${API_URL}/${item.product_image}`}
                          alt={item.product_name}
                          className="w-full h-full object-cover rounded-lg"
                        />
                      ) : (
                        <Package className="w-8 h-8 text-text-faint" />
                      )}
                    </div>

                    <div className="flex-1">
                      <h3 className="font-semibold text-text">{item.product_name}</h3>
                      <div className="flex items-center gap-4 mt-1 text-sm text-text-muted">
                        <span>Quantity: {item.quantity}</span>
                        <span>Price: {formatMoney(item.price)}</span>
                        <span className="font-medium text-primary">
                          Subtotal: {formatMoney(item.quantity * item.price)}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Order Total */}
              <div className="mt-6 pt-4 border-t border-primary/10">
                <div className="flex justify-between items-center">
                  <span className="text-lg font-semibold text-text">Your Portion Total</span>
                  <span className="text-2xl font-bold text-primary">
                    {formatMoney(order.items.reduce((total, item) => total + (item.quantity * item.price), 0))}
                  </span>
                </div>
              </div>
            </motion.div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Customer Information */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="theme-card rounded-2xl p-6"
            >
              <h2 className="text-xl font-bold text-text mb-6">Customer Information</h2>

              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <User className="w-5 h-5 text-primary" />
                  <div>
                    <div className="font-medium text-text">{order.customer_name}</div>
                    <div className="text-sm text-text-muted">Customer</div>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <Mail className="w-5 h-5 text-primary" />
                  <div>
                    <div className="font-medium text-text">{order.customer_email}</div>
                    <div className="text-sm text-text-muted">Email</div>
                  </div>
                </div>

                {order.customer_phone && (
                  <div className="flex items-center gap-3">
                    <Phone className="w-5 h-5 text-primary" />
                    <div>
                      <div className="font-medium text-text">{order.customer_phone}</div>
                      <div className="text-sm text-text-muted">Phone</div>
                    </div>
                  </div>
                )}
              </div>

              {/* Quick Actions */}
              <div className="mt-6 pt-4 border-t border-primary/10">
                <h3 className="font-semibold text-text mb-3">Quick Actions</h3>
                <div className="space-y-2">
                  <Button variant="primary">
                    <MessageSquare className="w-4 h-4" />
                    Contact Customer
                  </Button>
                  <Button variant="accent">
                    <Printer className="w-4 h-4" />
                    Print Shipping Label
                  </Button>
                  <button className="w-full flex items-center gap-2 px-4 py-2 bg-surface-1 text-text rounded-lg hover:bg-surface-2 transition-colors">
                    <Download className="w-4 h-4" />
                    Download Invoice
                  </button>
                </div>
              </div>
            </motion.div>

            {/* Shipping Information */}
            {(order.shipping_address || order.delivery_location) && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="theme-card rounded-2xl p-6"
              >
                <h2 className="text-xl font-bold text-text mb-6">Delivery Details</h2>

                {order.shipping_address && (
                  <div className="flex items-start gap-3 mb-3">
                    <MapPin className="w-5 h-5 text-primary mt-0.5" />
                    <div className="text-sm text-text whitespace-pre-line">
                      {order.shipping_address}
                    </div>
                  </div>
                )}
                {order.delivery_note && (
                  <details className="mb-3 text-xs text-text-muted">
                    <summary className="cursor-pointer font-medium">Delivery note</summary>
                    <p className="mt-1 whitespace-pre-wrap">{order.delivery_note}</p>
                  </details>
                )}
                {order.delivery_location && (
                  <MapView
                    location={order.delivery_location}
                    height="200px"
                    markerLabel="Drop-off"
                    markerColor="#e11d48"
                  />
                )}
              </motion.div>
            )}

            {/* Order Summary */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="theme-card rounded-2xl p-6"
            >
              <h2 className="text-xl font-bold text-text mb-6">Order Summary</h2>

              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-text-muted">Order ID</span>
                  <span className="font-medium text-text">#{order.id}</span>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-text-muted">Order Date</span>
                  <span className="font-medium text-text">
                    {new Date(order.created_at).toLocaleDateString()}
                  </span>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-text-muted">Status</span>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${badgeClass(order.status)}`}>
                    {statusInfo.label}
                  </span>
                </div>

                <div className="flex justify-between items-center pt-3 border-t border-primary/10">
                  <span className="font-semibold text-text">Your Revenue</span>
                  <span className="font-bold text-primary">
                    {formatMoney(order.items.reduce((total, item) => total + (item.quantity * item.price), 0))}
                  </span>
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