"use client";

/**
 * PhotoUploader — Drag-and-drop image upload component for banner management.
 *
 * Features:
 * - Drag-and-drop file upload
 * - Image preview with remove option
 * - Upload progress indicator
 * - Automatic URL return via onUpload callback
 * - Support for paste from clipboard
 * - Mobile-friendly touch interface
 */
import { useCallback, useRef, useState } from "react";
import { Upload, X, ImageIcon, Loader2, CheckCircle } from "@/lib/icons";
import { apiFetch } from "@/lib/api";
import { useToastStore } from "@/stores/toastStore";

interface PhotoUploaderProps {
  /** Current image URL (if any) */
  value?: string | null;
  /** Callback when upload completes with the new URL */
  onUpload: (url: string) => void;
  /** Callback when image is removed */
  onRemove?: () => void;
  /** Storage folder (default: "banners") */
  folder?: string;
  /** Placeholder text */
  placeholder?: string;
  /** Additional CSS classes */
  className?: string;
  /** Preview height in pixels */
  previewHeight?: number;
  /** Whether the uploader is disabled */
  disabled?: boolean;
}

export default function PhotoUploader({
  value,
  onUpload,
  onRemove,
  folder = "banners",
  placeholder = "Drop an image here or click to upload",
  className = "",
  previewHeight = 200,
  disabled = false,
}: PhotoUploaderProps) {
  const { addToast } = useToastStore();
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [preview, setPreview] = useState<string | null>(value || null);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dragCounterRef = useRef(0);

  const handleFile = useCallback(
    async (file: File) => {
      // Validate file type
      if (!file.type.startsWith("image/")) {
        addToast("Please upload an image file", "error");
        return;
      }

      // Validate file size (10MB max)
      const maxSize = 10 * 1024 * 1024;
      if (file.size > maxSize) {
        addToast("File too large (max 10MB)", "error");
        return;
      }

      // Show local preview immediately
      const reader = new FileReader();
      reader.onload = (e) => {
        setPreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);

      // Upload to server
      setIsUploading(true);
      setUploadSuccess(false);

      try {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("folder", folder);

        const res = await apiFetch("/admin/media/upload", {
          method: "POST",
          body: formData,
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || "Upload failed");
        }

        const data = await res.json();
        setPreview(data.url);
        setUploadSuccess(true);
        onUpload(data.url);
        addToast("Image uploaded successfully", "success");

        // Clear success indicator after 3 seconds
        setTimeout(() => setUploadSuccess(false), 3000);
      } catch (err) {
        // Reset preview on failure
        setPreview(value || null);
        addToast(
          err instanceof Error ? err.message : "Failed to upload image",
          "error"
        );
      } finally {
        setIsUploading(false);
      }
    },
    [folder, onUpload, addToast, value]
  );

  // Drag and drop handlers
  const handleDragEnter = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      dragCounterRef.current++;
      if (!disabled) setIsDragging(true);
    },
    [disabled]
  );

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounterRef.current--;
    if (dragCounterRef.current === 0) {
      setIsDragging(false);
    }
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);
      dragCounterRef.current = 0;

      if (disabled || isUploading) return;

      const files = e.dataTransfer.files;
      if (files.length > 0) {
        handleFile(files[0]);
      }
    },
    [disabled, isUploading, handleFile]
  );

  // Click to upload
  const handleClick = useCallback(() => {
    if (!disabled && !isUploading) {
      fileInputRef.current?.click();
    }
  }, [disabled, isUploading]);

  // File input change
  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (files && files.length > 0) {
        handleFile(files[0]);
      }
      // Reset input so same file can be uploaded again
      e.target.value = "";
    },
    [handleFile]
  );

  // Paste from clipboard
  const handlePaste = useCallback(
    (e: React.ClipboardEvent) => {
      if (disabled || isUploading) return;
      const items = e.clipboardData.items;
      for (const item of items) {
        if (item.type.startsWith("image/")) {
          const file = item.getAsFile();
          if (file) {
            handleFile(file);
            break;
          }
        }
      }
    },
    [disabled, isUploading, handleFile]
  );

  // Remove image
  const handleRemove = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      setPreview(null);
      setUploadSuccess(false);
      onRemove?.();
    },
    [onRemove]
  );

  return (
    <div className={`photo-upload-container ${className}`}>
      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handleFileChange}
        disabled={disabled || isUploading}
      />

      {/* Drop zone */}
      <div
        onClick={handleClick}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onPaste={handlePaste}
        tabIndex={0}
        className={`
          relative cursor-pointer overflow-hidden rounded-xl border-2 border-dashed
          transition-all duration-200
          ${isDragging ? "border-primary bg-primary/5 scale-[1.02]" : "border-border hover:border-primary/50"}
          ${disabled ? "opacity-50 cursor-not-allowed" : ""}
          ${isUploading ? "pointer-events-none" : ""}
        `}
        style={{ minHeight: preview ? previewHeight : 160 }}
      >
        {preview ? (
          /* Image preview */
          <div className="relative h-full w-full">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={preview}
              alt="Uploaded preview"
              className="h-full w-full object-cover"
              style={{ maxHeight: previewHeight }}
            />

            {/* Overlay with actions */}
            <div className="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 transition-opacity hover:opacity-100">
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleClick}
                  className="rounded-lg bg-white/90 px-3 py-1.5 text-sm font-medium text-text hover:bg-white"
                >
                  Change
                </button>
                <button
                  type="button"
                  onClick={handleRemove}
                  className="rounded-lg bg-danger/90 px-3 py-1.5 text-sm font-medium text-white hover:bg-danger"
                >
                  Remove
                </button>
              </div>
            </div>

            {/* Upload status indicators */}
            {isUploading && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/50">
                <Loader2 className="h-8 w-8 animate-spin text-white" />
              </div>
            )}
            {uploadSuccess && !isUploading && (
              <div className="absolute right-2 top-2 rounded-full bg-success p-1">
                <CheckCircle className="h-4 w-4 text-white" />
              </div>
            )}
          </div>
        ) : (
          /* Upload prompt */
          <div className="flex flex-col items-center justify-center px-4 py-8 text-center">
            {isUploading ? (
              <>
                <Loader2 className="mb-3 h-10 w-10 animate-spin text-primary" />
                <p className="text-sm font-medium text-text">Uploading...</p>
                <p className="mt-1 text-xs text-text-muted">Please wait</p>
              </>
            ) : (
              <>
                <div className="mb-3 rounded-full bg-primary/10 p-4">
                  {isDragging ? (
                    <Upload className="h-8 w-8 text-primary" />
                  ) : (
                    <ImageIcon className="h-8 w-8 text-primary" />
                  )}
                </div>
                <p className="text-sm font-medium text-text">
                  {isDragging ? "Drop image here" : placeholder}
                </p>
                <p className="mt-1 text-xs text-text-muted">
                  PNG, JPG, GIF, WebP up to 10MB
                </p>
                <p className="mt-2 text-xs text-text-muted">
                  or paste from clipboard
                </p>
              </>
            )}
          </div>
        )}
      </div>

      {/* URL display (for easy copying) */}
      {preview && !isUploading && (
        <div className="mt-2 flex items-center gap-2">
          <input
            type="text"
            readOnly
            value={preview}
            className="flex-1 rounded-lg border border-border bg-surface px-3 py-1.5 text-xs text-text-muted"
            onClick={(e) => (e.target as HTMLInputElement).select()}
          />
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              navigator.clipboard.writeText(preview);
              addToast("URL copied to clipboard", "success");
            }}
            className="rounded-lg border border-border bg-surface px-2 py-1.5 text-xs text-text-muted hover:bg-surface-hover"
          >
            Copy
          </button>
        </div>
      )}
    </div>
  );
}
