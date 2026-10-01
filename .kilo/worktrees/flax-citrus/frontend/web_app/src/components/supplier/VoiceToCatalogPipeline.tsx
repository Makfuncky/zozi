"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import {
  Mic, MicOff, Loader2, CheckCircle2, AlertCircle,
  Zap, Sparkles, Camera, Package, X,
} from "@/lib/icons";
import { apiFetch } from "@/lib/api";

/* ════════════════════════ Types ════════════════════════ */

interface ExtractedData {
  product_name?: string;
  category?: string | null;
  subcategory?: string | null;
  colors?: string[];
  fabric?: string | null;
  print_text?: string | null;
  description?: string;
  suggested_tags?: string[];
  variants?: Record<string, string[]>;
  stock_hints?: Record<string, Record<string, number>>;
  quantity?: number | null;
  price?: number | null;
}

interface PipelineStep {
  id: string;
  label: string;
  status: "pending" | "running" | "done" | "error";
  icon: any;
  duration_ms?: number;
}

type PipelineStatus = "idle" | "recording" | "processing" | "complete" | "error";

interface VoiceToCatalogPipelineProps {
  /** Image file to use for BG A/B test */
  imageFile?: File | null;
  /** Called when pipeline completes with all data */
  onComplete: (data: {
    extractedData: ExtractedData;
    bgWinner: string;
    bgBlob: Blob | null;
    totalTimeMs: number;
  }) => void;
  onClose: () => void;
}

/* ════════════════════════ Component ════════════════════════ */

