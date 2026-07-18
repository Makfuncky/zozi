"use client";

import { Button } from "@/components/ui/Button";

import { useCallback, useEffect, useRef, useState } from 'react';
import {
  X, ZoomIn, ZoomOut, RotateCw, RotateCcw,
  Sun, Moon, Layers, Grid2x2, Maximize2,
  Check, Loader2, RefreshCw, Square, Camera,
} from '@/lib/icons';

interface ProductImageCanvasProps {
  src: string;
  fileName?: string;
  onApply: (file: File) => void;
  onClose: () => void;
}

type BgMode = 'transparent' | 'white' | 'black' | 'custom';

const BR_CANVAS_SIZE = 800;
const ASPECTS: Array<{ key: string; label: string; w: number; h: number | null }> = [
  { key: 'free', label: 'Free', w: -1, h: null },
  { key: '1:1', label: '1:1', w: 1, h: 1 },
  { key: '4:3', label: '4:3', w: 4, h: 3 },
  { key: '3:4', label: '3:4', w: 3, h: 4 },
  { key: '16:9', label: '16:9', w: 16, h: 9 },
];

export default function ProductImageCanvas({ src, fileName, onApply, onClose }: ProductImageCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const [loaded, setLoaded] = useState(false);
  const [imgNatural, setImgNatural] = useState({ w: 0, h: 0 });
  const [zoom, setZoom] = useState(1);
  const [rotation, setRotation] = useState(0);
  const [panX, setPanX] = useState(0);
  const [panY, setPanY] = useState(0);
  const [bgMode, setBgMode] = useState<BgMode>('transparent');
  const [customColor, setCustomColor] = useState('#e5e7eb');
  const [aspect, setAspect] = useState('1:1');
  const [showGrid, setShowGrid] = useState(false);
  const [isPanning, setIsPanning] = useState(false);
  const [saving, setSaving] = useState(false);

  const panStart = useRef({ x: 0, y: 0, panX: 0, panY: 0 });

  const bgColor = bgMode === 'transparent' ? null : bgMode === 'white' ? '#ffffff' : bgMode === 'black' ? '#000000' : customColor;

  const getOutputSize = useCallback(() => {
    const asp = ASPECTS.find((a) => a.key === aspect);
    if (!asp || asp.w === -1) return { w: BR_CANVAS_SIZE, h: BR_CANVAS_SIZE };
    const base = BR_CANVAS_SIZE;
    const ratio = asp.w / (asp.h ?? 1);
    if (ratio >= 1) return { w: base, h: Math.round(base / ratio) };
    return { w: Math.round(base * ratio), h: base };
  }, [aspect]);

  const drawScene = useCallback(() => {
    const canvas = canvasRef.current;
    const img = imgRef.current;
    if (!canvas || !img || !loaded) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const out = getOutputSize();
    const dpr = window.devicePixelRatio || 1;
    canvas.width = out.w * dpr;
    canvas.height = out.h * dpr;
    canvas.style.width = `${out.w}px`;
    canvas.style.height = `${out.h}px`;
    ctx.scale(dpr, dpr);

    // Background
    if (bgColor) {
      ctx.fillStyle = bgColor;
      ctx.fillRect(0, 0, out.w, out.h);
    } else {
      ctx.clearRect(0, 0, out.w, out.h);
      // Checkerboard for transparent
      const s = 10;
      ctx.fillStyle = '#ccc';
      ctx.fillRect(0, 0, out.w, out.h);
      ctx.fillStyle = '#fff';
      for (let y = 0; y < out.h; y += s) {
        for (let x = 0; x < out.w; x += s) {
          if ((Math.floor(x / s) + Math.floor(y / s)) % 2 === 0) {
            ctx.fillRect(x, y, s, s);
          }
        }
      }
    }

    // Grid overlay
    if (showGrid) {
      ctx.strokeStyle = 'rgba(255,255,255,0.25)';
      ctx.lineWidth = 1;
      const cols = 3, rows = 3;
      for (let i = 1; i < cols; i++) {
        const x = (out.w / cols) * i;
        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, out.h); ctx.stroke();
      }
      for (let i = 1; i < rows; i++) {
        const y = (out.h / rows) * i;
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(out.w, y); ctx.stroke();
      }
    }

    // Calculate image placement
    const rad = (rotation * Math.PI) / 180;
    const cos = Math.abs(Math.cos(rad));
    const sin = Math.abs(Math.sin(rad));
    const rotW = imgNatural.w * cos + imgNatural.h * sin;
    const rotH = imgNatural.w * sin + imgNatural.h * cos;

    const fitScale = Math.min((out.w * 0.85) / rotW, (out.h * 0.85) / rotH);
    const drawW = imgNatural.w * fitScale * zoom;
    const drawH = imgNatural.h * fitScale * zoom;

    const cx = out.w / 2 + panX;
    const cy = out.h / 2 + panY;

    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(rad);
    ctx.drawImage(img, -drawW / 2, -drawH / 2, drawW, drawH);
    ctx.restore();

    // Border
    ctx.strokeStyle = 'rgba(0,0,0,0.1)';
    ctx.lineWidth = 1;
    ctx.strokeRect(0, 0, out.w, out.h);
  }, [loaded, bgColor, zoom, rotation, panX, panY, aspect, showGrid, imgNatural, getOutputSize]);

  useEffect(() => { drawScene(); }, [drawScene]);

  const onImgLoad = () => {
    if (!imgRef.current) return;
    const nw = imgRef.current.naturalWidth;
    const nh = imgRef.current.naturalHeight;
    setImgNatural({ w: nw, h: nh });
    setLoaded(true);
  };

  // Pan handlers
  const onPointerDown = (e: React.PointerEvent) => {
    setIsPanning(true);
    panStart.current = { x: e.clientX, y: e.clientY, panX, panY };
  };
  const onPointerMove = (e: React.PointerEvent) => {
    if (!isPanning) return;
    setPanX(panStart.current.panX + (e.clientX - panStart.current.x));
    setPanY(panStart.current.panY + (e.clientY - panStart.current.y));
  };
  const onPointerUp = () => setIsPanning(false);

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    setZoom((z) => Math.max(0.1, Math.min(5, z - e.deltaY * 0.001)));
  };

  const rotateCW = () => setRotation((r) => r + 90);
  const rotateCCW = () => setRotation((r) => r - 90);
  const resetView = () => { setZoom(1); setPanX(0); setPanY(0); setRotation(0); };

  const handleApply = async () => {
    setSaving(true);
    try {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const out = getOutputSize();
      const dpr = window.devicePixelRatio || 1;
      // Create a clean output canvas at output size
      const outCanvas = document.createElement('canvas');
      outCanvas.width = out.w;
      outCanvas.height = out.h;
      const outCtx = outCanvas.getContext('2d');
      if (!outCtx) return;

      outCtx.drawImage(canvas, 0, 0, out.w * dpr, out.h * dpr, 0, 0, out.w, out.h);

      const blob: Blob | null = await new Promise((resolve) => outCanvas.toBlob((b) => resolve(b), 'image/png', 0.95));
      if (!blob) throw new Error('No blob');
      const base = (fileName || 'product').replace(/\.\w+$/, '') || 'product';
      const file = new File([blob], `${base}_canvas.png`, { type: 'image/png' });
      onApply(file);
    } finally {
      setSaving(false);
    }
  };

  const zoomPercent = Math.round(zoom * 100);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center theme-overlay p-2 sm:p-4" onClick={onClose}>
      <div className="theme-card w-full max-w-5xl rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[96vh]" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-border/20">
          <h3 className="text-lg font-bold text-text flex items-center gap-2">
            <Camera className="w-5 h-5 text-primary" /> Product Photo Studio
          </h3>
          <Button variant="danger" type="button" onClick={onClose}>
            <X className="w-5 h-5" />
          </Button>
        </div>

        {/* Hidden image for drawing */}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img ref={imgRef} src={src} alt="" onLoad={onImgLoad} className="hidden" crossOrigin="anonymous" />

        {/* Canvas area */}
        <div
          ref={containerRef}
          className="relative flex-1 overflow-hidden bg-surface-1 flex items-center justify-center cursor-grab active:cursor-grabbing select-none"
          onPointerDown={onPointerDown}
          onPointerMove={onPointerMove}
          onPointerUp={onPointerUp}
          onPointerLeave={onPointerUp}
          onWheel={handleWheel}
          style={{ minHeight: 300 }}
        >
          <canvas ref={canvasRef} className="max-w-full max-h-full" />
          {!loaded && (
            <div className="absolute inset-0 flex items-center justify-center">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          )}
          {/* Zoom badge */}
          {loaded && (
            <div className="absolute bottom-3 left-3 px-2 py-1 rounded-md bg-black/50 text-white text-xs font-medium">
              {zoomPercent}%
            </div>
          )}
        </div>

        {/* Controls */}
        <div className="border-t border-border/20 p-3 space-y-3 overflow-auto max-h-[35vh]">
          {/* Row 1: Zoom + Rotate + Grid + Reset */}
          <div className="flex flex-wrap items-center gap-2">
            <button type="button" onClick={() => setZoom((z) => Math.max(0.1, z - 0.2))} className="editor-btn" title="Zoom out"><ZoomOut className="w-4 h-4" /></button>
            <input type="range" min={10} max={500} value={zoom * 100}
              onChange={(e) => setZoom(+e.target.value / 100)}
              className="w-24 sm:w-32 theme-range" />
            <button type="button" onClick={() => setZoom((z) => Math.min(5, z + 0.2))} className="editor-btn" title="Zoom in"><ZoomIn className="w-4 h-4" /></button>
            <span className="text-xs text-text-muted w-10">{zoomPercent}%</span>

            <div className="w-px h-6 bg-border/30 mx-1" />

            <button type="button" onClick={rotateCCW} className="editor-btn" title="Rotate left"><RotateCcw className="w-4 h-4" /></button>
            <button type="button" onClick={rotateCW} className="editor-btn" title="Rotate right"><RotateCw className="w-4 h-4" /></button>
            <button type="button" onClick={resetView} className="editor-btn" title="Reset view"><RefreshCw className="w-4 h-4" /></button>

            <div className="w-px h-6 bg-border/30 mx-1" />

            <button type="button" onClick={() => setShowGrid(!showGrid)}
              className={`editor-btn ${showGrid ? 'editor-btn-active' : ''}`} title="Toggle grid">
              <Grid2x2 className="w-4 h-4" />
            </button>
            <button type="button" onClick={() => { setZoom(1); setPanX(0); setPanY(0); }}
              className="editor-btn" title="Fit to frame">
              <Maximize2 className="w-4 h-4" />
            </button>
          </div>

          {/* Row 2: Background + Aspect */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs text-text-muted flex items-center gap-1"><Layers className="w-3.5 h-3.5" /> BG:</span>
            <button type="button" onClick={() => setBgMode('transparent')} className={`editor-btn ${bgMode === 'transparent' ? 'editor-btn-active' : ''}`}>
              <span className="w-3 h-3 rounded border border-border/50 bg-[url('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAYAAADED76LAAAAGElEQVQYV2N8+vTpfwY0gNGYqEiKBAQAERQDFeNNBmMAAAAASUVORK5CYII=')]" /> Transparent
            </button>
            <button type="button" onClick={() => setBgMode('white')} className={`editor-btn ${bgMode === 'white' ? 'editor-btn-active' : ''}`}>
              <span className="w-3 h-3 rounded border border-border/50 bg-white" /> White
            </button>
            <button type="button" onClick={() => setBgMode('black')} className={`editor-btn ${bgMode === 'black' ? 'editor-btn-active' : ''}`}>
              <span className="w-3 h-3 rounded border border-border/50 bg-black" /> Black
            </button>
            <button type="button" onClick={() => setBgMode('custom')} className={`editor-btn ${bgMode === 'custom' ? 'editor-btn-active' : ''}`}>
              <span className="w-3 h-3 rounded border border-border/50" style={{ backgroundColor: customColor }} /> Custom
            </button>
            {bgMode === 'custom' && (
              <input type="color" value={customColor} onChange={(e) => setCustomColor(e.target.value)}
                className="w-8 h-8 p-0.5 rounded border border-border/50 cursor-pointer" />
            )}

            <div className="w-px h-6 bg-border/30 mx-1" />

            <span className="text-xs text-text-muted flex items-center gap-1"><Square className="w-3.5 h-3.5" /> Ratio:</span>
            {ASPECTS.map((a) => (
              <button key={a.key} type="button" onClick={() => setAspect(a.key)}
                className={`px-2 py-0.5 rounded-md text-xs border transition-colors ${aspect === a.key ? 'bg-primary text-white border-primary' : 'bg-surface-2 text-text border-border/50 hover:bg-primary/10'}`}>
                {a.label}
              </button>
            ))}
          </div>

          {/* Tooltip */}
          <p className="text-[11px] text-text-muted">Drag to pan · Scroll to zoom · Right-click to reset</p>
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 px-4 py-3 border-t border-border/20">
          <Button variant="primary" type="button" onClick={onClose}>Cancel</Button>
          <Button variant="primary" type="button" onClick={handleApply} disabled={!loaded || saving}>
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />} Apply to Product
          </Button>
        </div>
      </div>

      <style jsx>{`
        :global(.editor-btn) {
          display: inline-flex;
          align-items: center;
          gap: 0.3rem;
          padding: 0.35rem 0.6rem;
          border-radius: 0.5rem;
          border: 1px solid rgba(120, 120, 120, 0.3);
          font-size: 0.75rem;
          background: var(--surface-2, #f3f4f6);
          color: var(--text, #1f2937);
          transition: all 0.15s ease;
          white-space: nowrap;
        }
        :global(.editor-btn:hover) {
          background: var(--primary, #2563eb);
          color: #fff;
          border-color: var(--primary, #2563eb);
        }
        :global(.editor-btn-active) {
          background: var(--primary, #2563eb);
          color: #fff;
          border-color: var(--primary, #2563eb);
        }
      `}</style>
    </div>
  );
}
