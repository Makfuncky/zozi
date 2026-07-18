"use client";

import { useRef, useState } from 'react';
import { Upload, Mic, PenLine, X, Camera, ImageIcon } from '@/lib/icons';

interface SmartMediaUploadProps {
  onImagesSelected: (files: File[]) => void;
  onVoiceStart: () => void;
  onManualEntry: () => void;
  onClose: () => void;
}

export default function SmartMediaUpload({
  onImagesSelected,
  onVoiceStart,
  onManualEntry,
  onClose,
}: SmartMediaUploadProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);

  const handleFiles = (fileList: FileList) => {
    const files = Array.from(fileList);
    if (files.length > 0) onImagesSelected(files);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center theme-overlay" onClick={onClose} role="dialog" aria-modal="true" aria-label="Add product media">
      <div className="glass-panel relative w-full max-w-lg mx-4 overflow-hidden rounded-xl border shadow-2xl" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-border">
          <h2 className="text-lg font-semibold text-text">Add Product Media</h2>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-surface-2 text-text-muted hover:text-text transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Drop zone */}
        <div
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFiles(e.dataTransfer.files); }}
          className={`mx-5 mt-4 p-8 border-2 border-dashed rounded-xl text-center transition-all cursor-pointer
            ${dragOver ? 'border-primary bg-primary/5 scale-[1.02]' : 'border-border hover:border-primary/50 hover:bg-surface-2'}`}
          onClick={() => fileInputRef.current?.click()}
        >
          <Upload className="w-12 h-12 mx-auto mb-3 text-primary/60" />
          <p className="text-sm font-medium text-text">Drop photos & videos here</p>
          <p className="text-xs text-text-faint mt-1">or click to browse (JPG, PNG, WebP, MP4)</p>
          <input ref={fileInputRef} type="file" accept="image/jpeg,image/png,image/webp,image/gif,video/mp4,video/webm"
            multiple className="hidden" onChange={(e) => e.target.files && handleFiles(e.target.files)} />
        </div>

        {/* Or divider */}
        <div className="flex items-center gap-3 mx-5 mt-4">
          <div className="flex-1 h-px bg-border" />
          <span className="text-xs font-medium text-text-faint">OR</span>
          <div className="flex-1 h-px bg-border" />
        </div>

        {/* Option buttons */}
        <div className="p-5 pt-3 grid grid-cols-3 gap-3">
          <button onClick={() => { navigator.mediaDevices?.getUserMedia({ video: true }).then(() => {
            const inp = document.createElement('input');
            inp.type = 'file'; inp.accept = 'image/*'; inp.capture = 'environment';
            inp.click();
          }).catch(() => {
            const inp = document.createElement('input');
            inp.type = 'file'; inp.accept = 'image/*';
            inp.onchange = (e) => e.target && handleFiles((e.target as HTMLInputElement).files!);
            inp.click();
          }); }}
            className="flex flex-col items-center gap-2 p-4 rounded-xl theme-btn-secondary">
            <Camera className="w-7 h-7 text-primary" />
            <span className="text-xs font-medium text-text-muted">Capture</span>
          </button>

          <button onClick={onVoiceStart}
            className="flex flex-col items-center gap-2 p-4 rounded-xl theme-btn-secondary">
            <Mic className="w-7 h-7 text-primary" />
            <span className="text-xs font-medium text-text-muted">Describe by Voice</span>
          </button>

          <button onClick={onManualEntry}
            className="flex flex-col items-center gap-2 p-4 rounded-xl theme-btn-secondary">
            <PenLine className="w-7 h-7 text-primary" />
            <span className="text-xs font-medium text-text-muted">Enter Manually</span>
          </button>
        </div>

        {/* Footer tip */}
        <div className="px-5 pb-5">
          <p className="text-xs text-text-faint text-center">
            Upload images first, then use <strong>Voice</strong> to auto-fill details
            or <strong>Manual</strong> to type them in.
          </p>
        </div>
      </div>
    </div>
  );
}