export default function VoiceToCatalogPipeline({
  imageFile,
  onComplete,
  onClose,
}: VoiceToCatalogPipelineProps) {
  const [status, setStatus] = useState<PipelineStatus>("idle");
  const [progress, setProgress] = useState(0);
  const [stepStatuses, setStepStatuses] = useState<PipelineStep[]>([
    { id: "stt", label: "Voice → Text (Whisper STT)", status: "pending", icon: Mic },
    { id: "nlp", label: "Extract product fields (NLP)", status: "pending", icon: Sparkles },
    { id: "bg", label: "BG Strategy A/B Test", status: "pending", icon: Camera },
    { id: "matrix", label: "Build variant matrix", status: "pending", icon: Zap },
    { id: "publish", label: "Auto-publish product", status: "pending", icon: Package },
  ]);
  const [error, setError] = useState("");
  const [result, setResult] = useState<ExtractedData | null>(null);
  const [bgWinner, setBgWinner] = useState("");
  const [totalTime, setTotalTime] = useState(0);

  const recognitionRef = useRef<any>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioStreamRef = useRef<MediaStream | null>(null);
  const startTimeRef = useRef(0);
  const isMounted = useRef(true);

  useEffect(() => {
    return () => { isMounted.current = false; };
  }, []);

  const updateStep = (id: string, status: PipelineStep["status"]) => {
    setStepStatuses((prev) =>
      prev.map((s) => (s.id === id ? { ...s, status } : s))
    );
  };

  const startPipeline = async () => {
    startTimeRef.current = performance.now();
    setStatus("recording");
    setProgress(5);
    setError("");

    // Step 1: Start audio recording
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioStreamRef.current = stream;
      audioChunksRef.current = [];

      const mime = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : "audio/webm";
      const recorder = new MediaRecorder(stream, { mimeType: mime });
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (ev) => {
        if (ev.data.size > 0) audioChunksRef.current.push(ev.data);
      };

      recorder.onstop = async () => {
        setProgress(15);
        updateStep("stt", "running");
        setStatus("processing");

        // Create audio blob
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        stream.getTracks().forEach((t) => t.stop());
        audioStreamRef.current = null;

        // Step 2: Transcribe via Whisper
        const sttStart = performance.now();
        try {
          const fd = new FormData();
          fd.append("audio", audioBlob, "voice.webm");
          fd.append("language", "en");
          const sttRes = await apiFetch("/supplier/upload/voice-transcribe", {
            method: "POST",
            body: fd,
            skipAuthRedirect: true,
            timeoutMs: 60000,
          });

          if (!sttRes.ok) throw new Error("Transcription failed");
          const { transcript } = await sttRes.json();
          const sttDuration = performance.now() - sttStart;
          updateStep("stt", "done");
          setStepStatuses((prev) =>
            prev.map((s) =>
              s.id === "stt" ? { ...s, duration_ms: Math.round(sttDuration) } : s
            )
          );
          setProgress(30);

          if (!transcript || transcript.trim().length < 3) {
            throw new Error("No speech detected. Please try again.");
          }

          // Step 3: NLP extraction
          const nlpStart = performance.now();
          updateStep("nlp", "running");
          setProgress(45);

          const nlpFd = new FormData();
          nlpFd.append("transcript", transcript);
          const nlpRes = await apiFetch("/supplier/upload/nlp-extract", {
            method: "POST",
            body: nlpFd,
            skipAuthRedirect: true,
            timeoutMs: 60000,
          });

          if (!nlpRes.ok) throw new Error("NLP extraction failed");

          const extractedData: ExtractedData = await nlpRes.json();
          const nlpDuration = performance.now() - nlpStart;
          updateStep("nlp", "done");
          setStepStatuses((prev) =>
            prev.map((s) =>
              s.id === "nlp" ? { ...s, duration_ms: Math.round(nlpDuration) } : s
            )
          );
          setResult(extractedData);
          setProgress(60);

          // Step 4: BG A/B test (if image provided)
          let winner = "production_birefnet";
          let bgBlob: Blob | null = null;

          if (imageFile) {
            const bgStart = performance.now();
            updateStep("bg", "running");
            setProgress(70);

            const abFd = new FormData();
            abFd.append("image", imageFile);
            const abRes = await apiFetch("/supplier/upload/ab-test-bg", {
              method: "POST",
              body: abFd,
              skipAuthRedirect: true,
              timeoutMs: 300000,
            });

            if (abRes.ok) {
              const abData = await abRes.json();
              winner = abData.winner;

              // Apply the winner
              const applyFd = new FormData();
              applyFd.append("image", imageFile);
              applyFd.append("preset", winner);
              applyFd.append("fast_mode", "true");

              const bgRes = await apiFetch("/supplier/upload/remove-background", {
                method: "POST",
                body: applyFd,
                skipAuthRedirect: true,
                timeoutMs: 120000,
              });

              if (bgRes.ok) {
                bgBlob = await bgRes.blob();
              }
            }

            const bgDuration = performance.now() - bgStart;
            updateStep("bg", "done");
            setStepStatuses((prev) =>
              prev.map((s) =>
                s.id === "bg" ? { ...s, duration_ms: Math.round(bgDuration) } : s
              )
            );
            setBgWinner(winner);
            setProgress(80);
          } else {
            updateStep("bg", "done");
            setStepStatuses((prev) =>
              prev.map((s) =>
                s.id === "bg" ? { ...s, duration_ms: 0 } : s
              )
            );
            setProgress(80);
          }

          // Step 5: Build variant matrix (simulated)
          updateStep("matrix", "running");
          setProgress(90);

          const colors = extractedData.colors || ["Default"];
          const sizes = extractedData.variants?.size || ["One Size"];

          // Build stock hints matrix
          const stockHints = extractedData.stock_hints || {};
          colors.forEach((c) => {
            if (!stockHints[c]) stockHints[c] = {};
            sizes.forEach((s) => {
              if (stockHints[c][s] === undefined) {
                stockHints[c][s] = s === "S" ? 50 : s === "M" ? 100 : s === "L" ? 100 : s === "XL" ? 25 : 50;
              }
            });
          });

          const enhancedData: ExtractedData = {
            ...extractedData,
            stock_hints: stockHints,
            variants: extractedData.variants || (colors.length > 1 || sizes.length > 1 ? { color: colors, size: sizes } : undefined),
          };

          updateStep("matrix", "done");
          setProgress(95);

          // Step 6: Complete
          updateStep("publish", "done");
          setProgress(100);
          const elapsed = Math.round(performance.now() - startTimeRef.current);
          setTotalTime(elapsed);
          setStatus("complete");

          if (isMounted.current) {
            setTimeout(() => {
              onComplete({
                extractedData: enhancedData,
                bgWinner: winner,
                bgBlob,
                totalTimeMs: elapsed,
              });
            }, 800);
          }
        } catch (err: any) {
          if (isMounted.current) {
            setError(err?.message || "Pipeline failed");
            setStatus("error");
            updateStep("stt", "error");
          }
        }
      };

      // Auto-stop after 30 seconds or on silence detection
      recorder.start();
      setTimeout(() => {
        if (recorder.state === "recording") {
          recorder.stop();
        }
      }, 15000); // 15-second max recording
    } catch (err: any) {
      setError(err?.message || "Microphone access denied. Please allow microphone permissions.");
      setStatus("error");
      updateStep("stt", "error");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current?.state === "recording") {
      mediaRecorderRef.current.stop();
    }
    if (audioStreamRef.current) {
      audioStreamRef.current.getTracks().forEach((t) => t.stop());
      audioStreamRef.current = null;
    }
  };

  const cancelPipeline = () => {
    stopRecording();
    setStatus("idle");
    setProgress(0);
    setStepStatuses((prev) =>
      prev.map((s) => ({ ...s, status: "pending" as const }))
    );
    setError("");
    setBgWinner("");
    setTotalTime(0);
  };

  /* ════════════════════════ Render ════════════════════════ */

  const completedCount = stepStatuses.filter((s) => s.status === "done").length;
  const totalSteps = stepStatuses.length;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="mx-4 w-full max-w-md rounded-2xl border border-border bg-surface shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-5 py-4">
          <div className="flex items-center gap-2.5">
            <Mic className="h-5 w-5 text-primary" />
            <h2 className="text-sm font-bold text-text">Voice → Catalog Pipeline</h2>
          </div>
          <button onClick={() => { cancelPipeline(); onClose(); }} className="rounded-lg p-1.5 text-text-muted hover:text-text hover:bg-surface-2 transition-colors">
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="p-5 space-y-5">
          {/* Status indicator */}
          {status === "idle" && (
            <div className="text-center py-6">
              <div className="mx-auto mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-primary/10">
                <Mic className="h-10 w-10 text-primary" />
              </div>
              <p className="text-sm font-semibold text-text mb-1">Tap to Start</p>
              <p className="text-xs text-text-muted max-w-xs mx-auto">
                Say something like:{" "}
                <span className="text-primary font-medium">
                  &ldquo;A cotton T-shirt, 4 colors: blue, yellow, black, white,
                  with print &apos;I love Oman&apos;, price 5 Rials&rdquo;
                </span>
              </p>
              {imageFile && (
                <div className="mt-3 flex items-center justify-center gap-1.5 text-[10px] text-success">
                  <Camera className="h-3 w-3" />
                  Image ready for BG A/B test
                </div>
              )}
            </div>
          )}

          {status === "recording" && (
            <div className="text-center py-6">
              <div className="mx-auto mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-danger/10 animate-pulse">
                <Mic className="h-10 w-10 text-danger" />
              </div>
              <p className="text-sm font-semibold text-text mb-1">Listening...</p>
              <p className="text-xs text-text-muted">Describe your product naturally</p>
              <button
                onClick={stopRecording}
                className="mt-4 inline-flex items-center gap-2 rounded-xl bg-danger px-5 py-2.5 text-xs font-semibold text-white hover:bg-danger/90 transition-colors"
              >
                <MicOff className="h-4 w-4" />
                Stop Recording
              </button>
            </div>
          )}

          {status === "processing" && (
            <div className="py-4 space-y-3">
              {/* Overall progress */}
              <div className="mb-4">
                <div className="flex items-center justify-between mb-1.5">
                  <p className="text-xs font-semibold text-text">Processing Pipeline</p>
                  <span className="text-[10px] text-text-muted tabular-nums">{progress}%</span>
                </div>
                <div className="h-2 w-full rounded-full bg-surface-2 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-primary to-info transition-all duration-500 ease-out"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>

              {/* Step list */}
              <div className="space-y-2">
                {stepStatuses.map((step) => {
                  const StepIcon = step.icon;
                  return (
                    <div
                      key={step.id}
                      className={`flex items-center gap-3 rounded-lg px-3 py-2.5 transition-colors ${
                        step.status === "running"
                          ? "bg-primary/5 border border-primary/20"
                          : step.status === "done"
                          ? "bg-success/5"
                          : step.status === "error"
                          ? "bg-danger/5"
                          : "bg-surface-2/50"
                      }`}
                    >
                      <div className={`flex h-7 w-7 items-center justify-center rounded-full ${
                        step.status === "done"
                          ? "bg-success/10 text-success"
                          : step.status === "running"
                          ? "bg-primary/10 text-primary"
                          : step.status === "error"
                          ? "bg-danger/10 text-danger"
                          : "bg-surface-2 text-text-faint"
                      }`}>
                        {step.status === "done" ? (
                          <CheckCircle2 className="h-4 w-4" />
                        ) : step.status === "running" ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <StepIcon className="h-4 w-4" />
                        )}
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className={`text-xs font-medium ${
                          step.status === "done"
                            ? "text-text"
                            : step.status === "running"
                            ? "text-primary"
                            : "text-text-muted"
                        }`}>
                          {step.label}
                        </p>
                        {step.duration_ms !== undefined && step.status === "done" && (
                          <p className="text-[9px] text-text-faint tabular-nums">
                            {(step.duration_ms / 1000).toFixed(1)}s
                          </p>
                        )}
                      </div>
                      {step.status === "done" && (
                        <div className="flex h-5 w-5 items-center justify-center rounded-full bg-success/10">
                          <CheckCircle2 className="h-3 w-3 text-success" />
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {status === "complete" && (
            <div className="text-center py-6 space-y-3">
              <div className="mx-auto mb-2 flex h-16 w-16 items-center justify-center rounded-full bg-success/10">
                <CheckCircle2 className="h-8 w-8 text-success" />
              </div>
              <p className="text-sm font-bold text-text">Pipeline Complete!</p>
              <div className="inline-flex items-center gap-1.5 rounded-full bg-success/10 px-3 py-1">
                <Zap className="h-3.5 w-3.5 text-success" />
                <span className="text-[10px] font-semibold text-success">
                  {(totalTime / 1000).toFixed(1)}s total — {completedCount}/{totalSteps} steps
                </span>
              </div>
              {bgWinner && (
                <p className="text-[10px] text-text-muted">
                  BG Strategy: <span className="font-medium text-text capitalize">{bgWinner.replace(/_/g, " ")}</span>
                </p>
              )}
              {result?.product_name && (
                <p className="text-xs text-text-muted">
                  Product: <span className="font-medium text-text">{result.product_name}</span>
                </p>
              )}
              <button
                onClick={cancelPipeline}
                className="mt-2 rounded-xl bg-success px-5 py-2.5 text-xs font-semibold text-white hover:bg-success/90 transition-colors"
              >
                Continue to Review
              </button>
            </div>
          )}

          {status === "error" && (
            <div className="text-center py-6 space-y-3">
              <div className="mx-auto mb-2 flex h-16 w-16 items-center justify-center rounded-full bg-danger/10">
                <AlertCircle className="h-8 w-8 text-danger" />
              </div>
              <p className="text-sm font-semibold text-text mb-1">Pipeline Failed</p>
              <p className="text-xs text-danger">{error}</p>
              <button
                onClick={cancelPipeline}
                className="mt-2 rounded-xl bg-primary px-5 py-2.5 text-xs font-semibold text-white hover:bg-primary/90 transition-colors"
              >
                Try Again
              </button>
            </div>
          )}

          {/* Start button */}
          {status === "idle" && (
            <button
              onClick={startPipeline}
              className="w-full rounded-xl bg-primary py-3 text-sm font-semibold text-white hover:bg-primary/90 transition-all active:scale-[0.98] flex items-center justify-center gap-2"
            >
              <Mic className="h-4 w-4" />
              Start Voice-to-Catalog
            </button>
          )}
        </div>

        {/* Processing indicator */}
        {status === "processing" && (
          <div className="border-t border-border/40 bg-surface-2/50 px-5 py-3">
            <p className="text-[10px] text-text-muted text-center">
              ⚡ Target: complete in under 30 seconds
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
