"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Share2, Copy, Check, Mail, MessageCircle } from "lucide-react";

interface WishlistShareProps {
  wishlistId?: string;
  wishlistName?: string;
}

export default function WishlistShare({ wishlistName = "My Wishlist" }: WishlistShareProps) {
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  const shareUrl = typeof window !== "undefined" ? window.location.href : "";
  const encodedUrl = encodeURIComponent(shareUrl);
  const encodedText = encodeURIComponent(`Check out my wishlist: ${wishlistName}`);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback for older browsers
      const input = document.createElement("input");
      input.value = shareUrl;
      document.body.appendChild(input);
      input.select();
      document.execCommand("copy");
      document.body.removeChild(input);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-4 py-2 rounded-lg border border-border text-text-secondary hover:border-primary/30 hover:text-primary transition-colors"
      >
        <Share2 className="w-4 h-4" />
        Share Wishlist
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -10 }}
            className="absolute right-0 top-full mt-2 w-64 p-4 rounded-xl bg-surface-1 border border-border shadow-xl z-50"
          >
            <h4 className="font-medium text-text-primary mb-3">Share Wishlist</h4>

            <div className="space-y-2">
              <button
                onClick={handleCopy}
                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-surface-2 transition-colors text-left"
              >
                {copied ? (
                  <Check className="w-4 h-4 text-success" />
                ) : (
                  <Copy className="w-4 h-4 text-text-faint" />
                )}
                <span className="text-sm text-text-secondary">
                  {copied ? "Copied!" : "Copy link"}
                </span>
              </button>

              <a
                href={`mailto:?subject=${encodedText}&body=${encodedUrl}`}
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-surface-2 transition-colors"
              >
                <Mail className="w-4 h-4 text-text-faint" />
                <span className="text-sm text-text-secondary">Share via email</span>
              </a>

              <a
                href={`https://wa.me/?text=${encodedText}%20${encodedUrl}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-surface-2 transition-colors"
              >
                <MessageCircle className="w-4 h-4 text-text-faint" />
                <span className="text-sm text-text-secondary">Share on WhatsApp</span>
              </a>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
