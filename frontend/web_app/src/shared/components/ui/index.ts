// Shared UI components index
// Components are imported directly with platform extensions (e.g., @shared/components/ui/Input)

export { default as Input } from "./Input";
export type { InputProps } from "./Input";

export { default as ErrorBoundary } from "./ErrorBoundary";
export type { ErrorBoundaryProps } from "./ErrorBoundary";

export { default as ErrorAlert } from "./ErrorAlert.web";
export type { ErrorAlertProps } from "./ErrorAlert.web";

export { GlassCard, GlassCardHeader, GlassCardContent, GlassCardFooter } from "./GlassCard.web";
export type { GlassCardProps } from "./GlassCard.web";

export { default as Button } from "./Button.web";
export type { ButtonProps, ButtonVariant, ButtonSize } from "./Button.web";