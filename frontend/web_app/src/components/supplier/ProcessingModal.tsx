"use client";

import { X, Loader2, ImageIcon, Zap, RefreshCw } from '@/lib/icons';

interface ProcessingModalProps {
  bgProgress: number;
  aiProgress: number;
  bgModel: string | null;
  error: string | null;
  onRetry?: () => void;
  onClose?: () => void;
}

export default function ProcessingModal({
  bgProgress,
  aiProgress,
  bgModel,
  error,
  onRetry,
  onClose,
}: ProcessingModalProps) {
  const overall = Math.round((bgProgress + aiProgress) / 2);
  const isComplete = bgProgress >= 100 && aiProgress >= 100;
  const isFailed = !!error;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center theme-overlay" role="dialog" aria-modal="true" aria-label="Processing your product">
      <div className="glass-panel relative w-full max-w-md mx-4 rounded-xl border shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-border">
          <h2 className="text-lg font-semibold text-text flex items-center gap-2">
            {isComplete ? (
              <span className="w-6 h-6 rounded-full bg-success/10 flex items-center justify-center">
                <span className="text-success text-xs">✓</span>
              </span>
            ) : isFailed ? (
              <span className="text-danger">Processing Failed</span>
            ) : (
              <>
                <Loader2 className="w-5 h-5 text-primary animate-spin" />
                Processing Product
              </>
            )}
          </h2>
          {onClose && (
            <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-surface-2 text-text-muted transition-colors">
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        <div className="p-6 space-y-5">
          {/* Overall progress */}
          <div className="text-center">
            <div className="relative w-24 h-24 mx-auto mb-3">
              <svg className="w-24 h-24 -rotate-90" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="42" fill="none" stroke="currentColor"
                  className="text-surface-3" strokeWidth="6" />
                <circle cx="50" cy="50" r="42" fill="none"
                  stroke={isFailed ? '#ef4444' : '#2563eb'}
                  strokeWidth="6" strokeLinecap="round"
                  strokeDasharray={`${2 * Math.PI * 42}`}
                  strokeDashoffset={`${2 * Math.PI * 42 * (1 - overall / 100)}`}
                  className="transition-all duration-500" />
              </svg>
              <span className="absolute inset-0 flex items-center justify-center text-lg font-bold text-text">
                {isFailed ? '!' : `${overall}%`}
              </span>
            </div>
            <p className="text-sm text-text-muted">
              {isComplete
                ? 'Processing complete!'
                : isFailed
                  ? error
                  : 'AI is analyzing your product...'}
            </p>
          </div>

          {/* BG Removal progress */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <div className="flex items-center gap-1.5 text-xs font-medium text-text-muted">
                <ImageIcon className="w-3.5 h-3.5" />
                Background Removal
                {bgModel && <span className="px-1.5 py-0.5 bg-primary/5 text-primary text-[10px] rounded">{bgModel}</span>}
              </div>
              <span className="text-xs font-mono text-text-faint">{bgProgress}%</span>
            </div>
            <div className="h-2 bg-surface-3 rounded-full overflow-hidden">
              <div
                className="h-full bg-primary rounded-full transition-all duration-300"
                style={{ width: `${bgProgress}%` }}
              />
            </div>
          </div>

          {/* AI Analysis progress */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <div className="flex items-center gap-1.5 text-xs font-medium text-text-muted">
                <Zap className="w-3.5 h-3.5" />
                AI Product Analysis
              </div>
              <span className="text-xs font-mono text-text-faint">{aiProgress}%</span>
            </div>
            <div className="h-2 bg-surface-3 rounded-full overflow-hidden">
              <div
                className="h-full bg-accent rounded-full transition-all duration-300"
                style={{ width: `${aiProgress}%` }}
              />
            </div>
          </div>

          {/* Status messages */}
          <div className="space-y-1">
            {bgProgress < 100 && (
              <p className="text-xs text-text-faint flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
                Removing background from image...
              </p>
            )}
            {aiProgress < 100 && (
              <p className="text-xs text-text-faint flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
                Detecting product details...
              </p>
            )}
            {isComplete && (
              <p className="text-xs text-success flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-success" />
                Analysis complete! Reviewing results...
              </p>
            )}
          </div>

          {/* Error state */}
          {isFailed && onRetry && (
            <button onClick={onRetry}
              className="w-full theme-btn-primary py-2.5 text-sm font-medium flex items-center justify-center gap-2">
              <RefreshCw className="w-4 h-4" /> Retry Processing
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
