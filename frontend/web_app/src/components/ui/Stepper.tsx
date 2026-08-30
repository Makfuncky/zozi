"use client";
import { cn } from "@/lib/utils";

interface Step {
  label: string;
  description?: string;
}

interface StepperProps {
  steps: Step[];
  currentStep: number;
  className?: string;
}

export function Stepper({ steps, currentStep, className }: StepperProps) {
  return (
    <div className={cn("flex items-start w-full", className)}>
      {steps.map((step, i) => (
        <div key={i} className="flex-1 flex flex-col items-center relative">
          {i > 0 && (
            <div className={cn("absolute top-4 right-1/2 w-full h-0.5 -translate-y-1/2", i <= currentStep ? "bg-brand" : "bg-surface-2")} />
          )}
          <div className={cn("relative z-10 flex items-center justify-center w-8 h-8 rounded-full border-2 text-xs font-bold transition-colors", i < currentStep ? "bg-brand border-brand text-on-brand" : i === currentStep ? "border-brand text-brand bg-surface-0" : "border-surface-2 text-text-muted bg-surface-0")}>
            {i < currentStep ? "✓" : i + 1}
          </div>
          <div className="mt-2 text-center">
            <p className={cn("text-xs font-medium", i <= currentStep ? "text-text" : "text-text-muted")}>{step.label}</p>
            {step.description && <p className="text-xs text-text-faint mt-0.5">{step.description}</p>}
          </div>
        </div>
      ))}
    </div>
  );
}
