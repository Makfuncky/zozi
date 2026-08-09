"use client";

import { useRef, useState } from 'react';
import { Upload, Mic, PenLine, X, Camera, Sparkles, ChevronRight } from '@/lib/icons';

interface UploadModalProps {
  onImage: (file: File, previewUrl: string) => void;
  onVoice: () => void;
  onMagicEdit: () => void;
  onManualEntry: () => void;
  onClose: () => void;
}

/**
 * UploadModal — Step 1 in the 5-step upload flow.
 *
 * Single-entry point for uploading/capturing product images.
 * Supports:
 *  - Drag & drop
 *  - File picker (click or click-to-browse)
 *  - Camera capture (native `capture="environment"`)
 *  - Voice description
 *  - Magic photo editing
 */
export default function UploadModal({
  onImage,
  onVoice,
  onMagicEdit,
  onManualEntry,
  onClose,
}: UploadModalProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const MAX_IMAGE_SIZE = 5 * 1024 * 1024; // 5MB

  const handleFiles = (fileList: FileList) => {
    const file = fileList[0];
    if (!file) return;
    if (!['image/jpeg', 'image/png', 'image/webp', 'image/gif'].includes(file.type)) {
      return;
    }
    if (file.size > MAX_IMAGE_SIZE) return;

    const reader = new FileReader();
    reader.onload = (ev) => {
      const url = ev.target?.result as string;
      if (url) onImage(file, url);
    };
    reader.readAsDataURL(file);
  };

  const handleCameraCapture = async () => {
    try {
      await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
      // Permission granted — trigger native camera capture
      const inp = document.createElement('input');
      inp.type = 'file';
      inp.accept = 'image/*';
      inp.capture = 'environment' as any;
      inp.onchange = (e) => {
        if ((e.target as HTMLInputElement).files?.length) {
          handleFiles((e.target as HTMLInputElement).files!);
        }
      };
      inp.click();
    } catch {
      // Fallback: open file picker
      const inp = document.createElement('input');
      inp.type = 'file';
      inp.accept = 'image/*';
      inp.onchange = (e) => {
        if ((e.target as HTMLInputElement).files?.length) {
          handleFiles((e.target as HTMLInputElement).files!);
        }
      };
      inp.click();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center theme-overlay" onClick={onClose} role="dialog" aria-modal="true" aria-label="Add product media">
      <div className="glass-panel relative w-full max-w-md mx-4 overflow-hidden rounded-xl border shadow-2xl" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-border">
          <h2 className="text-lg font-semibold text-text">Add Product</h2>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-surface-2 text-text-muted hover:text-text transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Drop zone */}
        <div
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFiles(e.dataTransfer.files); }}
          onClick={() => fileInputRef.current?.click()}
          className={`mx-5 mt-4 p-8 border-2 border-dashed rounded-xl text-center transition-all cursor-pointer
            ${dragOver ? 'border-primary bg-primary/5 scale-[1.02]' : 'border-border hover:border-primary/50 hover:bg-surface-2'}`}
        >
          <Upload className="w-12 h-12 mx-auto mb-3 text-primary/60" />
          <p className="text-sm font-medium text-text">Drop photo here</p>
          <p className="text-xs text-text-faint mt-1">or click to browse (JPG, PNG, WebP)</p>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp,image/gif"
            className="hidden"
            onChange={(e) => e.target.files && handleFiles(e.target.files)}
          />
        </div>

        {/* OR divider */}
        <div className="flex items-center gap-3 mx-5 mt-4">
          <div className="flex-1 h-px bg-border" />
          <span className="text-xs font-medium text-text-faint">OR</span>
          <div className="flex-1 h-px bg-border" />
        </div>

        {/* Action buttons */}
        <div className="p-5 pt-3 grid grid-cols-3 gap-3">
          <button onClick={handleCameraCapture}
            className="flex flex-col items-center gap-2 p-4 rounded-xl theme-btn-secondary group transition-all hover:scale-[1.02]">
            <Camera className="w-7 h-7 text-primary group-hover:scale-110 transition-transform" />
            <span className="text-xs font-medium text-text-muted">Take Photo</span>
          </button>

          <button onClick={onVoice}
            className="flex flex-col items-center gap-2 p-4 rounded-xl theme-btn-secondary group transition-all hover:scale-[1.02]">
            <Mic className="w-7 h-7 text-primary group-hover:scale-110 transition-transform" />
            <span className="text-xs font-medium text-text-muted">Voice Note</span>
          </button>

          <button onClick={onMagicEdit}
            className="flex flex-col items-center gap-2 p-4 rounded-xl theme-btn-secondary group transition-all hover:scale-[1.02]">
            <Sparkles className="w-7 h-7 text-primary group-hover:scale-110 transition-transform" />
            <span className="text-xs font-medium text-text-muted">Magic Edit</span>
          </button>
        </div>

        {/* Manual entry link */}
        <div className="px-5 pb-5">
          <button onClick={onManualEntry}
            className="w-full flex items-center justify-center gap-1.5 py-2 text-xs text-text-muted hover:text-primary transition-colors border border-dashed border-border rounded-lg">
            <PenLine className="w-3.5 h-3.5" />
            Enter details manually
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Footer tip */}
        <div className="px-5 pb-5 -mt-2">
          <p className="text-[10px] text-text-faint text-center leading-relaxed">
            Upload a photo and AI will auto-fill product details.{' '}
            <strong>Voice</strong> describes variants,{' '}
            <strong>Magic Edit</strong> refines the image.
          </p>
        </div>
      </div>
    </div>
  );
}
