import type { ReactNode } from "react";

export function DraftStepSection({
  step,
  title,
  description,
  children,
}: {
  step: number;
  title: string;
  description: string;
  children: ReactNode;
}) {
  return (
    <section className="rounded-xl border border-border bg-surface-1" data-step={step}>
      <div className="border-b border-border px-4 py-3">
        <div className="flex items-center gap-3">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/10 text-xs font-bold text-primary">
            {step}
          </span>
          <div>
            <p className="text-xs font-semibold text-text">{title}</p>
            <p className="text-[11px] text-text-muted">{description}</p>
          </div>
        </div>
      </div>
      <div className="px-4 py-4">{children}</div>
    </section>
  );
}


