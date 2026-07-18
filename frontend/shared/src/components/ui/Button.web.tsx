"use client";

import React from "react";

export type ButtonVariant = "default" | "primary" | "secondary" | "ghost" | "danger";
export type ButtonSize = "xs" | "sm" | "md" | "lg" | "xl";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  icon?: React.ReactNode;
  iconRight?: React.ReactNode;
}

const variantStyles: Record<ButtonVariant, string> = {
  default:
    "theme-btn-primary",
  primary:
    "theme-btn-primary",
  secondary:
    "theme-btn-secondary border",
  ghost: "text-text-muted hover:bg-surface-1 hover:text-text",
  danger:
    "bg-danger text-on-brand border border-danger/20 hover:bg-danger/80",
};

const spinnerStyles: Record<ButtonVariant, string> = {
  default: "border-white/30 border-t-white",
  primary: "border-white/30 border-t-white",
  secondary: "border-text/30 border-t-text",
  ghost: "border-text/20 border-t-text",
  danger: "border-white/30 border-t-white",
};

const sizeStyles: Record<ButtonSize, string> = {
  xs: "h-7 px-2.5 text-[11px] rounded-lg",
  sm: "h-8 px-3 text-xs rounded-xl",
  md: "h-10 px-5 text-xs rounded-xl",
  lg: "h-11 px-6 text-sm rounded-xl",
  xl: "h-12 px-8 text-sm rounded-xl",
};

function mergeClasses(...classes: Array<string | undefined | null | false>) {
  return classes.filter(Boolean).join(" ");
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = "default",
      size = "md",
      loading = false,
      icon,
      iconRight,
      children,
      disabled,
      className,
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || loading;

    return (
      <button
        ref={ref}
        disabled={isDisabled}
        className={mergeClasses(
          "relative inline-flex items-center justify-center overflow-hidden whitespace-nowrap select-none font-semibold tracking-tight transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-surface-base disabled:pointer-events-none disabled:opacity-40",
          variantStyles[variant],
          sizeStyles[size],
          className
        )}
        {...props}
      >
        {loading ? (
          <span className={mergeClasses("mr-1.5 h-3.5 w-3.5 animate-spin rounded-full border-2", spinnerStyles[variant])} />
        ) : (
          <>
            {icon && <span className="mr-1.5 shrink-0">{icon}</span>}
            {children}
            {iconRight && <span className="ml-1.5 shrink-0">{iconRight}</span>}
          </>
        )}
      </button>
    );
  }
);

Button.displayName = "Button";

export default Button;
