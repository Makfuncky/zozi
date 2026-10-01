"use client";
import { createContext, useContext, type ReactNode } from "react";
import { cn } from "@/lib/utils";

interface FormGroupContextValue {
  error?: string;
  required?: boolean;
}

const FormGroupContext = createContext<FormGroupContextValue>({});

interface FormGroupProps {
  children: ReactNode;
  label?: string;
  error?: string;
  required?: boolean;
  hint?: string;
  className?: string;
}

export function FormGroup({ children, label, error, required, hint, className }: FormGroupProps) {
  return (
    <FormGroupContext.Provider value={{ error, required }}>
      <div className={cn("mb-4", className)}>
        {label && (
          <label className="block text-sm font-medium text-text mb-1.5">
            {label}
            {required && <span className="text-danger ml-0.5">*</span>}
          </label>
        )}
        {children}
        {error && <p className="mt-1.5 text-xs text-danger flex items-center gap-1">{error}</p>}
        {hint && !error && <p className="mt-1.5 text-xs text-text-faint">{hint}</p>}
      </div>
    </FormGroupContext.Provider>
  );
}

export function useFormGroup() {
  return useContext(FormGroupContext);
}
