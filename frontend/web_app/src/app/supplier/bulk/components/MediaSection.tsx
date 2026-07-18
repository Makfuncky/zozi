import { type RefObject, useState } from "react";
import { FileJson, ImageIcon, Link2, X } from "@/lib/icons";
import { resolveImage } from "@/lib/utils";
import { getDraftFieldId } from "../validation";
import { isEmbeddableVideoUrl, isVideoAsset, revokeObjectUrl } from "../draftUtils";
import type { ProductDraft } from "../types";
import { Button } from "@/components/ui/Button";

interface MediaSectionProps {
  draft: ProductDraft;
  imgRef: RefObject<HTMLInputElement | null>;
  videoRef: RefObject<HTMLInputElement | null>;
  galleryFilePreviews: string[];
  galleryMediaCounts: { images: number; videos: number };
  onUpdate: (patch: Partial<ProductDraft>) => void;
  onImageChange: (files: FileList | File[]) => void;
  onSetExtraUrl: (index: number, value: string) => void;
  onSetExtraFile: (index: number, file: File | null) => void;
  onAddExtraSlot: () => void;
  onRemoveExtraSlot: (index: number) => void;
  onSetVideoFile: (file: File | null) => void;
}

export function MediaSection({
  draft,
  imgRef,
  videoRef,
  galleryFilePreviews,
  galleryMediaCounts,
  onUpdate,
  onImageChange,
  onSetExtraUrl,
  onSetExtraFile,
  onAddExtraSlot,
  onRemoveExtraSlot,
  onSetVideoFile,
}: MediaSectionProps) {
  const mediaCount = draft.extraImageUrls.filter(Boolean).length + (draft.additionalImageFiles ?? []).filter(Boolean).length;
  const videoPreview = draft.videoPreview || draft.videoUrl;
  const [showUrlTools, setShowUrlTools] = useState(Boolean(draft.imageUrl || draft.videoUrl || draft.extraImageUrls.some(Boolean) || draft.imageMode === "url" || draft.videoMode === "url"));

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border bg-surface-2/40 px-3 py-2">
        <div>
          <span className="text-[11px] font-semibold uppercase tracking-wider text-text-muted">Photos and video</span>
          <p className="mt-1 text-[10px] text-text-faint">Upload files directly. The first photo becomes the cover automatically.</p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => setShowUrlTools((current) => !current)}
            className="rounded-lg bg-surface-base px-3 py-1 text-xs font-semibold text-text-muted transition-colors hover:text-text"
          >
            {showUrlTools ? "Hide URL tools" : "Use external media URLs"}
          </button>
          {showUrlTools ? (
            <>
              <button
                type="button"
                onClick={() => onUpdate({ imageMode: draft.imageMode === "url" ? "upload" : "url" })}
                className={`flex items-center gap-1 rounded-lg px-3 py-1 text-xs font-semibold transition-colors ${draft.imageMode === "url" ? "bg-primary text-on-brand" : "bg-surface-base text-text-muted hover:text-text"}`}
              >
                <Link2 className="h-3 w-3" /> Main image URL
              </button>
              <button
                type="button"
                onClick={() => onUpdate({ videoMode: draft.videoMode === "url" ? "upload" : "url" })}
                className={`rounded-lg px-3 py-1 text-xs font-semibold transition-colors ${draft.videoMode === "url" ? "bg-primary text-on-brand" : "bg-surface-base text-text-muted hover:text-text"}`}
              >
                Video URL
              </button>
            </>
          ) : null}
        </div>
      </div>

      <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_minmax(18rem,24rem)]">
        <div className="grid gap-3 md:grid-cols-[13rem_minmax(0,1fr)]">
          {draft.imageMode === "upload" ? (
            <div
              className="relative flex aspect-square cursor-pointer items-center justify-center overflow-hidden rounded-xl border-2 border-dashed border-border bg-surface-2 transition-colors hover:border-primary/50"
              onClick={() => imgRef.current?.click()}
            >
              {draft.imagePreview ? (
                <>
                  <img src={draft.imagePreview} alt="preview" className="block h-full w-full object-cover" />
                  <button
                    type="button"
                    onClick={(event) => {
                      event.stopPropagation();
                      revokeObjectUrl(draft.imagePreview);
                      onUpdate({ imageFile: null, imagePreview: null });
                    }}
                    className="absolute right-2 top-2 rounded-lg bg-black/60 p-1 text-white hover:bg-black/80"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </>
              ) : (
                <div className="pointer-events-none px-3 text-center text-text-muted">
                  <ImageIcon className="mx-auto mb-2 h-8 w-8 opacity-50" />
                  <p className="text-xs font-medium">Upload photos</p>
                  <p className="mt-1 text-[10px]">First photo becomes the cover image.</p>
                </div>
              )}
              <input
                id={getDraftFieldId(draft.id, "image-trigger")}
                ref={imgRef}
                type="file"
                accept="image/*"
                multiple
                className="hidden"
                onChange={(event) => {
                  if (event.target.files?.length) onImageChange(event.target.files);
                  event.currentTarget.value = "";
                }}
              />
            </div>
          ) : (
            <div>
              <label htmlFor={getDraftFieldId(draft.id, "image-url")} className="mb-1 block text-[11px] font-semibold uppercase tracking-wider text-text-muted">
                Main Image URL
              </label>
              <input
                id={getDraftFieldId(draft.id, "image-url")}
                type="url"
                value={draft.imageUrl}
                onChange={(event) => onUpdate({ imageUrl: event.target.value })}
                placeholder="https://example.com/product.jpg"
                className="theme-input h-9 w-full rounded-xl border px-3 text-xs placeholder:text-text-faint focus:border-primary focus:outline-none transition-colors"
              />
              {draft.imageUrl && (
                <img
                  src={resolveImage(draft.imageUrl)}
                  alt="URL preview"
                  onError={(event) => { (event.target as HTMLImageElement).style.display = "none"; }}
                  className="mt-2 aspect-square w-full rounded-xl border border-border object-cover"
                />
              )}
            </div>
          )}

          <div className="space-y-2">
            <div className="flex items-center justify-between gap-3">
              <label className="text-[11px] font-semibold uppercase tracking-wider text-text-muted">
                Gallery ({mediaCount} / 19)
              </label>
              <span className="text-[10px] text-text-faint">{galleryMediaCounts.images} photos, {galleryMediaCounts.videos} videos</span>
            </div>

            <div className="grid grid-cols-4 gap-2 sm:grid-cols-5">
              {draft.extraImageUrls.map((url, index) => {
                const file = (draft.additionalImageFiles ?? [])[index] ?? null;
                const preview = file ? (galleryFilePreviews[index] || null) : (url ? (url.startsWith("http") ? url : resolveImage(url)) : null);
                const isVideo = file ? file.type.startsWith("video/") : isVideoAsset(preview);
                return (
                  <div key={index} className="group relative aspect-square overflow-hidden rounded-xl border border-border bg-surface-2">
                    {preview ? (
                      <>
                        {isVideo ? (
                          <div className="flex h-full w-full flex-col items-center justify-center gap-1 text-text-muted">
                            <FileJson className="h-5 w-5" />
                            <span className="text-[9px] font-semibold">Video {index + 1}</span>
                          </div>
                        ) : (
                          <img src={preview} alt={`Extra ${index + 1}`} className="h-full w-full object-cover" />
                        )}
                        <Button variant="danger" className="absolute right-1 top-1 rounded-full p-0.5 opacity-0 transition-opacity group-hover:opacity-100" type="button"
                          onClick={() => onRemoveExtraSlot(index)}
                        >
                          <X className="h-3 w-3" />
                        </Button>
                      </>
                    ) : (
                      <label className="flex h-full w-full cursor-pointer flex-col items-center justify-center text-text-faint transition-colors hover:text-primary">
                        <ImageIcon className="mb-0.5 h-5 w-5" />
                        <span className="text-[9px]">Upload</span>
                        <input
                          type="file"
                          accept="image/*,video/*"
                          className="hidden"
                          onChange={(event) => {
                            const fileValue = event.target.files?.[0] ?? null;
                            if (fileValue) onSetExtraFile(index, fileValue);
                            event.currentTarget.value = "";
                          }}
                        />
                      </label>
                    )}
                    <span className="absolute bottom-0.5 left-0.5 rounded bg-black/50 px-1 text-[7px] font-bold text-white">{index + 1}</span>
                  </div>
                );
              })}
              {draft.extraImageUrls.length < 19 && (
                <Button variant="secondary" id={getDraftFieldId(draft.id, "gallery-add")}
                  type="button"
                  onClick={onAddExtraSlot}>
                  <span className="sr-only">Add gallery slot</span>
                  <ImageIcon className="mx-auto h-5 w-5" />
                </Button>
              )}
            </div>

            {showUrlTools && draft.extraImageUrls.length > 0 && (
              <div className="space-y-1">
                {draft.extraImageUrls.map((url, index) => {
                  const file = (draft.additionalImageFiles ?? [])[index];
                  if (file) return null;
                  return (
                    <div key={index} className="flex items-center gap-1.5">
                      <span className="w-4 shrink-0 text-right text-[10px] text-text-faint">{index + 1}.</span>
                      <input
                        id={getDraftFieldId(draft.id, `gallery-url-${index}`)}
                        type="url"
                        value={url}
                        onChange={(event) => onSetExtraUrl(index, event.target.value)}
                        placeholder={`Image or video URL ${index + 1}`}
                        className="theme-input h-7 flex-1 rounded-lg border px-2.5 text-[11px] placeholder:text-text-faint focus:border-primary focus:outline-none transition-colors"
                      />
                      <button type="button" onClick={() => onRemoveExtraSlot(index)} className="rounded p-1 text-danger/50 transition-colors hover:text-danger">
                        <X className="h-3 w-3" />
                      </button>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        <div className="rounded-xl border border-border bg-surface-2/40 p-3">
          <div>
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-wider text-text-muted">Product Video</p>
              <p className="mt-1 text-[10px] text-text-faint">Optional MP4, WebM, YouTube, or Vimeo.</p>
            </div>
          </div>

          <div className="mt-3 space-y-2">
            {draft.videoMode === "upload" ? (
              <>
                <button
                  id={getDraftFieldId(draft.id, "video-trigger")}
                  type="button"
                  onClick={() => videoRef.current?.click()}
                  className="theme-btn-secondary w-full rounded-xl px-3 py-2 text-xs font-semibold"
                >
                  {draft.videoFile ? "Replace video" : "Upload video"}
                </button>
                <input
                  ref={videoRef}
                  type="file"
                  accept="video/mp4,video/webm"
                  className="hidden"
                  onChange={(event) => {
                    const file = event.target.files?.[0] ?? null;
                    onSetVideoFile(file);
                    event.currentTarget.value = "";
                  }}
                />
              </>
            ) : (
              <input
                id={getDraftFieldId(draft.id, "video-url")}
                type="url"
                value={draft.videoUrl}
                onChange={(event) => onUpdate({ videoUrl: event.target.value, videoPreview: event.target.value })}
                placeholder="https://www.youtube.com/watch?v=..."
                className="theme-input h-9 w-full rounded-xl border px-3 text-xs placeholder:text-text-faint focus:border-primary focus:outline-none transition-colors"
              />
            )}

            {videoPreview ? (
              <div className="overflow-hidden rounded-xl border border-border bg-surface-base">
                {videoPreview.startsWith("blob:") || isVideoAsset(videoPreview) || videoPreview.startsWith("/uploads/") || videoPreview.startsWith("uploads/") ? (
                  <video controls className="aspect-video w-full bg-black">
                    <source src={videoPreview} />
                  </video>
                ) : isEmbeddableVideoUrl(videoPreview) ? (
                  <iframe
                    src={videoPreview}
                    title="Product video preview"
                    className="aspect-video w-full"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                  />
                ) : (
                  <div className="p-3 text-xs text-text-muted">Preview unavailable for this video reference.</div>
                )}
              </div>
            ) : (
              <div className="flex aspect-video items-center justify-center rounded-xl border border-dashed border-border text-[10px] text-text-faint">
                Video preview
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}


