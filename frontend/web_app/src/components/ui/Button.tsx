"use client";

import { cn } from "@/lib/utils";
import { forwardRef } from "react";

export type ButtonVariant =
  | "primary"
  | "secondary"
  | "ghost"
  | "danger"
  | "danger-outline"
  | "accent"
  | "admin"
  | "warning"
  | "info";
export type ButtonSize = "sm" | "md" | "lg";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  isLoading?: boolean;
  icon?: React.ReactNode;
  iconRight?: React.ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", leftIcon, rightIcon, isLoading, icon, iconRight, children, disabled, ...props }, ref) => {
    const baseClasses = "inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-primary disabled:opacity-50 disabled:cursor-not-allowed";
    
    const variantClasses: Record<ButtonVariant, string> = {
      primary: "theme-btn-primary",
      secondary: "theme-btn-secondary text-text hover:!bg-surface-3",
      ghost: "text-text-muted hover:text-text hover:bg-surface-2",
      danger: "theme-btn-danger",
      "danger-outline": "theme-btn-danger-outline",
      accent: "theme-btn-accent",
      admin: "theme-btn-admin",
      warning: "bg-warning text-on-warning hover:bg-warning/90 shadow-lg shadow-warning/25",
      info: "bg-info text-white hover:bg-info/90 shadow-lg shadow-info/25",
    };

    const sizeClasses = {
      sm: "h-8 px-3 text-sm",
      md: "h-10 px-4",
      lg: "h-12 px-6 text-lg",
    };

    // Support both old (icon/iconRight) and new (leftIcon/rightIcon) prop names
    const finalLeftIcon = leftIcon || icon;
    const finalRightIcon = rightIcon || iconRight;

    return (
      <button
        ref={ref}
        className={cn(
          baseClasses,
          variantClasses[variant],
          sizeClasses[size],
          "icon-gap", // RTL: reverse icon order
          isLoading && "opacity-50 cursor-wait",
          className
        )}
        disabled={disabled || isLoading}
        aria-busy={isLoading || undefined}
        {...props}
      >
        {isLoading ? (
          <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" aria-hidden="true" />
        ) : (
          <>
            {finalRightIcon}
            {children}
            {finalLeftIcon}
          </>
        )}
      </button>
    );
  }
);

Button.displayName = "Button";