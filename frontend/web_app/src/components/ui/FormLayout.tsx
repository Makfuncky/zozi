"use client";

import { cn } from "@/lib/utils";

interface FormLayoutProps {
  className?: string;
  children: React.ReactNode;
}

interface FormGroupProps {
  className?: string;
  label: string;
  name?: string;
  children: React.ReactNode;
  required?: boolean;
  error?: string;
}

interface FormRowProps {
  className?: string;
  children: React.ReactNode;
  cols?: 1 | 2 | 3;
}

export function FormLayout({ className, children }: FormLayoutProps) {
  return (
    <div className={cn("space-y-6", className)}>
      {children}
    </div>
  );
}

export function FormSection({ className, title, children }: { className?: string; title?: string; children: React.ReactNode }) {
  return (
    <section className={cn("space-y-4", className)}>
      {title && (
        <h3 id={`form-section-${title.toLowerCase().replace(/\s+/g, "-")}`} className="text-lg font-semibold text-text border-b border-border pb-2">
          {title}
        </h3>
      )}
      {children}
    </section>
  );
}

export function FormGroup({ className, label, name, children, required, error }: FormGroupProps) {
  const errorId = name ? `${name}-error` : undefined;
  
  return (
    <div className={cn("space-y-2", className)}>
      <label 
        htmlFor={name} 
        className="block text-sm font-medium text-text-muted"
      >
        {label}
        {required && <span className="text-danger ml-1" aria-hidden="true">*</span>}
      </label>
      {children}
      {error && (
        <span id={errorId} className="text-sm text-danger" role="alert" aria-live="polite">
          {error}
        </span>
      )}
    </div>
  );
}

export function FormRow({ className, children, cols = 2 }: FormRowProps) {
  const gridCols = {
    1: "grid-cols-1",
    2: "grid-cols-1 md:grid-cols-2",
    3: "grid-cols-1 md:grid-cols-2 lg:grid-cols-3",
  };

  return (
    <div className={cn("grid gap-4", gridCols[cols], className)}>
      {children}
    </div>
  );
}

interface FormInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: string;
}

export function FormInput({ 
  className, 
  error,
  id,
  ...props 
}: FormInputProps) {
  return (
    <input
      id={id}
      aria-invalid={error ? "true" : undefined}
      aria-describedby={error ? `${id}-error` : undefined}
      className={cn(
        "w-full px-3 py-2 bg-surface-2 border border-border rounded-lg",
        "text-text placeholder:text-text-faint",
        "focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent",
        error && "border-danger",
        className
      )}
      {...props}
    />
  );
}

interface FormSelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  error?: string;
}

export function FormSelect({ 
  className, 
  error,
  id,
  ...props 
}: FormSelectProps) {
  return (
    <select
      id={id}
      aria-invalid={error ? "true" : undefined}
      aria-describedby={error ? `${id}-error` : undefined}
      className={cn(
        "w-full px-3 py-2 bg-surface-2 border border-border rounded-lg",
        "text-text placeholder:text-text-faint",
        "focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent",
        error && "border-danger",
        className
      )}
      {...props}
    />
  );
}

interface FormTextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: string;
}

export function FormTextarea({ 
  className, 
  error,
  id,
  ...props 
}: FormTextareaProps) {
  return (
    <textarea
      id={id}
      aria-invalid={error ? "true" : undefined}
      aria-describedby={error ? `${id}-error` : undefined}
      className={cn(
        "w-full px-3 py-2 bg-surface-2 border border-border rounded-lg",
        "text-text placeholder:text-text-faint resize-y",
        "focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent",
        error && "border-danger",
        className
      )}
      {...props}
    />
  );
}


