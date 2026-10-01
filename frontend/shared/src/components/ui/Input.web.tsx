"use client";

import React, { forwardRef, useState } from "react";
import { AlertCircle, Eye, EyeOff } from "lucide-react";

function cn(...classes: Array<string | undefined | false | null>) {
  return classes.filter(Boolean).join(" ");
}

export interface InputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "size"> {
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: React.ReactNode;
  showPasswordToggle?: boolean;
  inputSize?: "sm" | "md" | "lg";
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      className,
      type = "text",
      label,
      error,
      helperText,
      leftIcon,
      showPasswordToggle,
      inputSize = "md",
      id,
      ...props
    },
    ref
  ) => {
    const [showPassword, setShowPassword] = useState(false);
    const [inputId] = useState(() => id || `input-${Math.random().toString(36).slice(2, 9)}`);
    const actualType = showPasswordToggle && showPassword ? "text" : type;

    const sizeClasses = {
      sm: "h-8 px-2.5 text-xs",
      md: "h-10 px-3 text-xs",
      lg: "h-11 px-4 text-sm",
    };

    return (
      <div className="relative">
        {label && (
          <label
            htmlFor={inputId}
            className="mb-1.5 block text-[11px] font-semibold uppercase tracking-wider text-text-muted"
          >
            {label}
          </label>
        )}

        <div className="relative">
          {leftIcon && (
            <div className="absolute left-3 top-1/2 z-10 -translate-y-1/2 text-text-muted">
              {leftIcon}
            </div>
          )}

          <input
            id={inputId}
            ref={ref}
            type={actualType}
            className={cn(
              "flex w-full rounded-xl border bg-surface-1 text-text border-border transition-all placeholder:text-text-faint focus:border-primary/50 focus:outline-none focus:ring-2 focus:ring-primary/40 disabled:cursor-not-allowed disabled:opacity-50",
              sizeClasses[inputSize],
              leftIcon ? "pl-11" : undefined,
              showPasswordToggle ? "pr-10" : undefined,
              error ? "border-danger/50 focus:border-danger focus:ring-danger/30" : undefined,
              className
            )}
            {...props}
          />

          {showPasswordToggle && (
            <button
              type="button"
              onClick={() => setShowPassword((prev) => !prev)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted transition-colors hover:text-text"
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          )}
        </div>

        {(error || helperText) && (
          <div className="mt-1.5 flex items-center gap-2 text-xs">
            {error && <AlertCircle className="h-3.5 w-3.5 shrink-0 text-danger" />}
            <span className={error ? "text-danger" : "text-text-muted"}>
              {error || helperText}
            </span>
          </div>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";
export default Input;