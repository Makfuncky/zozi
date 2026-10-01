"use client";

import { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Search, ChevronRight, Package, CreditCard, Truck, Shield, HelpCircle, Mail, MessageCircle } from "lucide-react";

const FAQ_ITEMS = [
  { q: "How do I place an order?", a: "Browse products, add items to cart, proceed to checkout, select payment method and delivery address, then confirm your order." },
  { q: "What payment methods do you accept?", a: "We accept Cash on Delivery (COD), credit/debit cards (Stripe), Tap, PayTabs, and Thawani depending on your country." },
  { q: "How long does delivery take?", a: "Delivery time depends on your location and the supplier. Standard delivery is 3-7 business days. Express options may be available." },
  { q: "Can I return a product?", a: "Yes, most products can be returned within 14 days of delivery. Go to your Orders page and request a return." },
  { q: "How do I track my order?", a: "Go to your Orders page and click on the order number to see real-time tracking information." },
  { q: "Is my payment information secure?", a: "Yes, we use industry-standard encryption and never store your full card details. Payments are processed by PCI-compliant providers." },
  { q: "How do I become a supplier?", a: "Register as a supplier from the login page, complete your profile verification, and start listing products." },
  { q: "Do you ship internationally?", a: "We ship to multiple countries in the GCC and MENA region. Check the available countries selector in the header." },
];

const CATEGORIES = [
  { icon: Package, title: "Orders", desc: "Placing, modifying, and canceling orders", href: "/orders" },
  { icon: Truck, title: "Shipping & Delivery", desc: "Delivery times, tracking, and shipping costs", href: "/orders" },
  { icon: CreditCard, title: "Payments", desc: "Payment methods, invoices, and refunds", href: "/orders" },
  { icon: Shield, title: "Returns & Refunds", desc: "Return policy and refund processing", href: "/returns" },
];

export default function HelpPage() {
  const [search, setSearch] = useState("");
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  const filteredFaqs = FAQ_ITEMS.filter(
    (item) =>
      item.q.toLowerCase().includes(search.toLowerCase()) ||
      item.a.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-surface-0">
      {/* Hero */}
      <div className="bg-gradient-to-br from-primary/10 via-surface-0 to-accent/5 py-16 px-4">
        <div className="max-w-3xl mx-auto text-center">
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-4xl md:text-5xl font-display font-bold text-text-primary mb-4"
          >
            How can we help?
          </motion.h1>
          <p className="text-text-secondary text-lg mb-8">
            Search our knowledge base or browse categories below.
          </p>
          <div className="relative max-w-xl mx-auto">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-text-faint w-5 h-5" />
            <input
              type="text"
              placeholder="Search for answers..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-12 pr-4 py-3 rounded-xl bg-surface-1 border border-border focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none text-text-primary"
            />
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 py-12">
        {/* Categories */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-12">
          {CATEGORIES.map((cat) => (
            <Link
              key={cat.title}
              href={cat.href}
              className="p-5 rounded-xl border border-border bg-surface-0 hover:border-primary/30 hover:shadow-md transition-all group"
            >
              <cat.icon className="w-8 h-8 text-primary mb-3" />
              <h3 className="font-semibold text-text-primary mb-1 group-hover:text-primary transition-colors">
                {cat.title}
              </h3>
              <p className="text-sm text-text-secondary">{cat.desc}</p>
            </Link>
          ))}
        </div>

        {/* FAQ */}
        <h2 className="text-2xl font-display font-bold text-text-primary mb-6">
          Frequently Asked Questions
        </h2>
        <div className="space-y-3">
          {filteredFaqs.length === 0 ? (
            <p className="text-text-secondary py-8 text-center">No results found for "{search}"</p>
          ) : (
            filteredFaqs.map((item, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.05 }}
                className="border border-border rounded-xl overflow-hidden bg-surface-0"
              >
                <button
                  onClick={() => setOpenIndex(openIndex === idx ? null : idx)}
                  className="w-full flex items-center justify-between p-5 text-left hover:bg-surface-1/50 transition-colors"
                >
                  <span className="font-medium text-text-primary pr-4">{item.q}</span>
                  <ChevronRight className={`w-5 h-5 text-text-faint shrink-0 transition-transform ${openIndex === idx ? "rotate-90" : ""}`} />
                </button>
                {openIndex === idx && (
                  <div className="px-5 pb-5 text-text-secondary text-sm leading-relaxed border-t border-border pt-4">
                    {item.a}
                  </div>
                )}
              </motion.div>
            ))
          )}
        </div>

        {/* Contact */}
        <div className="mt-12 p-8 rounded-2xl bg-surface-1 border border-border text-center">
          <HelpCircle className="w-12 h-12 text-primary mx-auto mb-4" />
          <h3 className="text-xl font-display font-bold text-text-primary mb-2">Still need help?</h3>
          <p className="text-text-secondary mb-6">Our support team is ready to assist you.</p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              href="/contact"
              className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-primary text-white font-semibold hover:bg-primary-dark transition-colors"
            >
              <Mail className="w-4 h-4" /> Contact Us
            </Link>
            <Link
              href="/chatbot"
              className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl border border-border text-text-primary font-semibold hover:bg-surface-0 transition-colors"
            >
              <MessageCircle className="w-4 h-4" /> Live Chat
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
