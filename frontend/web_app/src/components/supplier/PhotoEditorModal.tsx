"use client";

import { Button } from "@/components/ui/Button";

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  X,
  Crop,
  RotateCw,
  FlipHorizontal,
  FlipVertical,
  ZoomIn,
  Sun,
  Contrast,
  Droplet,
  Undo2,
  Check,
  Loader2,
  Square,
} from '@/lib/icons';

interface PhotoEditorModalProps {
  src: string;
  fileName?: string;
  onApply: (file: File) => void;
  onClose: () => void;
}

type CropRect = { x: number; y: number; w: number; h: number };

const ASPECTS: Array<{ key: string; label: string; ratio: number | null }> = [
  { key: 'free', label: 'Free', ratio: null },
  { key: '1:1', label: '1:1', ratio: 1 },
  { key: '4:3', label: '4:3', ratio: 4 / 3 },
  { key: '3:4', label: '3:4', ratio: 3 / 4 },
  { key: '16:9', label: '16:9', ratio: 16 / 9 },
];

const DEFAULT_ADJ = { brightness: 100, contrast: 100, saturation: 100 };

export default function PhotoEditorModal({ src, fileName, onApply, onClose }: PhotoEditorModalProps) {
  const imgRef = useRef<HTMLImageElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [loaded, setLoaded] = useState(false);
  const [natural, setNatural] = useState({ w: 0, h: 0 });
  const [rotation, setRotation] = useState(0);
  const [flipH, setFlipH] = useState(false);
  const [flipV, setFlipV] = useState(false);
  const [adj, setAdj] = useState(DEFAULT_ADJ);
  const [aspect, setAspect] = useState<string>('free');
  const [crop, setCrop] = useState<CropRect | null>(null);
  const [cropMode, setCropMode] = useState(false);
  const [saving, setSaving] = useState(false);

  const dragState = useRef<{
    mode: 'move' | 'nw' | 'ne' | 'sw' | 'se' | 'new';
    startX: number;
    startY: number;
    orig: CropRect;
    boxW: number;
    boxH: number;
  } | null>(null);

  const filterStr = useMemo(
    () => `brightness(${adj.brightness}%) contrast(${adj.contrast}%) saturate(${adj.saturation}%)`,
    [adj],
  );

  const onImgLoad = () => {
    const img = imgRef.current;
    if (!img) return;
    setNatural({ w: img.naturalWidth, h: img.naturalHeight });
    setLoaded(true);
  };

  // Displayed image box (contained) inside container
  const getImgBox = useCallback(() => {
    const el = imgRef.current;
    if (!el) return null;
    return { w: el.clientWidth, h: el.clientHeight, left: el.offsetLeft, top: el.offsetTop };
  }, []);

  const resetCrop = useCallback(() => {
    const box = getImgBox();
    if (!box) return;
    const ratio = ASPECTS.find((a) => a.key === aspect)?.ratio ?? null;
    let w = box.w * 0.8;
    let h = box.h * 0.8;
    if (ratio) {
      if (w / h > ratio) w = h * ratio;
      else h = w / ratio;
    }
    setCrop({ x: (box.w - w) / 2, y: (box.h - h) / 2, w, h });
  }, [aspect, getImgBox]);

  useEffect(() => {
    if (cropMode) resetCrop();
    else setCrop(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cropMode, aspect]);

  const clampCrop = (c: CropRect, boxW: number, boxH: number): CropRect => {
    const w = Math.min(c.w, boxW);
    const h = Math.min(c.h, boxH);
    const x = Math.max(0, Math.min(c.x, boxW - w));
    const y = Math.max(0, Math.min(c.y, boxH - h));
    return { x, y, w, h };
  };

  const onPointerDown = (e: React.PointerEvent, mode: 'move' | 'nw' | 'ne' | 'sw' | 'se') => {
    if (!crop) return;
    e.stopPropagation();
    (e.target as HTMLElement).setPointerCapture?.(e.pointerId);
    const box = getImgBox();
    if (!box) return;
    dragState.current = { mode, startX: e.clientX, startY: e.clientY, orig: { ...crop }, boxW: box.w, boxH: box.h };
  };

  const onPointerMove = (e: React.PointerEvent) => {
    const ds = dragState.current;
    if (!ds || !crop) return;
    const dx = e.clientX - ds.startX;
    const dy = e.clientY - ds.startY;
    const ratio = ASPECTS.find((a) => a.key === aspect)?.ratio ?? null;
    let next = { ...ds.orig };
    if (ds.mode === 'move') {
      next.x = ds.orig.x + dx;
      next.y = ds.orig.y + dy;
    } else {
      if (ds.mode.includes('e')) next.w = ds.orig.w + dx;
      if (ds.mode.includes('s')) next.h = ds.orig.h + dy;
      if (ds.mode.includes('w')) { next.w = ds.orig.w - dx; next.x = ds.orig.x + dx; }
      if (ds.mode.includes('n')) { next.h = ds.orig.h - dy; next.y = ds.orig.y + dy; }
      if (ratio) {
        next.h = next.w / ratio;
        if (ds.mode.includes('n')) next.y = ds.orig.y + ds.orig.h - next.h;
      }
      next.w = Math.max(24, next.w);
      next.h = Math.max(24, next.h);
    }
    setCrop(clampCrop(next, ds.boxW, ds.boxH));
  };

  const onPointerUp = () => { dragState.current = null; };

  const rotateCw = () => setRotation((r) => (r + 90) % 360);
  const reset = () => {
    setRotation(0); setFlipH(false); setFlipV(false); setAdj(DEFAULT_ADJ);
    setCropMode(false); setCrop(null); setAspect('free');
  };

  const apply = async () => {
    if (!loaded) return;
    setSaving(true);
    try {
      const img = imgRef.current!;
      const box = getImgBox();

      // Source region in natural pixels (before rotation)
      let sx = 0, sy = 0, sw = natural.w, sh = natural.h;
      if (cropMode && crop && box) {
        const scaleX = natural.w / box.w;
        const scaleY = natural.h / box.h;
        sx = crop.x * scaleX;
        sy = crop.y * scaleY;
        sw = crop.w * scaleX;
        sh = crop.h * scaleY;
      }

      const rot = ((rotation % 360) + 360) % 360;
      const swapped = rot === 90 || rot === 270;
      const outW = Math.round(swapped ? sh : sw);
      const outH = Math.round(swapped ? sw : sh);

      const canvas = document.createElement('canvas');
      canvas.width = outW;
      canvas.height = outH;
      const ctx = canvas.getContext('2d');
      if (!ctx) throw new Error('no ctx');
      ctx.filter = filterStr;
      ctx.translate(outW / 2, outH / 2);
      ctx.rotate((rot * Math.PI) / 180);
      ctx.scale(flipH ? -1 : 1, flipV ? -1 : 1);
      ctx.drawImage(img, sx, sy, sw, sh, -sw / 2, -sh / 2, sw, sh);

      const blob: Blob | null = await new Promise((resolve) =>
        canvas.toBlob((b) => resolve(b), 'image/png', 0.95),
      );
      if (!blob) throw new Error('no blob');
      const base = (fileName || 'edited').replace(/\.\w+$/, '') || 'edited';
      const file = new File([blob], `${base}_edited.png`, { type: 'image/png' });
      onApply(file);
    } finally {
      setSaving(false);
    }
  };

  const transform = `rotate(${rotation}deg) scaleX(${flipH ? -1 : 1}) scaleY(${flipV ? -1 : 1})`;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center theme-overlay p-4" onClick={onClose}>
      <div
        className="theme-card w-full max-w-4xl rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-border/20">
          <h3 className="text-lg font-bold text-text flex items-center gap-2">
            <Crop className="w-5 h-5 text-primary" /> Edit Photo
          </h3>
          <Button variant="danger" type="button" onClick={onClose}>
            <X className="w-5 h-5" />
          </Button>
        </div>

        {/* Canvas area */}
        <div className="flex-1 overflow-auto bg-surface-1 p-4">
          <div
            ref={containerRef}
            className="relative mx-auto flex items-center justify-center select-none"
            style={{ minHeight: 320, maxHeight: '55vh' }}
            onPointerMove={onPointerMove}
            onPointerUp={onPointerUp}
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              ref={imgRef}
              src={src}
              alt="Editing"
              onLoad={onImgLoad}
              draggable={false}
              className="max-w-full object-contain"
              style={{ maxHeight: '55vh', transform, filter: filterStr, transition: 'transform 0.15s ease' }}
            />

            {/* Crop overlay */}
            {cropMode && crop && (
              <div
                className="absolute border-2 border-primary shadow-[0_0_0_9999px_rgba(0,0,0,0.45)] cursor-move"
                style={{ left: crop.x + (getImgBox()?.left || 0), top: crop.y + (getImgBox()?.top || 0), width: crop.w, height: crop.h }}
                onPointerDown={(e) => onPointerDown(e, 'move')}
              >
                {(['nw', 'ne', 'sw', 'se'] as const).map((h) => (
                  <div
                    key={h}
                    onPointerDown={(e) => onPointerDown(e, h)}
                    className="absolute w-3.5 h-3.5 bg-primary border border-white rounded-sm"
                    style={{
                      cursor: `${h}-resize`,
                      left: h.includes('w') ? -7 : undefined,
                      right: h.includes('e') ? -7 : undefined,
                      top: h.includes('n') ? -7 : undefined,
                      bottom: h.includes('s') ? -7 : undefined,
                    }}
                  />
                ))}
              </div>
            )}

            {!loaded && (
              <div className="absolute inset-0 flex items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
              </div>
            )}
          </div>
        </div>

        {/* Controls */}
        <div className="border-t border-border/20 p-4 space-y-4 overflow-auto" style={{ maxHeight: '30vh' }}>
          {/* Transform buttons */}
          <div className="flex flex-wrap gap-2">
            <button type="button" onClick={rotateCw} className="editor-btn"><RotateCw className="w-4 h-4" /> Rotate</button>
            <button type="button" onClick={() => setFlipH((v) => !v)} className={`editor-btn ${flipH ? 'editor-btn-active' : ''}`}><FlipHorizontal className="w-4 h-4" /> Flip H</button>
            <button type="button" onClick={() => setFlipV((v) => !v)} className={`editor-btn ${flipV ? 'editor-btn-active' : ''}`}><FlipVertical className="w-4 h-4" /> Flip V</button>
            <button type="button" onClick={() => setCropMode((v) => !v)} className={`editor-btn ${cropMode ? 'editor-btn-active' : ''}`}><Crop className="w-4 h-4" /> Crop</button>
            <button type="button" onClick={reset} className="editor-btn"><Undo2 className="w-4 h-4" /> Reset</button>
          </div>

          {/* Aspect presets (only when cropping) */}
          {cropMode && (
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs text-text-muted flex items-center gap-1"><Square className="w-3.5 h-3.5" /> Ratio:</span>
              {ASPECTS.map((a) => (
                <button
                  key={a.key}
                  type="button"
                  onClick={() => setAspect(a.key)}
                  className={`px-2.5 py-1 rounded-md text-xs border transition-colors ${
                    aspect === a.key ? 'bg-primary text-white border-primary' : 'bg-surface-2 text-text border-border/50 hover:bg-primary/10'
                  }`}
                >
                  {a.label}
                </button>
              ))}
            </div>
          )}

          {/* Adjustment sliders */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <label className="flex flex-col gap-1">
              <span className="text-xs text-text-muted flex items-center gap-1"><Sun className="w-3.5 h-3.5" /> Brightness {adj.brightness}%</span>
              <input type="range" min={20} max={200} value={adj.brightness} onChange={(e) => setAdj((a) => ({ ...a, brightness: +e.target.value }))} className="theme-range" />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-xs text-text-muted flex items-center gap-1"><Contrast className="w-3.5 h-3.5" /> Contrast {adj.contrast}%</span>
              <input type="range" min={20} max={200} value={adj.contrast} onChange={(e) => setAdj((a) => ({ ...a, contrast: +e.target.value }))} className="theme-range" />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-xs text-text-muted flex items-center gap-1"><Droplet className="w-3.5 h-3.5" /> Saturation {adj.saturation}%</span>
              <input type="range" min={0} max={200} value={adj.saturation} onChange={(e) => setAdj((a) => ({ ...a, saturation: +e.target.value }))} className="theme-range" />
            </label>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 px-5 py-3 border-t border-border/20">
          <Button variant="primary" type="button" onClick={onClose}>Cancel</Button>
          <Button variant="primary" type="button" onClick={apply} disabled={!loaded || saving}>
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />} Apply
          </Button>
        </div>
      </div>
    </div>
  );
}
