"use client";

import { Button } from "@/components/ui/Button";

import { useState, useRef, useEffect, useCallback } from 'react';
import { Mic, MicOff, Loader2, CheckCircle2, AlertCircle, Volume2, X, Wand2, ChevronRight } from '@/lib/icons';
import { apiFetch } from '@/lib/api';

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

interface VoiceProductInputProps {
  onDataExtracted: (data: ExtractedData) => void;
  onClose: () => void;
}

type Step = 'record' | 'processing' | 'review';

export default function VoiceProductInput({ onDataExtracted, onClose }: VoiceProductInputProps) {
  const [step, setStep] = useState<Step>('record');
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [interimTranscript, setInterimTranscript] = useState('');
  const [extractedData, setExtractedData] = useState<ExtractedData | null>(null);
  const [error, setError] = useState('');

  // Gap-filling state: which gaps are still open
  type GapType = 'colors' | 'fabric' | 'stock' | 'price';
  const [gaps, setGaps] = useState<GapType[]>([]);
  const [activeGap, setActiveGap] = useState<GapType | null>(null);

  const [tempColors, setTempColors] = useState<string[]>([]);
  const [tempColorInput, setTempColorInput] = useState('');
  const [tempFabric, setTempFabric] = useState<string | null>(null);
  const [stockValues, setStockValues] = useState<Record<string, Record<string, string>>>({});
  const [priceValue, setPriceValue] = useState('');

  const recognitionRef = useRef<any>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);

  const FABRIC_OPTIONS = ['Cotton', 'Polyester', 'Cotton-Poly Blend', 'Silk', 'Linen', 'Wool', 'Denim', 'Leather', 'Nylon', 'Spandex', 'Rayon', 'Jersey', 'Velvet', 'Lace', 'Other'];

  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        try { recognitionRef.current.abort(); } catch {}
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(t => t.stop());
      }
    };
  }, []);

  // Analyse what's missing from extracted data
  const computeGaps = useCallback((data: ExtractedData): GapType[] => {
    const missing: GapType[] = [];
    const hasColors = (data.colors && data.colors.length > 0) || (data.variants?.Color && data.variants.Color.length > 0);
    if (!hasColors) missing.push('colors');
    if (!data.fabric) missing.push('fabric');
    const hasStock = data.stock_hints && Object.keys(data.stock_hints).length > 0;
    if (!hasStock) missing.push('stock');
    if (!data.price && data.price !== 0) missing.push('price');
    return missing;
  }, []);

  const showNextGap = useCallback((remaining: GapType[]) => {
    if (remaining.length === 0) {
      // All gaps filled → auto-apply
      setActiveGap(null);
      setTimeout(() => {
        const data = extractedData || {};
        onDataExtracted({
          ...data,
          colors: data.colors?.length ? data.colors : tempColors.length ? tempColors : undefined,
          fabric: data.fabric || tempFabric,
          quantity: Object.values(stockValues).reduce((sum, sizes) =>
            sum + Object.values(sizes).reduce((s, v) => s + (parseInt(v) || 0), 0), 0) || data.quantity || undefined,
          price: priceValue ? parseFloat(priceValue) : data.price || undefined,
        });
        onClose();
      }, 300);
      return;
    }
    setGaps(remaining);
    setActiveGap(remaining[0]);
  }, [extractedData, tempColors, tempFabric, stockValues, priceValue, onDataExtracted, onClose]);

  // After extraction, compute gaps and start filling
  useEffect(() => {
    if (step === 'review' && extractedData) {
      const missing = computeGaps(extractedData);
      const hasColors = (extractedData.colors && extractedData.colors.length > 0) || (extractedData.variants?.Color && extractedData.variants.Color.length > 0);
      if (hasColors && extractedData.colors) {
        setTempColors(extractedData.colors);
      }
      if (extractedData.fabric) setTempFabric(extractedData.fabric);
      if (extractedData.price) setPriceValue(String(extractedData.price));
      if (extractedData.stock_hints) {
        const init: Record<string, Record<string, string>> = {};
        for (const [color, sizes] of Object.entries(extractedData.stock_hints)) {
          init[color] = {};
          for (const [size, qty] of Object.entries(sizes)) init[color][size] = String(qty || '');
        }
        setStockValues(init);
      }
      if (missing.length === 0) {
        // Everything provided → auto-apply
        const timer = setTimeout(() => {
          onDataExtracted(extractedData);
          onClose();
        }, 600);
        return () => clearTimeout(timer);
      }
      setGaps(missing);
      setActiveGap(missing[0]);
    }
  }, [step, extractedData, computeGaps, onDataExtracted, onClose]);

  const fillGapAndAdvance = (gap: GapType) => {
    const remaining = gaps.filter(g => g !== gap);
    setGaps(remaining);
    if (remaining.length === 0) {
      setActiveGap(null);
      // All gaps filled → auto-apply
      setTimeout(() => {
        const data = extractedData || {};
        onDataExtracted({
          ...data,
          colors: data.colors?.length ? data.colors : tempColors.length ? tempColors : undefined,
          fabric: data.fabric || tempFabric,
          quantity: Object.values(stockValues).reduce((sum, sizes) =>
            sum + Object.values(sizes).reduce((s, v) => s + (parseInt(v) || 0), 0), 0) || data.quantity || undefined,
          price: priceValue ? parseFloat(priceValue) : data.price || undefined,
        });
        onClose();
      }, 300);
    } else {
      setActiveGap(remaining[0]);
    }
  };

  const startRecording = useCallback(async () => {
    setError('');
    setTranscript('');
    setInterimTranscript('');
    setIsRecording(true);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];
      mediaRecorder.ondataavailable = (e) => { if (e.data.size > 0) audioChunksRef.current.push(e.data); };
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        await transcribeAudio(audioBlob);
      };
      mediaRecorder.start();

      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognitionRef.current = recognition;
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';
        recognition.onresult = (event: any) => {
          let final = '';
          let interim = '';
          for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) final += event.results[i][0].transcript;
            else interim += event.results[i][0].transcript;
          }
          if (final) setTranscript(prev => prev + ' ' + final);
          setInterimTranscript(interim);
        };
        recognition.onerror = () => {};
        recognition.start();
      }
    } catch {
      setError('Microphone access denied.');
      setIsRecording(false);
    }
  }, []);

  const stopRecording = useCallback(() => {
    setIsRecording(false);
    setInterimTranscript('');
    if (recognitionRef.current) { try { recognitionRef.current.stop(); } catch {} recognitionRef.current = null; }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') mediaRecorderRef.current.stop();
    if (streamRef.current) { streamRef.current.getTracks().forEach(t => t.stop()); streamRef.current = null; }
  }, []);

  const transcribeAudio = async (audioBlob: Blob) => {
    setStep('processing');
    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.webm');
      formData.append('language', 'en');
      const transcribeRes = await apiFetch('/supplier/upload/voice-transcribe', { method: 'POST', body: formData });
      const { transcript: fullTranscript } = await transcribeRes.json();
      const text = fullTranscript || transcript;
      setTranscript(text);

      const extractFormData = new FormData();
      extractFormData.append('transcript', text);
      const extractRes = await apiFetch('/supplier/upload/nlp-extract', { method: 'POST', body: extractFormData });
      const data: ExtractedData = await extractRes.json();
      setExtractedData(data);
      setStep('review');
    } catch {
      setError('AI processing failed. Please try again or enter details manually.');
      setStep('record');
    }
  };

  const colors = extractedData?.variants?.Color || extractedData?.colors || tempColors || [];
  const sizes = extractedData?.variants?.Size || extractedData?.variants?.size || ['S', 'M', 'L', 'XL'];
  const gapProgress = gaps.length > 0 ? `${gaps.indexOf(activeGap as GapType) + 1}/${gaps.length}` : '';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center theme-overlay" onClick={onClose} role="dialog" aria-modal="true" aria-label="Describe your product by voice">
      <div className="glass-panel relative w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto rounded-xl border shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between p-5 border-b border-border sticky top-0 bg-surface-1 z-10">
          <h2 className="text-lg font-semibold text-text">
            {activeGap ? 'Fill Missing Details' : 'Describe Your Product'}
          </h2>
          <div className="flex items-center gap-2">
            <div className="hidden sm:flex items-center gap-1.5 text-[11px]">
              <span className={`px-2 py-0.5 rounded-full ${step === 'record' ? 'bg-primary text-white' : step === 'processing' ? 'bg-amber/10 text-amber' : 'bg-success/10 text-success'}`}>
                {step === 'record' ? '1 Record' : step === 'processing' ? '2 Analyze' : '3 Done'}
              </span>
              {gapProgress && <span className="text-text-faint text-[10px]">Gaps {gapProgress}</span>}
            </div>
            <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-surface-2 text-text-muted hover:text-text transition-colors">
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {step === 'record' && (
          <div className="p-6 space-y-5">
            <div className="text-center py-8">
              {isRecording ? (
                <div className="animate-pulse">
                  <div className="w-20 h-20 rounded-full bg-danger/10 flex items-center justify-center mx-auto mb-4">
                    <Mic className="w-10 h-10 text-danger" />
                  </div>
                  <div className="flex items-center justify-center gap-2 mb-2">
                    <span className="w-2 h-2 rounded-full bg-danger animate-ping" />
                    <p className="text-sm font-medium text-text">Recording...</p>
                  </div>
                  {interimTranscript && <p className="text-xs text-text-faint italic mt-2">{interimTranscript}</p>}
                  <Button variant="danger" onClick={stopRecording}>
                    <MicOff className="w-4 h-4" /> Stop Recording
                  </Button>
                </div>
              ) : (
                <div>
                  <div className="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
                    <Mic className="w-10 h-10 text-primary" />
                  </div>
                  <p className="text-sm text-text-muted mb-2">Say something like:</p>
                  <p className="text-xs text-text-faint italic mb-4">
                    "A T-shirt, 4 colors: blue, yellow, black, white, print 'I love Oman'"
                  </p>
                  <button onClick={startRecording}
                    className="theme-btn-primary inline-flex items-center gap-2 px-6 py-3 shadow-lg text-sm font-medium">
                    <Mic className="w-5 h-5" /> Start Recording
                  </button>
                </div>
              )}
            </div>
            {error && (
              <div className="p-3 bg-danger/5 border border-danger/30 rounded-xl flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-danger mt-0.5 shrink-0" />
                <p className="text-xs text-danger">{error}</p>
              </div>
            )}
          </div>
        )}

        {step === 'processing' && (
          <div className="p-6 text-center py-12">
            <Loader2 className="w-10 h-10 text-primary animate-spin mx-auto mb-4" />
            <p className="text-sm font-medium text-text">AI is analyzing your voice...</p>
            <p className="text-xs text-text-faint mt-1">Extracting product details</p>
            {transcript && (
              <div className="mt-4 p-3 bg-surface-2 rounded-xl text-left">
                <p className="text-xs text-text-faint mb-1 font-medium">Transcript:</p>
                <p className="text-sm text-text-muted">{transcript}</p>
              </div>
            )}
          </div>
        )}

        {step === 'review' && extractedData && !activeGap && gaps.length === 0 && (
          <div className="p-5 space-y-4">
            <div className="p-3 bg-success/5 border border-success/30 rounded-xl flex items-start gap-2">
              <CheckCircle2 className="w-4 h-4 text-success mt-0.5 shrink-0" />
              <p className="text-xs text-success">Everything detected! Auto-applying...</p>
            </div>
            <div className="space-y-3">
              {extractedData.product_name && (
                <div><p className="text-xs font-medium text-text-faint">Product Name</p><p className="text-sm font-medium text-text">{extractedData.product_name}</p></div>
              )}
              {colors.length > 0 && (
                <div><p className="text-xs font-medium text-text-faint">Colors</p><div className="flex flex-wrap gap-1.5 mt-1">{colors.map(c => <span key={c} className="px-2.5 py-0.5 bg-primary/5 text-primary text-xs rounded-full border border-primary/20">{c}</span>)}</div></div>
              )}
              {extractedData.fabric && <div><p className="text-xs font-medium text-text-faint">Fabric</p><p className="text-sm text-text-muted">{extractedData.fabric}</p></div>}
              {extractedData.price && <div><p className="text-xs font-medium text-text-faint">Price</p><p className="text-sm text-text-muted">{extractedData.price} OMR</p></div>}
            </div>
          </div>
        )}

        {step === 'review' && activeGap === 'colors' && (
          <div className="p-5 space-y-4">
            <div className="p-3 bg-amber/5 border border-amber/20 rounded-xl">
              <p className="text-sm font-medium text-amber-800 mb-1">What colors is this product available in?</p>
              <p className="text-xs text-amber-600">We didn't detect colors from your recording. Add them below.</p>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {tempColors.map(c => (
                <span key={c} className="inline-flex items-center gap-1 px-2.5 py-1 bg-primary/5 text-primary text-xs rounded-full border border-primary/20">
                  {c}
                  <button onClick={() => setTempColors(prev => prev.filter(x => x !== c))} className="text-primary/60 hover:text-danger"><X className="w-2.5 h-2.5" /></button>
                </span>
              ))}
            </div>
            <div className="flex gap-2">
              <input type="text" value={tempColorInput} onChange={(e) => setTempColorInput(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter' && tempColorInput.trim()) { setTempColors(prev => [...prev, tempColorInput.trim()]); setTempColorInput(''); } }}
                placeholder="Type a color and press Enter" className="theme-input flex-1 text-sm" />
              <button onClick={() => { if (tempColorInput.trim()) { setTempColors(prev => [...prev, tempColorInput.trim()]); setTempColorInput(''); } }}
                className="theme-btn-primary px-3 py-2 text-sm">Add</button>
            </div>
            <div className="flex flex-wrap gap-1">
              {['Black', 'White', 'Red', 'Blue', 'Green', 'Yellow', 'Orange', 'Purple', 'Pink', 'Brown', 'Grey', 'Navy', 'Beige', 'Gold', 'Silver'].filter(c => !tempColors.includes(c)).slice(0, 8).map(c => (
                <button key={c} onClick={() => setTempColors(prev => [...prev, c])}
                  className="px-2 py-1 rounded bg-surface-2 text-text-muted text-xs border border-border/40 hover:bg-primary/5 hover:text-primary hover:border-primary/30 transition-all">+{c}</button>
              ))}
            </div>
            <button onClick={() => fillGapAndAdvance('colors')}
              className="w-full theme-btn-primary py-2.5 text-sm font-medium">
              {gaps.length > 1 ? `Next → (${gaps.indexOf('colors') + 1}/${gaps.length})` : 'Continue'}
            </button>
          </div>
        )}

        {step === 'review' && activeGap === 'fabric' && (
          <div className="p-5 space-y-4">
            <div className="p-3 bg-amber/5 border border-amber/20 rounded-xl">
              <p className="text-sm font-medium text-amber-800 mb-1">What fabric/material is this made of?</p>
              <p className="text-xs text-amber-600">Tap to select, or type a custom material.</p>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {FABRIC_OPTIONS.map(f => (
                <button key={f} onClick={() => setTempFabric(tempFabric === f ? null : f)}
                  className={`px-3 py-1.5 text-xs rounded-lg border transition-all ${
                    tempFabric === f ? 'bg-primary text-white border-primary shadow-sm' : 'bg-surface-2 text-text-muted border-border/40 hover:border-primary/30 hover:text-primary'
                  }`}>{f}</button>
              ))}
            </div>
            {tempFabric && <p className="text-xs text-text-muted">Selected: <strong>{tempFabric}</strong></p>}
            <button onClick={() => fillGapAndAdvance('fabric')}
              className="w-full theme-btn-primary py-2.5 text-sm font-medium">
              {tempFabric ? `Use ${tempFabric}` : 'Skip'} {gaps.length > 1 ? `→ (${gaps.indexOf('fabric') + 1}/${gaps.length})` : ''}
            </button>
          </div>
        )}

        {step === 'review' && activeGap === 'stock' && (
          <div className="p-5 space-y-4">
            <div className="p-3 bg-amber/5 border border-amber/20 rounded-xl">
              <p className="text-sm font-medium text-amber-800 mb-1">Enter Stock Quantities</p>
              <p className="text-xs text-amber-600">Fill in available stock for each variant.</p>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left py-2 pr-3 font-medium text-text-faint">Color</th>
                    {sizes.map(s => <th key={s} className="py-2 px-2 font-medium text-text-faint text-center">{s}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {(colors.length ? colors : ['Default']).map(color => (
                    <tr key={color} className="border-b border-border/50">
                      <td className="py-2 pr-3 font-medium text-text-muted">{color}</td>
                      {sizes.map(size => (
                        <td key={`${color}-${size}`} className="py-1 px-1">
                          <input type="number" min="0" placeholder="0"
                            value={stockValues[color]?.[size] ?? ''}
                            onChange={(e) => setStockValues(prev => ({ ...prev, [color]: { ...(prev[color] || {}), [size]: e.target.value } }))}
                            className="theme-input w-full px-2 py-1.5 text-center text-xs" />
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <button onClick={() => fillGapAndAdvance('stock')}
              className="w-full theme-btn-primary py-2.5 text-sm font-medium">
              {gaps.length > 1 ? `Next → (${gaps.indexOf('stock') + 1}/${gaps.length})` : 'Continue'}
            </button>
          </div>
        )}

        {step === 'review' && activeGap === 'price' && (
          <div className="p-5 space-y-4">
            <div className="p-3 bg-amber/5 border border-amber/20 rounded-xl">
              <p className="text-sm font-medium text-amber-800 mb-1">Set Price</p>
              <p className="text-xs text-amber-600">Enter the selling price for this product.</p>
            </div>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-text-faint">OMR</span>
              <input type="number" step="0.001" min="0" placeholder="0.000"
                value={priceValue} onChange={(e) => setPriceValue(e.target.value)}
                className="theme-input w-full pl-14 pr-4 py-2.5 text-sm" />
            </div>
            <button onClick={() => fillGapAndAdvance('price')}
              className="w-full theme-btn-primary py-2.5 text-sm font-medium">
              {priceValue ? 'Confirm & Apply' : 'Skip (set later)'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
