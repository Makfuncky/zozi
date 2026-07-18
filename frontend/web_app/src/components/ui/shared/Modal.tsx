"use client";

import { cn } from "@/lib/utils";
import { forwardRef, useEffect } from "react";
import { X } from "@/lib/icons";

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  size?: "sm" | "md" | "lg" | "xl";
  showCloseButton?: boolean;
  className?: string;
  bodyClassName?: string;
  overlayClassName?: string;
}

export const Modal = forwardRef<HTMLDivElement, ModalProps>(
  ({ 
    isOpen, 
    onClose, 
    title,
    children, 
    size = "md", 
    showCloseButton = true,
    className,
    bodyClassName,
    overlayClassName,
  }, ref) => {
    // Close on Escape and lock background scroll while open.
    useEffect(() => {
      if (!isOpen) return;
      const onKey = (event: KeyboardEvent) => {
        if (event.key === "Escape") onClose();
      };
      window.addEventListener("keydown", onKey);
      const prevOverflow = document.body.style.overflow;
      document.body.style.overflow = "hidden";
      return () => {
        window.removeEventListener("keydown", onKey);
        document.body.style.overflow = prevOverflow;
      };
    }, [isOpen, onClose]);

    if (!isOpen) return null;

    const sizeClasses = {
      sm: "max-w-sm",
      md: "max-w-md",
      lg: "max-w-lg",
      xl: "max-w-2xl",
    };

    return (
      <div 
        className={cn(
          "fixed inset-0 z-50 flex items-center justify-center theme-overlay p-4",
          "animate-fade-in",
          overlayClassName
        )}
        onClick={onClose}
        role="dialog"
        aria-modal="true"
        aria-labelledby={title ? "modal-title" : undefined}
      >
        <div 
          ref={ref}
          className={cn(
            "glass-panel border rounded-xl shadow-2xl max-h-[80vh] overflow-y-auto",
            "animate-scale-in",
            sizeClasses[size],
            className
          )}
          onClick={(e) => e.stopPropagation()}
        >
          {(title || showCloseButton) && (
            <div className="flex items-center justify-between p-4 border-b border-glass-border-mid">
              {title && (
                <h3 id="modal-title" className="text-sm font-bold text-text">
                  {title}
                </h3>
              )}
              {showCloseButton && (
                <button 
                  onClick={onClose}
                  className="text-text-muted hover:text-text transition-colors rounded-lg p-1"
                  aria-label="Close modal"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>
          )}
          <div className={cn("p-5", bodyClassName)}>
            {children}
          </div>
        </div>
      </div>
    );
  }
);

Modal.displayName = "Modal";

/**
 * Modal footer component for action buttons
 */
export function ModalFooter({ 
  className, 
  children 
}: { 
  className?: string; 
  children: React.ReactNode 
}) {
  return (
    <div className={cn("flex items-center justify-end gap-2 border-t border-glass-border-mid p-4", className)}>
      {children}
    </div>
  );
}