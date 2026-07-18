"use client";

import { useCallback, useEffect, useRef, useState } from "react";

type Point = { x: number; y: number };

interface SignaturePadProps {
  height?: number;
  strokeColor?: string;
  backgroundColor?: string;
  borderColor?: string;
  className?: string;
  onChange: (value: string | null) => void;
}

function drawStroke(
  context: CanvasRenderingContext2D,
  stroke: Point[],
  strokeColor: string,
) {
  if (!stroke.length) return;

  context.strokeStyle = strokeColor;
  context.lineWidth = 2.5;
  context.lineCap = "round";
  context.lineJoin = "round";
  context.beginPath();
  context.moveTo(stroke[0].x, stroke[0].y);

  for (let index = 1; index < stroke.length; index += 1) {
    context.lineTo(stroke[index].x, stroke[index].y);
  }

  if (stroke.length === 1) {
    context.lineTo(stroke[0].x + 0.1, stroke[0].y + 0.1);
  }

  context.stroke();
}

export default function SignaturePad({
  height = 180,
  strokeColor = "#111827",
  backgroundColor = "#ffffff",
  borderColor = "#d1d5db",
  className = "",
  onChange,
}: SignaturePadProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const drawingRef = useRef(false);
  const currentStrokeRef = useRef<Point[]>([]);
  const strokesRef = useRef<Point[][]>([]);
  const [hasSignature, setHasSignature] = useState(false);

  const paintBackground = useCallback((context: CanvasRenderingContext2D, width: number, canvasHeight: number) => {
    context.save();
    context.fillStyle = backgroundColor;
    context.fillRect(0, 0, width, canvasHeight);
    context.restore();
  }, [backgroundColor]);

  const exportSignature = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || strokesRef.current.length === 0) {
      onChange(null);
      return;
    }
    onChange(canvas.toDataURL("image/png"));
  }, [onChange]);

  const redraw = useCallback(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const width = container.clientWidth;
    if (!width) return;

    const devicePixelRatio = window.devicePixelRatio || 1;
    canvas.width = Math.round(width * devicePixelRatio);
    canvas.height = Math.round(height * devicePixelRatio);
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;

    const context = canvas.getContext("2d");
    if (!context) return;

    context.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0);
    paintBackground(context, width, height);

    for (const stroke of strokesRef.current) {
      drawStroke(context, stroke, strokeColor);
    }
  }, [height, paintBackground, strokeColor]);

  useEffect(() => {
    redraw();
    const handleResize = () => redraw();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [redraw]);

  useEffect(() => {
    redraw();
  }, [backgroundColor, borderColor, redraw, strokeColor]);

  function pointFromEvent(event: React.PointerEvent<HTMLCanvasElement>): Point {
    const bounds = event.currentTarget.getBoundingClientRect();
    return {
      x: event.clientX - bounds.left,
      y: event.clientY - bounds.top,
    };
  }

  function startDrawing(event: React.PointerEvent<HTMLCanvasElement>) {
    const canvas = canvasRef.current;
    const context = canvas?.getContext("2d");
    if (!canvas || !context) return;

    drawingRef.current = true;
    currentStrokeRef.current = [pointFromEvent(event)];
    event.currentTarget.setPointerCapture(event.pointerId);
    redraw();
    drawStroke(context, currentStrokeRef.current, strokeColor);
  }

  function continueDrawing(event: React.PointerEvent<HTMLCanvasElement>) {
    if (!drawingRef.current) return;

    const canvas = canvasRef.current;
    const context = canvas?.getContext("2d");
    if (!canvas || !context) return;

    currentStrokeRef.current = [...currentStrokeRef.current, pointFromEvent(event)];
    redraw();
    drawStroke(context, currentStrokeRef.current, strokeColor);
  }

  function stopDrawing(event?: React.PointerEvent<HTMLCanvasElement>) {
    if (!drawingRef.current) return;
    drawingRef.current = false;
    if (event) {
      try {
        event.currentTarget.releasePointerCapture(event.pointerId);
      } catch {}
    }

    if (currentStrokeRef.current.length > 0) {
      strokesRef.current = [...strokesRef.current, currentStrokeRef.current];
      currentStrokeRef.current = [];
      setHasSignature(true);
      redraw();
      exportSignature();
    }
  }

  function clearSignature() {
    strokesRef.current = [];
    currentStrokeRef.current = [];
    setHasSignature(false);
    redraw();
    onChange(null);
  }

  return (
    <div className={`space-y-2 ${className}`.trim()}>
      <div
        ref={containerRef}
        className="overflow-hidden rounded-xl border bg-white"
        style={{ borderColor }}
      >
        <canvas
          ref={canvasRef}
          aria-label="Delivery signature pad"
          data-testid="delivery-signature-pad"
          className="block touch-none"
          onPointerDown={startDrawing}
          onPointerMove={continueDrawing}
          onPointerUp={stopDrawing}
          onPointerLeave={() => stopDrawing()}
          onPointerCancel={() => stopDrawing()}
        />
      </div>
      <div className="flex items-center justify-between gap-3 text-xs text-text-muted">
        <span>{hasSignature ? "Signature captured" : "Draw the customer signature here."}</span>
        <button
          type="button"
          onClick={clearSignature}
          className="rounded-lg border border-border px-2.5 py-1 font-semibold text-text hover:bg-surface-2"
        >
          Clear Signature
        </button>
      </div>
    </div>
  );
}


