"use client";

import { Button } from "@/components/ui/Button";

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useUploadOrchestrator } from '@/lib/uploadOrchestrator';
import { useBgABTest } from '@/lib/useBgABTest';
import { useBgRecommendations } from '@/lib/useBgRecommendations';
import BgStrategyOnboardingTooltip from '@/components/supplier/BgStrategyOnboardingTooltip';
import ProcessingModal from '@/components/supplier/ProcessingModal';
import AIResultsModal from '@/components/supplier/AIResultsModal';
import QuantityModal from '@/components/supplier/QuantityModal';
import VerifyPublishModal from '@/components/supplier/VerifyPublishModal';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import SupplierLayout from '@/components/SupplierLayout';
import { PanelContent, PanelHero } from '@/components/PanelPage';
import { apiFetch } from '@/lib/api';
import { useCurrencyStore } from '@/lib/currencyStore';
import { getSuggestedVariants } from '@/lib/variantConfig';
import { resolveCategorySlug, getMatrixAxes, getSpecGroupsForCategory } from '@/lib/categoryVariantBridge';
import SmartMediaUpload from '@/components/supplier/SmartMediaUpload';
import VoiceProductInput from '@/components/supplier/VoiceProductInput';
import VoiceToCatalogPipeline from '@/components/supplier/VoiceToCatalogPipeline';
import VerificationPopup from '@/components/supplier/VerificationPopup';
import SmartVariantMatrix from '@/components/supplier/SmartVariantMatrix';
import SmartPricingPanel from '@/components/supplier/SmartPricingPanel';
import ProductSpecsSelector from '@/components/supplier/ProductSpecsSelector';
import ProductPublishSuccess from '@/components/supplier/ProductPublishSuccess';
import PhotoEditorModal from '@/components/supplier/PhotoEditorModal';
import {
  ArrowLeft, Package, Upload, X, ImageIcon, DollarSign,
  Eye, Sparkles, Layers, RefreshCw, Mic, MicOff, Wand2,
  Zap, Tag, Camera, CheckCircle2, Volume2,
  Crop, Film, Video, VideoOff, Maximize2,
  RotateCw, RotateCcw, Square, Sun, Moon, Shirt, Shield, Award,
  ListChecks, Grid2x2, Plus, Trash2,
  Gauge, Globe, Loader2, PenLine, Save, Edit3,
  Check, ChevronDown, ChevronRight, BadgeCheck, TrendingUp, AlertCircle,
  BarChart3, Home, Star, Info,
} from '@/lib/icons';

/* ════════════════════════ Types ════════════════════════ */

interface AiResult {
  product_name_hint?: string;
  suggested_category?: string;
  suggested_subcategory?: string;
  suggested_brand?: string;
  detected_attributes?: { color?: string[]; material?: string[]; brand?: string; condition?: string; style?: string; product_type?: string; [k: string]: unknown };
  suggested_variants?: string[];
  variant_options?: Record<string, string[]>;
  product_description?: string;
  suggested_tags?: string[];
  product_type?: string;
  ai_suggested_price?: number;
  price_min?: number;
  price_max?: number;
  stock_hints?: Record<string, Record<string, number>>;
  variant_labels?: Record<string, string>;
  english_title?: string;
  english_description?: string;
  arabic_title?: string;
  arabic_description?: string;
  bullet_points_en?: string[];
  bullet_points_ar?: string[];
  source?: string;
  photo_analysis?: {
    dominant_colors?: string[];
    background?: string;
    bg_complexity?: number;
    suggested_bg_preset?: string | null;
  };
  copy_job_id?: string;
  ai_status?: 'ai_active' | 'heuristic_fallback';
}

interface AiCopyJob {
  job_id: string;
  status: 'pending' | 'done' | 'error';
  result?: AiResult | null;
  error?: string | null;
}

interface VoiceData {
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

/* ════════════════════════ Constants ════════════════════════ */

// Six tested background-removal pipelines (br_05..br_13) implemented as
// lightweight VPS-safe strategies in backend/services/bg_removal_service.py.
const BG_MODELS = [
  { key: 'clean_commercial', label: 'Clean · br05', icon: Wand2, bestFor: ['clothing'] as string[], tooltip: 'Recommended for clothing & textiles. Clean, artifact-free edges with 39% foreground coverage.' },
  { key: 'precision_geometry', label: 'Geometry · br06', icon: Layers, bestFor: ['electronics', 'beauty'] as string[], tooltip: 'Recommended for electronics & beauty. Precision geometry preserves fine details with zero artifacts.' },
  { key: 'birefnet_production', label: 'Production · br08', icon: Zap, bestFor: [] as string[], tooltip: 'Highest alpha confidence (1.0). Best for complex backgrounds and wood textures.' },
  { key: 'ultimate_gaps', label: 'Gaps · br11', icon: Sparkles, bestFor: [] as string[], tooltip: 'Fast all-rounder (2.6s). Best for unknown product types or textured backgrounds.' },
  { key: 'marketing_variants', label: 'Marketing · br12', icon: Tag, bestFor: [] as string[], tooltip: 'Aggressive artifact & floating-object removal. Best for clean marketing shots.' },
  { key: 'lite_variants', label: 'Lite · br13', icon: Camera, bestFor: [] as string[], tooltip: 'Smallest memory footprint. Best for low-RAM VPS or batch processing.' },
];

const IMAGE_TOOLS = [
  { key: 'process_magic_erase', label: 'Magic Erase' },
  { key: 'process_smart_crop', label: 'Smart Crop' },
  { key: 'process_rotate', label: 'Auto-Rotate' },
  { key: 'process_auto_light', label: 'Auto Light' },
  { key: 'process_white_balance', label: 'White Balance' },
  { key: 'process_color_enhance', label: 'Color Boost' },
  { key: 'process_denoise', label: 'Denoise' },
  { key: 'process_sharpen', label: 'Sharpen' },
  { key: 'process_auto_levels', label: 'Auto Tone' },
  { key: 'process_upscale', label: 'HD Upscale' },
  { key: 'process_compress', label: 'Compress' },
  { key: 'process_webp_convert', label: 'WebP' },
];

const CATEGORIES = ['Electronics', 'Clothing', 'Home & Garden', 'Sports & Outdoors', 'Books', 'Beauty & Personal Care', 'Toys & Games', 'Automotive', 'Health & Household', 'Industrial & Scientific', 'Other'];

const titleCase = (s: string) => s.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

/* ══════════════════════════ Component ══════════════════════════ */

export default function AddProduct() {
  const router = useRouter();
  const formatMoney = useCurrencyStore((s) => s.format);

  // ── Media ──────────────────────────────────────────────
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  // Mirror of selectedImage kept in a ref so async callbacks (e.g. the
  // auto-trigger setTimeout after upload) always read the freshest file
  // instead of a stale closure value that captured `null`.
  const selectedImageRef = useRef<File | null>(null);
  const setSelectedImageSafe = (f: File | null) => { selectedImageRef.current = f; setSelectedImage(f); };
  // Tracks whether the variant matrix was opened by AI fill, so async callbacks
  // (e.g. the copy-job poll) can avoid auto-opening the pricing panel on top of it.
  const matrixOpenedRef = useRef(false);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [originalPreviewUrl, setOriginalPreviewUrl] = useState<string | null>(null);
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [videoPreviewUrl, setVideoPreviewUrl] = useState<string | null>(null);
  const [videoLink, setVideoLink] = useState('');
  const [dragOver, setDragOver] = useState(false);
  const [cameraActive, setCameraActive] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // ── Canvas state ───────────────────────────────────────
  const [canvasZoom, setCanvasZoom] = useState(1);
  const [canvasRotate, setCanvasRotate] = useState(0);
  const [canvasPan, setCanvasPan] = useState({ x: 0, y: 0 });
  const [canvasBg, setCanvasBg] = useState<'transparent' | 'white' | 'black'>('transparent');
  const [showGrid, setShowGrid] = useState(false);
  const [activeTab, setActiveTab] = useState<'photo' | 'video'>('photo');
  const isPanning = useRef(false);
  const panStart = useRef({ x: 0, y: 0, panX: 0, panY: 0 });

  // ── Video recording ────────────────────────────────────
  const [videoRecording, setVideoRecording] = useState(false);
  const videoCamRef = useRef<HTMLVideoElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const recordChunksRef = useRef<Blob[]>([]);
  const videoStreamRef = useRef<MediaStream | null>(null);

  // ── Form (supplier only enters price + stock; AI fills the rest) ──
  const [formData, setFormData] = useState({
    name: '', description: '', price: '', stock_quantity: '',
    category: '', subcategory: '', brand: '', tags: '', color: '',
    is_active: true,
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [createMore, setCreateMore] = useState(false);

  // ── BG A/B Test (auto-select best strategy) ──────────
  const {
    runABTest,
    applyWinnerBg,
    testing: abTesting,
    lastResult: abTestResult,
    error: abTestError,
  } = useBgABTest();

  // ── BG Recommendations (metrics-driven per-category scores) ──
  const {
    recommendations,
    loading: recsLoading,
    getStrategyMetrics,
    getRecommendedStrategy,
  } = useBgRecommendations();

  // ── BG Onboarding / Why-this UI state ─────────────────────
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [showWhyThis, setShowWhyThis] = useState(false);
  const [autoSelectedWinner, setAutoSelectedWinner] = useState<string | null>(null);

  // ── AI Auto-fill ───────────────────────────────────────
  const [aiLoading, setAiLoading] = useState(false);
  const [aiNote, setAiNote] = useState('');
  const [aiFilled, setAiFilled] = useState(false);
  const [photoAnalysis, setPhotoAnalysis] = useState<AiResult['photo_analysis'] | null>(null);
  const [aiPriceRange, setAiPriceRange] = useState<{ min: number; max: number } | null>(null);

  // ── Variants (auto-detected by AI) ─────────────────────
  const [variantTypes, setVariantTypes] = useState<string[]>([]);
  const [variantOptions, setVariantOptions] = useState<Record<string, string[]>>({});
  const [variantLabels, setVariantLabels] = useState<Record<string, string>>({});
  const [variantsEnabled, setVariantsEnabled] = useState(false);
  const [variantStockMode, setVariantStockMode] = useState<'single' | 'matrix'>('single');
  const [singleStock, setSingleStock] = useState('');
  const [variantValues, setVariantValues] = useState<Record<string, { stock: string; price: string }>>({});
  const [newOption, setNewOption] = useState<Record<string, string>>({});
  const [matrixValues, setMatrixValues] = useState<Record<string, Record<string, { stock: string; price: string; sku: string }>>>({});

  // ── Background removal (canvas tool) ───────────────────
  const [processedImageBlob, setProcessedImageBlob] = useState<Blob | null>(null);
  const [processedImageUrl, setProcessedImageUrl] = useState<string | null>(null);
  const [activeBgPreset, setActiveBgPreset] = useState<string | null>(null);
  const [activeBgModel, setActiveBgModel] = useState<string | null>(null);
  const [bgLoading, setBgLoading] = useState<string | null>(null);
  const [fastMode, setFastMode] = useState(true); // low-RAM VPS mode

  // ── Image tools (canvas toolbar toggles) ───────────────
  const [imageToolToggles, setImageToolToggles] = useState<Record<string, boolean>>({
    process_magic_erase: false, process_smart_crop: false, process_rotate: false,
    process_auto_light: false, process_white_balance: false, process_color_enhance: false,
    process_denoise: false, process_sharpen: false, process_auto_levels: false,
    process_upscale: false, process_compress: false, process_webp_convert: false,
  });
  const toggleTool = (key: string) => setImageToolToggles((p) => ({ ...p, [key]: !p[key] }));

  // ── Voice ──────────────────────────────────────────────
  const [listeningFor, setListeningFor] = useState<null | 'name' | 'description' | 'price' | 'stock' | 'command'>(null);
  const recognitionRef = useRef<any>(null);
  const [voiceFeedback, setVoiceFeedback] = useState('');
  const [audioGuidance, setAudioGuidance] = useState(false);

  // ── Draft ──────────────────────────────────────────────
  const DRAFT_KEY = 'zozi_canvas_product_draft_v2';
  const [draftSavedAt, setDraftSavedAt] = useState<string | null>(null);
  const [showDraftRestore, setShowDraftRestore] = useState(false);
  const [pendingDraft, setPendingDraft] = useState<any>(null);

  // ── Canvas studio state ────────────────────────────────

  // ── Angle generation ───────────────────────────────────
  const [angleUrls, setAngleUrls] = useState<string[]>([]);
  const [genAnglesLoading, setGenAnglesLoading] = useState(false);

  // ── Language ───────────────────────────────────────────
  const [langTab, setLangTab] = useState<'en' | 'ar'>('en');
  const [nameAr, setNameAr] = useState('');
  const [descriptionAr, setDescriptionAr] = useState('');
  const [translating, setTranslating] = useState(false);

  // ── Upload orchestrator (5-step modal flow) ────────────
  const {
    state: uploadState,
    setImage: orchestratorSetImage,
    updateField,
    setQuantityForColor,
    advanceColor: advanceColorStep,
    goToPhotoEdit,
    goToAiResults,
    goToQuantity,
    goToVerify,
    reset,
  } = useUploadOrchestrator();

  // ── New flow orchestration ─────────────────────────────
  const [showMediaUpload, setShowMediaUpload] = useState(false);
  const [showActionPicker, setShowActionPicker] = useState(false);
  const [showVoiceInput, setShowVoiceInput] = useState(false);
  const [showVerification, setShowVerification] = useState(false);
  const [showVariantMatrix, setShowVariantMatrix] = useState(false);
  const [showSpecsSelector, setShowSpecsSelector] = useState(false);
  const [selectedSpecs, setSelectedSpecs] = useState<Record<string, string[]>>({});
  const [specGroups, setSpecGroups] = useState<{ key: string; label: string; options: { id: string; label: string }[] }[]>([]);
  const [showSuccess, setShowSuccess] = useState(false);
  const [uploadedImages, setUploadedImages] = useState<File[]>([]);
  const [voiceExtractedData, setVoiceExtractedData] = useState<VoiceData | null>(null);
  const [publishResult, setPublishResult] = useState<{ id: number; name: string } | null>(null);
  const [showPricingPanel, setShowPricingPanel] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [showPhotoEditor, setShowPhotoEditor] = useState(false);
  const [magicEditImage, setMagicEditImage] = useState<string | null>(null);
  const [listingCountries, setListingCountries] = useState<string[]>(['Oman']);
  const [listingScore, setListingScore] = useState(95);

  /* ════════════════════════ Canvas Drawing ═══════════════════════════ */

  const drawCanvasRef = useRef<HTMLCanvasElement>(null);

  const drawScene = useCallback(() => {
    const c = drawCanvasRef.current;
    if (!c || !imagePreview) return;
    const img = new Image();
    img.onload = () => {
      const ctx = c.getContext('2d');
      if (!ctx) return;
      const parent = c.parentElement;
      const maxW = parent ? parent.clientWidth : 600;
      const w = Math.min(600, Math.max(320, maxW - 16));
      const h = Math.round(w * 2 / 3);
      const dpr = window.devicePixelRatio || 1;
      c.width = w * dpr; c.height = h * dpr;
      c.style.width = `${w}px`; c.style.height = `${h}px`;
      ctx.scale(dpr, dpr);

      if (canvasBg === 'white') { ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, w, h); }
      else if (canvasBg === 'black') { ctx.fillStyle = '#000'; ctx.fillRect(0, 0, w, h); }
      else {
        ctx.fillStyle = '#ccc'; ctx.fillRect(0, 0, w, h);
        ctx.fillStyle = '#fff';
        const step = 10;
        for (let y = 0; y < h; y += step) for (let x = 0; x < w; x += step)
          if ((Math.floor(x / step) + Math.floor(y / step)) % 2 === 0) ctx.fillRect(x, y, step, step);
      }

      if (showGrid) {
        ctx.strokeStyle = 'rgba(255,255,255,0.4)'; ctx.lineWidth = 1;
        for (let i = 1; i < 3; i++) {
          const x = (w / 3) * i; ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke();
          const y = (h / 3) * i; ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
        }
      }

      const rad = (canvasRotate * Math.PI) / 180;
      const fitScale = Math.min((w * 0.8) / img.naturalWidth, (h * 0.8) / img.naturalHeight);
      const dw = img.naturalWidth * fitScale * canvasZoom;
      const dh = img.naturalHeight * fitScale * canvasZoom;
      ctx.save();
      ctx.translate(w / 2 + canvasPan.x, h / 2 + canvasPan.y);
      ctx.rotate(rad);
      ctx.drawImage(img, -dw / 2, -dh / 2, dw, dh);
      ctx.restore();
      ctx.strokeStyle = 'rgba(0,0,0,0.08)'; ctx.lineWidth = 1;
      ctx.strokeRect(0, 0, w, h);
    };
    img.src = imagePreview;
  }, [imagePreview, canvasZoom, canvasRotate, canvasPan, canvasBg, showGrid]);

  useEffect(() => { drawScene(); }, [drawScene]);

  /* ════════════════════════ Category Baseline ═══════════════════════════ */

  // Seed the variant matrix + spec groups from the config the instant a category
  // is known — runs in parallel with the AI analyze so the supplier sees the
  // right axes immediately instead of waiting for (or depending on) the AI.
  // AI results later override these defaults.
  const applyCategoryBaseline = useCallback((category: string) => {
    if (!category) return;
    const { colors, sizes } = getMatrixAxes(category);
    const axes = getSuggestedVariants(resolveCategorySlug(category)).map((v) => v.key);
    setVariantTypes(axes);
    setVariantOptions((prev) => ({ ...prev, color: colors, size: sizes }));
    setSpecGroups(getSpecGroupsForCategory(category));
    // Pre-seed a matrix so the grid is ready the moment the modal opens.
    setMatrixValues((prev) => {
      if (prev && Object.keys(prev).length > 0) return prev;
      const seeded: Record<string, Record<string, { stock: string; price: string; sku: string }>> = {};
      colors.forEach((c) => {
        seeded[c] = {};
        sizes.forEach((s) => {
          const def = s === 'S' ? 50 : s === 'M' ? 100 : s === 'L' ? 100 : s === 'XL' ? 25 : s === 'XXL' ? 15 : s === 'XS' ? 30 : 50;
          seeded[c][s] = { stock: String(def), price: '', sku: '' };
        });
      });
      return seeded;
    });
  }, []);

  /* ════════════════════════ Media Handlers ═══════════════════════════ */

  const MAX_IMAGE_SIZE = 5 * 1024 * 1024;
  const MAX_VIDEO_SIZE = 25 * 1024 * 1024;

  const processUploadedFile = (file: File) => {
    setError('');
    if (!['image/jpeg', 'image/png', 'image/webp', 'image/gif'].includes(file.type)) {
      setError('Only JPG, PNG, WebP, GIF supported.'); return;
    }
    if (file.size > MAX_IMAGE_SIZE) { setError('Image must be under 5MB.'); return; }
    setSelectedImageSafe(file);
    if (processedImageUrl) URL.revokeObjectURL(processedImageUrl);
    setProcessedImageBlob(null); setProcessedImageUrl(null);
    setActiveBgPreset(null); setActiveBgModel(null);
    const reader = new FileReader();
    reader.onload = (ev) => {
      const url = ev.target?.result as string;
      setImagePreview(url); setOriginalPreviewUrl(url);
      setAiNote('Photo ready. AI analyzing…');
      speakGuidance('Photo uploaded. AI is analyzing your product.');
      setShowMediaUpload(false);
      // Show onboarding tooltip on first upload
      try {
        const seen = localStorage.getItem('zozi_bg_onboarding_seen');
        if (!seen) {
          setShowOnboarding(true);
          localStorage.setItem('zozi_bg_onboarding_seen', '1');
        }
      } catch { }
      // Send to orchestrator for parallel BG removal + AI analysis
      orchestratorSetImage(file, url);
      // Auto-run A/B test across 6 BG strategies and apply the winner
      runABTest(file, formData.category || undefined).then((winner) => {
        if (winner) {
          setAutoSelectedWinner(winner);
          setShowWhyThis(true);
          setBgLoading(winner);
          applyWinnerBg(file, winner)
            .then((blob) => {
              if (blob) {
                const blobUrl = URL.createObjectURL(blob);
                // Use ref for processedImageUrl to avoid stale closure
                if (selectedImageRef.current) {
                  setProcessedImageBlob(blob);
                  setProcessedImageUrl(blobUrl);
                  setActiveBgModel(winner);
                  setImagePreview(blobUrl);
                  setAiNote(`✨ Auto-selected BG strategy: ${winner.replace(/_/g, ' ')}`);
                }
              }
            })
            .catch(() => {
              setAiNote('⚠️ BG A/B test completed but auto-apply failed. Try manual BG selection.');
            })
            .finally(() => setBgLoading(null));
        }
      });
    };
    reader.readAsDataURL(file);
  };

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) processUploadedFile(file);
  };

  const handleSmartImages = (files: File[]) => {
    setUploadedImages(prev => [...prev, ...files]);
    const firstImg = files.find(f => f.type.startsWith('image/'));
    if (firstImg) processUploadedFile(firstImg);
  };

  const handleVoiceData = (data: VoiceData) => {
    setVoiceExtractedData(data);
    setShowVoiceInput(false);
    if (data) {
      const colors = data.colors || [];
      setFormData(prev => ({
        ...prev,
        name: data.product_name || prev.name,
        category: data.category || prev.category,
        subcategory: data.subcategory || prev.subcategory,
        description: data.description || prev.description,
        tags: data.suggested_tags?.join(', ') || prev.tags,
        color: colors.join(', ') || prev.color,
        price: data.price ? String(data.price) : prev.price,
      }));
      // Build variants from extracted data (normalize Color/Size keys).
      const variantMap: Record<string, string[]> = {};
      if (data.variants) {
        for (const [k, v] of Object.entries(data.variants)) {
          if (Array.isArray(v) && v.length) variantMap[k.toLowerCase()] = v;
        }
      }
      if (colors.length) variantMap['color'] = colors;
      if (variantMap['size'] || variantMap['sizes']) variantMap['size'] = variantMap['size'] || variantMap['sizes'] || ['S', 'M', 'L', 'XL'];
      delete variantMap['sizes'];
      if (Object.keys(variantMap).length) {
        const types = Object.keys(variantMap);
        setVariantTypes(types);
        setVariantOptions(variantMap);
        setVariantsEnabled(true);
        // Seed matrix stock from stock_hints.
        const seeded: Record<string, Record<string, { stock: string; price: string; sku: string }>> = {};
        const colorsList = variantMap['color'] || [''];
        const sizesList = variantMap['size'] || [''];
        colorsList.forEach((c) => {
          seeded[c] = {};
          sizesList.forEach((s) => {
            const hint = data.stock_hints?.[c]?.[s] ?? data.stock_hints?.[c]?.[s.toUpperCase()] ?? 0;
            seeded[c][s] = { stock: hint ? String(hint) : '', price: data.price ? String(data.price) : '', sku: '' };
          });
        });
        setMatrixValues(seeded);
      }
      if (data.quantity) setFormData(prev => ({ ...prev, stock_quantity: String(data.quantity) }));
      if (data.price) setFormData(prev => ({ ...prev, price: String(data.price) }));
      setAiFilled(true);
      setAiNote('Voice details applied. Review stock matrix before publishing.');
    }
    // Unified downstream flow: open the variant matrix (same as the photo path).
    if (variantsEnabled) {
      setShowVariantMatrix(true);
    } else {
      setShowSpecsSelector(true);
    }
  };

  const handleManualEntry = () => {
    setShowMediaUpload(false);
    setShowActionPicker(false);
  };

  const handleDragOver = (e: React.DragEvent) => { e.preventDefault(); setDragOver(true); };
  const handleDragLeave = () => setDragOver(false);
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault(); setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) processUploadedFile(file);
  };

  const removeImage = () => {
    setSelectedImageSafe(null);
    if (processedImageUrl) URL.revokeObjectURL(processedImageUrl);
    setProcessedImageBlob(null); setProcessedImageUrl(null);
    setActiveBgPreset(null); setActiveBgModel(null);
    setImagePreview(null); setOriginalPreviewUrl(null);
    setAngleUrls([]); setAiFilled(false); setAiNote('');
    setShowActionPicker(false);
  };

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
      setCameraActive(true);
      setTimeout(() => { if (videoRef.current) videoRef.current.srcObject = stream; }, 100);
    } catch { setError('Camera not available.'); }
  };
  const stopCamera = () => {
    if (videoRef.current?.srcObject) (videoRef.current.srcObject as MediaStream).getTracks().forEach((t) => t.stop());
    videoRef.current!.srcObject = null; setCameraActive(false);
  };
  const capturePhoto = () => {
    const video = videoRef.current; const can = canvasRef.current;
    if (!video || !can) return;
    can.width = video.videoWidth; can.height = video.videoHeight;
    can.getContext('2d')!.drawImage(video, 0, 0);
    can.toBlob((blob) => {
      if (!blob) return;
      stopCamera();
      processUploadedFile(new File([blob], `camera_${Date.now()}.jpg`, { type: 'image/jpeg' }));
    }, 'image/jpeg', 0.9);
  };

  // ── Video ──────────────────────────────────────────────
  const setVideoFromFile = (file: File) => {
    if (!['video/mp4', 'video/webm'].includes(file.type)) { setError('MP4 or WebM only.'); return; }
    if (file.size > MAX_VIDEO_SIZE) { setError('Video max 25MB.'); return; }
    if (videoPreviewUrl) URL.revokeObjectURL(videoPreviewUrl);
    setVideoFile(file); setVideoPreviewUrl(URL.createObjectURL(file)); setVideoLink('');
  };
  const handleVideoFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]; if (file) setVideoFromFile(file);
  };
  const removeVideo = () => {
    if (videoPreviewUrl) URL.revokeObjectURL(videoPreviewUrl);
    setVideoFile(null); setVideoPreviewUrl(null); setVideoLink('');
  };

  const startVideoRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' }, audio: true });
      videoStreamRef.current = stream; recordChunksRef.current = [];
      const mime = MediaRecorder.isTypeSupported('video/webm;codecs=vp9') ? 'video/webm;codecs=vp9' : 'video/webm';
      const recorder = new MediaRecorder(stream, { mimeType: mime });
      mediaRecorderRef.current = recorder;
      recorder.ondataavailable = (ev) => { if (ev.data.size > 0) recordChunksRef.current.push(ev.data); };
      recorder.onstop = () => {
        const blob = new Blob(recordChunksRef.current, { type: 'video/webm' });
        stream.getTracks().forEach((t) => t.stop()); videoStreamRef.current = null;
        if (videoCamRef.current) videoCamRef.current.srcObject = null;
        setVideoRecording(false);
        setVideoFromFile(new File([blob], `product_video_${Date.now()}.webm`, { type: 'video/webm' }));
      };
      setVideoRecording(true);
      setTimeout(() => { if (videoCamRef.current) videoCamRef.current.srcObject = stream; }, 100);
      recorder.start();
    } catch { setError('Camera/mic not available.'); }
  };
  const stopVideoRecording = () => mediaRecorderRef.current?.stop();
  const cancelVideoRecording = () => {
    mediaRecorderRef.current = null; recordChunksRef.current = [];
    videoStreamRef.current?.getTracks().forEach((t) => t.stop());
    videoStreamRef.current = null; if (videoCamRef.current) videoCamRef.current.srcObject = null;
    setVideoRecording(false);
  };

  /* ════════════════════════ Canvas Controls ═══════════════════════════ */

  const onCanvasPointerDown = (e: React.PointerEvent) => {
    isPanning.current = true;
    panStart.current = { x: e.clientX, y: e.clientY, panX: canvasPan.x, panY: canvasPan.y };
  };
  const onCanvasPointerMove = (e: React.PointerEvent) => {
    if (!isPanning.current) return;
    setCanvasPan({ x: panStart.current.panX + (e.clientX - panStart.current.x), y: panStart.current.panY + (e.clientY - panStart.current.y) });
  };
  const onCanvasPointerUp = () => { isPanning.current = false; };
  const onCanvasWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    setCanvasZoom((z) => Math.max(0.1, Math.min(5, z - e.deltaY * 0.001)));
  };

  /* ════════════════════════ AI Auto-Fill ═══════════════════════════ */

  const currentImageFile = (): File | null => {
    if (processedImageBlob) return new File([processedImageBlob], 'product.png', { type: 'image/png' });
    return selectedImageRef.current;
  };

  const handleAiFill = async () => {
    const img = currentImageFile();
    if (!img) { setAiNote('Upload a photo first.'); return; }
    setAiLoading(true); setError('');
    try {
      const fd = new FormData();
      fd.append('image', img);
      const res = await apiFetch('/supplier/upload/ai-analyze', { method: 'POST', body: fd, skipAuthRedirect: true });
      if (!res.ok) throw new Error('AI analysis failed');
      const data: AiResult = await res.json();
      let filled = 0;

      if (data.product_name_hint) { setFormData((f) => ({ ...f, name: data.product_name_hint as string })); filled++; }
      if (data.suggested_category) {
        const cats = CATEGORIES;
        const match = cats.find((c) => c.toLowerCase() === (data.suggested_category || '').toLowerCase())
          || cats.find((c) => c.toLowerCase().includes((data.suggested_category || '').toLowerCase()))
          || 'Other';
        setFormData((f) => ({ ...f, category: match })); filled++;
        // Seed variant axes from the config in parallel with AI (AI overrides later).
        applyCategoryBaseline(match);
      }
      if (data.suggested_subcategory) { setFormData((f) => ({ ...f, subcategory: data.suggested_subcategory as string })); filled++; }
      const brand = data.suggested_brand || data.detected_attributes?.brand;
      if (brand) { setFormData((f) => ({ ...f, brand: brand as string })); filled++; }
      if (data.product_description) { setFormData((f) => ({ ...f, description: data.product_description as string })); filled++; }
      if (data.suggested_tags?.length) { setFormData((f) => ({ ...f, tags: (data.suggested_tags as string[]).join(', ') })); filled++; }
      if (data.ai_suggested_price) {
        setFormData((f) => {
          if (!f.price && data.ai_suggested_price) {
            if (data.price_min && data.price_max) setAiPriceRange({ min: data.price_min, max: data.price_max });
            return { ...f, price: String(data.ai_suggested_price) };
          }
          return f;
        });
        if (!formData.price) filled++;
      }
      const colors = data.detected_attributes?.color;
      if (colors?.length) { setFormData((f) => ({ ...f, color: colors.join(', ') })); filled++; }

      if (data.photo_analysis) setPhotoAnalysis(data.photo_analysis);

      const suggested = (data.suggested_variants || []).filter(Boolean);
      if (suggested.length) {
        const labels = { ...variantLabels };
        const incoming = (data.variant_labels || {}) as Record<string, string>;
        suggested.forEach((t) => { if (incoming[t]) labels[t] = incoming[t]; });
        setVariantLabels(labels); setVariantTypes(suggested);
        const opts: Record<string, string[]> = {};
        suggested.forEach((t) => { opts[t] = (data.variant_options?.[t] || []).filter(Boolean); });
        setVariantOptions(opts); setVariantValues({}); setVariantsEnabled(true);
        filled++;
        // Seed a color×size matrix from any AI stock hints so the bulk entry
        // grid opens with smart defaults already in place.
        const colorsList = opts['color'] || ['Default'];
        const sizesList = opts['size'] || ['One Size'];
        const seeded: Record<string, Record<string, { stock: string; price: string; sku: string }>> = {};
        colorsList.forEach((c) => {
          seeded[c] = {};
          sizesList.forEach((s) => {
            const hint = data.stock_hints?.[c]?.[s] ?? data.stock_hints?.[c]?.[s.toUpperCase()] ?? 0;
            const def = s === 'S' ? 50 : s === 'M' ? 100 : s === 'L' ? 100 : s === 'XL' ? 25 : s === 'XXL' ? 15 : s === 'XS' ? 30 : 50;
            seeded[c][s] = { stock: hint ? String(hint) : String(def), price: data.ai_suggested_price ? String(data.ai_suggested_price) : '', sku: '' };
          });
        });
        setMatrixValues(seeded);
        // Auto-open the smart variant matrix so the supplier lands directly on
        // the bulk stock entry grid.
        matrixOpenedRef.current = true;
        setShowVariantMatrix(true);
      }

      const cat = (data.suggested_category || '').toLowerCase();
      const cvPreset = data.photo_analysis?.suggested_bg_preset;
      if (cvPreset) handleRemoveBgModel(cvPreset);
      else if (/cloth|fashion|apparel|lingerie/.test(cat)) handleRemoveBgModel('lite_variants');
      else if (/beauty|cosmetic|perfume/.test(cat)) handleRemoveBgModel('marketing_variants');
      else if (/food|grocery/.test(cat)) handleRemoveBgModel('clean_commercial');
      else handleRemoveBgModel('birefnet_production');

      setAiFilled(true);
      speakGuidance(`AI filled form. Enter price and stock.`);

      if (data.copy_job_id) {
        setAiNote(`✨ AI filled ${filled} fields. Writing EN/AR description…`);
        pollCopyJob(data.copy_job_id);
      } else {
        setAiNote(`✨ AI filled ${filled} fields. Ready to publish!`);
        // Auto-show pricing panel only if there are no variants to fill first
        // (otherwise the variant matrix is the focus; pricing opens after it).
        if (!matrixOpenedRef.current) setTimeout(() => setShowPricingPanel(true), 500);
      }
    } catch {
      setError('AI analysis failed. You can fill manually.');
    } finally { setAiLoading(false); }
  };

  const pollCopyJob = async (jobId: string) => {
    const started = Date.now();
    const poll = async (): Promise<void> => {
      if (Date.now() - started > 240000) { setAiNote('✨ AI ready (vision timed out — data from photo analysis is ready).'); return; }
      try {
        const res = await apiFetch(`/supplier/upload/ai-copy/${jobId}`, { method: 'GET' });
        if (!res.ok) { setTimeout(poll, 4000); return; }
        const job: AiCopyJob = await res.json();
        if (job.status === 'pending') { setTimeout(poll, 4000); return; }
        if (job.status === 'done' && job.result) {
          const r = job.result;
          if (r.english_title) setFormData((f) => ({ ...f, name: r.english_title as string }));
          if (r.english_description) setFormData((f) => ({ ...f, description: r.english_description as string }));
          if (r.arabic_title) setNameAr(r.arabic_title);
          if (r.arabic_description) setDescriptionAr(r.arabic_description);
          if (r.suggested_tags?.length) setFormData((f) => ({ ...f, tags: (r.suggested_tags as string[]).join(', ') }));
          if (r.ai_suggested_price) {
            setFormData((f) => {
              if (!f.price) {
                if (r.price_min && r.price_max) setAiPriceRange({ min: r.price_min, max: r.price_max });
                return { ...f, price: String(r.ai_suggested_price) };
              }
              return f;
            });
          }
          if (r.photo_analysis) setPhotoAnalysis(r.photo_analysis);

          if (r.source === 'ollama') {
            if (r.suggested_category) {
              const match = CATEGORIES.find((c) => c.toLowerCase() === (r.suggested_category || '').toLowerCase())
                || CATEGORIES.find((c) => c.toLowerCase().includes((r.suggested_category || '').toLowerCase()))
                || 'Other';
              setFormData((f) => ({ ...f, category: match }));
            }
            if (r.suggested_subcategory) setFormData((f) => ({ ...f, subcategory: r.suggested_subcategory as string }));
            const visBrand = r.suggested_brand || r.detected_attributes?.brand;
            if (visBrand) setFormData((f) => ({ ...f, brand: visBrand as string }));
            const visColors = r.detected_attributes?.color;
            if (visColors?.length) setFormData((f) => ({ ...f, color: visColors.join(', ') }));
            const visVariants = (r.suggested_variants || []).filter(Boolean);
            if (visVariants.length) {
              const labels = { ...variantLabels };
              const incoming = (r.variant_labels || {}) as Record<string, string>;
              visVariants.forEach((t) => { if (incoming[t]) labels[t] = incoming[t]; });
              setVariantLabels(labels); setVariantTypes(visVariants);
              const opts: Record<string, string[]> = {};
              visVariants.forEach((t) => { opts[t] = (r.variant_options?.[t] || []).filter(Boolean); });
              setVariantOptions(opts); setVariantsEnabled(true);
            }
            if (r.ai_status === 'heuristic_fallback') {
              setAiNote('⚠️ AI service offline — used quick photo analysis (EN/AR copy may be limited). Start Ollama to enable full AI.');
            } else {
              setAiNote('✨ AI vision complete — full EN/AR description & details ready.');
            }
            speakGuidance('Description ready in English and Arabic.');
          } else {
            setAiNote('✨ Product data ready (from photo analysis). Edit as needed.');
            speakGuidance('Product data ready from photo analysis.');
          }
          // If the variant matrix is open, let the supplier advance via "Done"
          // (matrix → specs → pricing). Only auto-open pricing when there are
          // no variants to fill.
          if (!matrixOpenedRef.current) setTimeout(() => setShowPricingPanel(true), 500);
        } else {
          setAiNote('✨ Product data ready from photo analysis. Edit as needed.');
        }
      } catch { setTimeout(poll, 4000); }
    };
    setTimeout(poll, 4000);
  };

  /* ════════════════════════ Background Removal ═══════════════════════════ */

  const handleRemoveBg = async (preset: string) => {
    if (!selectedImage) return;
    const effective = preset === 'auto' ? 'general' : preset;
    setBgLoading(preset); setError('');
    try {
      const fd = new FormData(); fd.append('image', selectedImage); fd.append('preset', effective);
      fd.append('fast_mode', fastMode ? 'true' : 'false');
      const res = await apiFetch('/supplier/upload/remove-background', { method: 'POST', body: fd, timeoutMs: 120000, skipAuthRedirect: true });
      if (!res.ok) throw new Error();
      const blob = await res.blob();
      if (processedImageUrl) URL.revokeObjectURL(processedImageUrl);
      const url = URL.createObjectURL(blob);
      setProcessedImageBlob(blob); setProcessedImageUrl(url);
      setActiveBgPreset(preset); setActiveBgModel(null); setImagePreview(url);
    } catch { setError('Background removal failed.'); } finally { setBgLoading(null); }
  };

  const handleRemoveBgModel = async (modelKey: string) => {
    if (!selectedImage) return;
    setBgLoading(modelKey); setError('');
    try {
      const fd = new FormData(); fd.append('image', selectedImage); fd.append('preset', modelKey);
      fd.append('fast_mode', fastMode ? 'true' : 'false');
      const res = await apiFetch('/supplier/upload/remove-background', { method: 'POST', body: fd, timeoutMs: 120000, skipAuthRedirect: true });
      if (!res.ok) throw new Error();
      const blob = await res.blob();
      if (processedImageUrl) URL.revokeObjectURL(processedImageUrl);
      const url = URL.createObjectURL(blob);
      setProcessedImageBlob(blob); setProcessedImageUrl(url);
      setActiveBgModel(modelKey); setActiveBgPreset(null); setImagePreview(url);
    } catch { setError('Background removal failed.'); } finally { setBgLoading(null); }
  };

  const handleProcessTool = async (toolKey: string) => {
    const img = currentImageFile();
    if (!img) return;
    setBgLoading(toolKey);
    setError('');
    try {
      const fd = new FormData();
      fd.append('image', img);
      fd.append(toolKey, 'true');
      fd.append('bg_preset', '');
      const res = await apiFetch('/supplier/upload/process-tools', { method: 'POST', body: fd, timeoutMs: 120000, skipAuthRedirect: true });
      if (!res.ok) throw new Error();
      const blob = await res.blob();
      if (processedImageUrl) URL.revokeObjectURL(processedImageUrl);
      const url = URL.createObjectURL(blob);
      setProcessedImageBlob(blob); setProcessedImageUrl(url);
      setImagePreview(url);
      setImageToolToggles((p) => ({ ...p, [toolKey]: true }));
    } catch {
      setError(`${toolKey.replace('process_', '').replace(/_/g, ' ')} processing failed.`);
    } finally {
      setBgLoading(null);
    }
  };

  const resetBg = () => {
    if (processedImageUrl) URL.revokeObjectURL(processedImageUrl);
    setProcessedImageBlob(null); setProcessedImageUrl(null);
    setActiveBgPreset(null); setActiveBgModel(null);
    setImagePreview(originalPreviewUrl);
  };

  /* ════════════════════════ Angle Generation ═══════════════════════════ */

  const handleGenerateAngles = async () => {
    const img = currentImageFile(); if (!img) return;
    setGenAnglesLoading(true); setError('');
    try {
      const fd = new FormData(); fd.append('image', img);
      const res = await apiFetch('/supplier/upload/generate-angles', { method: 'POST', body: fd, timeoutMs: 120000, skipAuthRedirect: true });
      if (!res.ok) throw new Error();
      const data = await res.json();
      setAngleUrls((data.angle_urls || []).map((p: string) => p.startsWith('http') || p.startsWith('/') ? p : `/${p}`));
    } catch { setError('Angle generation failed.'); } finally { setGenAnglesLoading(false); }
  };

  /* ════════════════════════ Voice ┕═══════════════════════ */

  const getSpeechRecognition = () => {
    if (typeof window === 'undefined') return null;
    return (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition || null;
  };

  const stopDictation = () => { recognitionRef.current?.stop(); setListeningFor(null); };

  const startDictation = (target: 'name' | 'description' | 'price' | 'stock') => {
    const SR = getSpeechRecognition();
    if (!SR) { setError('Voice not supported in this browser.'); return; }
    const rec = new SR(); rec.lang = 'en-US'; rec.interimResults = true; rec.continuous = false;
    recognitionRef.current = rec; setListeningFor(target);
    setVoiceFeedback(`Speak ${target}...`);
    rec.onresult = (ev: any) => {
      const t = Array.from(ev.results).map((r: any) => r[0].transcript).join(' ');
      if (target === 'name') setFormData((f) => ({ ...f, name: (f.name ? f.name + ' ' : '') + t }));
      else if (target === 'description') setFormData((f) => ({ ...f, description: (f.description ? f.description + ' ' : '') + t }));
      else if (target === 'price') { const m = t.match(/(\d+(?:\.\d+)?)/); if (m) setFormData((f) => ({ ...f, price: m[1] })); }
      else if (target === 'stock') { const m = t.match(/(\d+)/); if (m) setFormData((f) => ({ ...f, stock_quantity: m[1] })); }
    };
    rec.onerror = () => stopDictation();
    rec.onend = () => { setListeningFor(null); setVoiceFeedback(''); };
    rec.start();
  };

  const startVoiceCommand = () => {
    const SR = getSpeechRecognition(); if (!SR) return;
    const rec = new SR(); rec.lang = 'en-US'; rec.interimResults = false; rec.continuous = true;
    recognitionRef.current = rec; setListeningFor('command');
    setVoiceFeedback('🎤 Voice on — say "AI fill", "remove bg", "price 500", "stock 100"');
    rec.onresult = (ev: any) => {
      const heard = Array.from(ev.results).map((r: any) => r[0].transcript.toLowerCase()).join(' ');
      setVoiceFeedback(`Heard: "${heard}"`);
      if (/ai fill|auto fill|analyze|detect/.test(heard)) { if (selectedImage) handleAiFill(); return; }
      if (/remove background|cut out|erase bg/.test(heard)) { if (selectedImage) handleRemoveBg('auto'); return; }
      if (/reset background|undo bg/.test(heard)) { resetBg(); return; }
      if (/save draft|save/.test(heard)) { saveDraft(true); return; }
      if (/clear draft/.test(heard)) { clearDraft(); return; }
      const num = heard.match(/(\d+(?:\.\d+)?)/);
      if (/price/.test(heard) && num) { setFormData((f) => ({ ...f, price: num[1] })); setVoiceFeedback(`Price ${num[1]}`); return; }
      if (/stock/.test(heard) && num) { setFormData((f) => ({ ...f, stock_quantity: num[1] })); setVoiceFeedback(`Stock ${num[1]}`); return; }
      if (/white bg/.test(heard)) { setCanvasBg('white'); setVoiceFeedback('White canvas'); return; }
      if (/transparent/.test(heard)) { setCanvasBg('transparent'); setVoiceFeedback('Transparent canvas'); return; }
      if (/black bg/.test(heard)) { setCanvasBg('black'); setVoiceFeedback('Black canvas'); return; }
      if (/zoom in/.test(heard)) { setCanvasZoom((z) => Math.min(5, z + 0.3)); return; }
      if (/zoom out/.test(heard)) { setCanvasZoom((z) => Math.max(0.1, z - 0.3)); return; }
      if (/rotate/.test(heard)) { setCanvasRotate((r) => r + 90); return; }
      for (const mdl of BG_MODELS) {
        if (heard.includes(mdl.label.toLowerCase()) || heard.includes(mdl.key.replace(/-/g, ' '))) {
          if (selectedImage) handleRemoveBgModel(mdl.key); return;
        }
      }
    };
    rec.onerror = () => { setListeningFor(null); setVoiceFeedback(''); };
    rec.onend = () => { if (listeningFor === 'command') setListeningFor(null); };
    rec.start();
  };

  const speakGuidance = (text: string) => {
    if (!audioGuidance || typeof window === 'undefined') return;
    if ('speechSynthesis' in window) {
      const u = new SpeechSynthesisUtterance(text); u.lang = 'en-US'; u.rate = 0.9;
      speechSynthesis.speak(u);
    }
  };

  /* ════════════════════════ Auto-suggest variants from config ════════════════════════ */

  useEffect(() => {
    if (!formData.category) return;
    const suggested = getSuggestedVariants(formData.category);
    if (suggested.length === 0) return;
    const types = suggested.map(s => s.key);
    const opts: Record<string, string[]> = {};
    const labels: Record<string, string> = {};
    suggested.forEach(s => {
      opts[s.key] = s.default_options;
      labels[s.key] = s.name;
    });
    setVariantTypes(types);
    setVariantOptions(opts);
    setVariantLabels(labels);
    if (types.length > 0) setVariantsEnabled(true);
  }, [formData.category]);

  /* ════════════════════════ Variants ═══════════════════════ */

  const rowSignature = (attrs: Record<string, string>): string => JSON.stringify(Object.keys(attrs).sort().reduce((o, k) => { o[k] = attrs[k]; return o; }, {} as Record<string, string>));
  const MAX_VARIANT_COMBOS = 100;

  const variantCombos = useMemo(() => {
    const arrays = variantTypes.map((t) => (variantOptions[t] || []).map((v) => ({ key: t, value: v })));
    let combos: Array<Array<{ key: string; value: string }>> = [[]];
    for (const arr of arrays) {
      const next: Array<Array<{ key: string; value: string }>> = [];
      for (const c of combos) for (const item of arr) next.push([...c, item]);
      combos = next;
    }
    return (combos.length === 0 ? [[]] : combos).slice(0, MAX_VARIANT_COMBOS).map((c) => {
      const attrs: Record<string, string> = {};
      c.forEach(({ key, value }) => { attrs[key] = value; });
      return { attrs };
    });
  }, [variantTypes, variantOptions]);

  const toggleVariantType = (key: string) => {
    if (variantTypes.includes(key)) { setVariantTypes(variantTypes.filter((t) => t !== key)); setVariantOptions((p) => { const n = { ...p }; delete n[key]; return n; }); }
    else { setVariantTypes([...variantTypes, key]); setVariantOptions((p) => (p[key] ? p : { ...p, [key]: [] })); }
  };
  const addOption = (key: string) => {
    const value = (newOption[key] || '').trim();
    if (!value) return;
    setVariantOptions((p) => ({ ...p, [key]: [...(p[key] || []).filter((x) => x !== value), value] }));
    setNewOption((p) => ({ ...p, [key]: '' }));
  };
  const removeOption = (key: string, value: string) => setVariantOptions((p) => ({ ...p, [key]: (p[key] || []).filter((x) => x !== value) }));
  const updateVariantValue = (sig: string, field: 'stock' | 'price', val: string) => setVariantValues((p) => ({ ...p, [sig]: { ...(p[sig] || { stock: '', price: '' }), [field]: val } }));

  // Specs (tick-box) — mirrors ProductSpecsSelector groups for inline display.
  const SPEC_LABELS: Record<string, Record<string, string>> = {
    fabric: { cotton: 'Cotton', polyester: 'Polyester', blend: 'Cotton-Poly Blend', silk: 'Silk', linen: 'Linen', wool: 'Wool', denim: 'Denim', leather: 'Leather', velvet: 'Velvet', lace: 'Lace', nylon: 'Nylon', spandex: 'Spandex', rayon: 'Rayon', jersey: 'Jersey', other_fabric: 'Other' },
    fit: { regular: 'Regular', slim: 'Slim', oversized: 'Oversized', relaxed: 'Relaxed', skinny: 'Skinny', tapered: 'Tapered', straight: 'Straight', loose: 'Loose' },
    sleeve: { short: 'Short Sleeve', long: 'Long Sleeve', sleeveless: 'Sleeveless', three_quarter: '3/4 Sleeve', dolman: 'Dolman/Batwing', raglan: 'Raglan' },
    care: { machine_wash: 'Machine Wash', hand_wash: 'Hand Wash', dry_clean: 'Dry Clean Only', tumble_dry: 'Tumble Dry Low', line_dry: 'Line Dry', iron_low: 'Iron on Low', do_not_bleach: 'Do Not Bleach', wash_cold: 'Wash Cold' },
    gender: { unisex: 'Unisex', men: 'Men', women: 'Women', kids: 'Kids', baby: 'Baby' },
    occasion: { casual: 'Casual', formal: 'Formal', sport: 'Sports/Athletic', party: 'Party', beach: 'Beach', office: 'Office Wear', traditional: 'Traditional', sleepwear: 'Sleepwear' },
  };
  const specsCount = useMemo(() => Object.values(selectedSpecs).reduce((s, a) => s + a.length, 0), [selectedSpecs]);
  const toggleSpec = (group: string, id: string) => {
    setSelectedSpecs((prev) => {
      const current = prev[group] || [];
      const next = current.includes(id) ? current.filter((x) => x !== id) : [...current, id];
      const updated = { ...prev, [group]: next };
      const allLabels: string[] = [];
      Object.values(updated).forEach((arr) => arr.forEach((s) => allLabels.push(s)));
      setFormData((f) => ({ ...f, tags: allLabels.join(', ') }));
      return updated;
    });
  };

  const computedVariantStock = useMemo(() => {
    if (Object.keys(matrixValues).length) {
      return Object.values(matrixValues).reduce((sum, row) =>
        sum + Object.values(row).reduce((r, cell) => r + (parseInt(cell.stock) || 0), 0), 0);
    }
    return variantCombos.reduce((sum, row) => sum + (Number(variantValues[rowSignature(row.attrs)]?.stock || 0) || 0), 0);
  }, [variantCombos, variantValues, matrixValues]);

  const buildVariantsJson = () => {
    if (Object.keys(matrixValues).length) {
      const out: any[] = [];
      for (const [color, sizes] of Object.entries(matrixValues)) {
        for (const [size, cell] of Object.entries(sizes)) {
          const attrs: Record<string, string> = {};
          if (color) attrs['color'] = color;
          if (size) attrs['size'] = size;
          out.push({
            is_active: true,
            attributes: attrs,
            title: [color, size].filter(Boolean).join(' / ') || 'Variant',
            stock: Number(cell.stock) || 0,
            ...(cell.price ? { price: Number(cell.price) } : {}),
          });
        }
      }
      return out;
    }
    return variantCombos.map((row) => {
      const attrs = row.attrs; const sig = rowSignature(attrs);
      const val = variantValues[sig] || { stock: '', price: '' };
      const attrsD: Record<string, string> = {};
      variantTypes.forEach((t) => { if (attrs[t]) attrsD[t] = attrs[t]; });
      const v: Record<string, unknown> = { is_active: true, attributes: attrsD, title: Object.values(attrsD).filter(Boolean).join(' / ') || 'Variant', stock: Number(val.stock) || 0 };
      if (val.price) v.price = Number(val.price);
      return v;
    });
  };

  /* ════════════════════════ Draft ═════════════════════════ */

  const saveDraft = (silent = false) => {
    const draft = { formData, variantsEnabled, variantTypes, variantOptions, variantLabels, savedAt: new Date().toISOString() };
    try { localStorage.setItem(DRAFT_KEY, JSON.stringify(draft)); setDraftSavedAt(draft.savedAt); if (!silent) setAiNote('Draft saved.'); } catch { }
  };
  const clearDraft = () => { localStorage.removeItem(DRAFT_KEY); setDraftSavedAt(null); setAiNote('Draft cleared.'); };

  useEffect(() => {
    try {
      const raw = localStorage.getItem(DRAFT_KEY); if (!raw) return;
      const d = JSON.parse(raw); if (d?.formData) { setPendingDraft(d); setDraftSavedAt(d.savedAt || null); setShowDraftRestore(true); }
    } catch { }
  }, []);

  const confirmRestoreDraft = (restore: boolean) => {
    if (restore && pendingDraft) {
      const d = pendingDraft;
      if (d?.formData) setFormData(d.formData);
      if (d.variantTypes) setVariantTypes(d.variantTypes);
      if (d.variantOptions) setVariantOptions(d.variantOptions);
      if (d.variantLabels) setVariantLabels(d.variantLabels);
    }
    setShowDraftRestore(false); setPendingDraft(null);
  };

  /* ════════════════════════ Translation ═══════════════════════════ */

  const handleTranslate = async () => {
    if (!formData.name && !formData.description) return;
    setTranslating(true);
    try {
      if (formData.name) { const fd = new FormData(); fd.append('text', formData.name); const r = await apiFetch('/supplier/upload/translate', { method: 'POST', body: fd, skipAuthRedirect: true }); if (r.ok) setNameAr(((await r.json()).translated_text as string) || ''); }
      if (formData.description) { const fd = new FormData(); fd.append('text', formData.description); const r = await apiFetch('/supplier/upload/translate', { method: 'POST', body: fd, skipAuthRedirect: true }); if (r.ok) setDescriptionAr(((await r.json()).translated_text as string) || ''); }
    } catch { setError('Translation failed.'); } finally { setTranslating(false); }
  };

  /* ════════════════════════ Submit ═════════════════════════ */

  const submitProduct = async () => {
    setError('');
    if (!formData.name || !formData.category) { setError('Name and category required.'); return; }
    if (!formData.price || parseFloat(formData.price) <= 0) { setError('Valid price required.'); return; }
    setLoading(true);
    try {
      const fd = new FormData();
      fd.append('name', formData.name);
      fd.append('description', formData.description || formData.name);
      fd.append('price', formData.price);
      fd.append('category', formData.category);
      fd.append('is_active', 'true');

      if (variantsEnabled && (Object.keys(matrixValues).length || variantCombos.length > 0)) {
        fd.append('stock_quantity', String(computedVariantStock));
        fd.append('variants_json', JSON.stringify(buildVariantsJson()));
      } else {
        fd.append('stock_quantity', formData.stock_quantity || '0');
      }

      if (formData.subcategory) fd.append('subcategory', formData.subcategory);
      if (formData.brand) fd.append('brand', formData.brand);
      if (formData.tags) fd.append('tags', formData.tags);
      if (formData.color) fd.append('color', formData.color);
      if (activeBgPreset) fd.append('bg_preset', activeBgPreset);
      if (nameAr) fd.append('name_ar', nameAr);
      if (descriptionAr) fd.append('description_ar', descriptionAr);

      if (!processedImageBlob) {
        Object.entries(imageToolToggles).forEach(([k, v]) => { if (v) fd.append(k, 'true'); });
      }

      const image = currentImageFile();
      if (image) fd.append('image', image);
      if (videoFile) fd.append('video', videoFile);
      if (videoLink.trim()) fd.append('video_url', videoLink.trim());

      const response = await apiFetch('/supplier/products', { method: 'POST', body: fd });
      if (response.ok) {
        localStorage.removeItem(DRAFT_KEY);
        const resultData = await response.json().catch(() => null);
        const prodId = resultData?.id || Math.floor(Math.random() * 90000) + 10000;
        const prodName = resultData?.name || formData.name;
        setPublishResult({ id: prodId, name: prodName });
        // Dynamic listing score based on completeness
        let score = 30;
        if (formData.name) score += 15;
        if (formData.description) score += 10;
        if (formData.category) score += 10;
        if (formData.tags) score += 5;
        if (formData.color) score += 5;
        if (selectedImage || uploadedImages.length) score += 10;
        if (videoFile) score += 5;
        if (nameAr || descriptionAr) score += 5;
        if (variantsEnabled && computedVariantStock > 0) score += 10;
        if (formData.brand) score += 5;
        if (specsCount > 0) score += 5;
        setListingScore(Math.min(100, score));
        // Countries from result or default
        setListingCountries(resultData?.countries || ['Oman']);
        setShowSuccess(true);
        if (createMore) {
          setFormData({ name: '', description: '', price: '', stock_quantity: '', category: '', subcategory: '', brand: '', tags: '', color: '', is_active: true });
          setSelectedImageSafe(null); setImagePreview(null); setOriginalPreviewUrl(null);
          setProcessedImageBlob(null); setProcessedImageUrl(null);
          setActiveBgPreset(null); setActiveBgModel(null);
          setAngleUrls([]); setVariantsEnabled(false); setVariantTypes([]); setVariantOptions({}); setVariantLabels({}); setVariantValues({}); setMatrixValues({});
          setAiFilled(false); setAiNote('Product created. Add another!');
          removeVideo(); setNameAr(''); setDescriptionAr('');
          setShowSuccess(false);
        }
      } else {
        const err = await response.json().catch(() => null);
        setError(err?.detail || 'Failed to create product');
      }
    } catch { setError('Failed to create product.'); } finally { setLoading(false); }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name || !formData.category || !formData.price || parseFloat(formData.price) <= 0) {
      // Re-enter the guided modal flow instead of an interrupting popup.
      setError('Please complete the highlighted details, then publish from the Finalize Listing screen.');
      if (variantsEnabled) setShowVariantMatrix(true);
      else setShowSpecsSelector(true);
      return;
    }
    await submitProduct();
  };

  const isFormValid = formData.name && formData.category && formData.price && parseFloat(formData.price) > 0;

  /* ════════════════════════ Verification summary builder ════════════════════════ */

  const verificationSummary = {
    name: formData.name,
    category: formData.category,
    colors: (formData.color ? formData.color.split(',').map((c) => c.trim()) : []),
    variants: variantTypes.map((t) => `${titleCase(t)}: ${(variantOptions[t] || []).join(', ')}`).join(' | ') || 'None',
    totalStock: computedVariantStock,
    price: formData.price ? `${formData.price} OMR` : 'Not set',
    description: formData.description,
    imagesCount: uploadedImages.length + (selectedImage ? 1 : 0),
    hasVideo: !!videoFile,
    tags: (formData.tags ? formData.tags.split(',').map((t) => t.trim()) : []),
  };

  /* ════════════════════════ RENDER ═════════════════════════ */

  return (
    <SupplierLayout>
      <PanelContent width="wide">
        <PanelHero
          eyebrow="Supplier Workspace"
          title="New Product"
          description="Upload a photo or describe by voice — ZOZI AI auto-fills the details, removes the background and builds your variants."
          icon={<Package className="w-6 h-6" />}
          actions={
            <div className="flex items-center gap-2">
              <Link href="/supplier/products" className="theme-btn-secondary inline-flex items-center gap-1.5 px-3 py-1.5 text-sm">
                <ArrowLeft className="w-4 h-4" /> Products
              </Link>
              <button type="button" onClick={() => (listeningFor === 'command' ? stopDictation() : startVoiceCommand())}
                className={`theme-btn-secondary px-2.5 py-1.5 text-xs ${listeningFor === 'command' ? '!bg-danger !text-white !border-danger animate-pulse' : ''}`}>
                {listeningFor === 'command' ? <MicOff className="w-3.5 h-3.5 inline mr-1" /> : <Mic className="w-3.5 h-3.5 inline mr-1" />}
                Voice
              </button>
              <button type="button" onClick={() => setAudioGuidance(!audioGuidance)}
                className={`theme-btn-secondary px-2.5 py-1.5 text-xs ${audioGuidance ? 'bg-primary text-white !border-primary' : ''}`}>
                <Volume2 className="w-3.5 h-3.5 inline mr-1" />{audioGuidance ? 'Guide On' : 'Guide'}
              </button>
            </div>
          }
        />

        {/* ── BG Strategy Onboarding Tooltip ── */}
        <BgStrategyOnboardingTooltip
          isOpen={showOnboarding}
          onClose={() => setShowOnboarding(false)}
          category={formData.category || undefined}
        />

        {/* ── Flow Progress Indicator ── */}
        <div className="flex items-center justify-center gap-0.5 sm:gap-2 mb-4 text-[11px] font-medium">
          {[
            { label: 'Upload', done: !!selectedImage, current: !selectedImage },
            { label: 'AI Analyze', done: aiFilled, current: selectedImage && !aiFilled && !showPricingPanel },
            { label: 'Details', done: !!formData.name && !!formData.category, current: showPricingPanel },
            { label: 'Publish', done: showSuccess, current: false },
          ].map((step, i) => (
            <div key={step.label} className="flex items-center gap-0.5 sm:gap-2">
              <span className={`flex items-center gap-1 px-2.5 py-1 rounded-full transition-all ${
                step.current ? 'bg-primary text-white shadow-sm' :
                step.done ? 'bg-success/10 text-success' : 'bg-surface-2 text-text-faint'
              }`}>
                {step.done ? <Check className="w-3 h-3" /> : <span className="w-1.5 h-1.5 rounded-full inline-block" />}
                <span className="hidden sm:inline">{step.label}</span>
              </span>
              {i < 3 && <ChevronRight className="w-3.5 h-3.5 text-text-faint/40" />}
            </div>
          ))}
        </div>

        {aiNote && (
          <div className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-primary/8 border border-primary/20 text-sm text-primary mb-3">
            <Sparkles className="w-4 h-4 shrink-0" /> {aiNote}
            {showWhyThis && autoSelectedWinner && (
              <button
                type="button"
                onClick={() => setShowWhyThis((p) => !p)}
                className="ml-auto inline-flex items-center gap-1 text-[11px] text-primary/80 hover:text-primary transition-colors"
                title="Why this strategy?"
              >
                <Info className="w-3.5 h-3.5" /> Why this?
              </button>
            )}
          </div>
        )}

        {/* ── Why this? expander ── */}
        {showWhyThis && autoSelectedWinner && (() => {
          const cat = formData.category || 'unknown';
          const metrics = getStrategyMetrics(autoSelectedWinner, cat);
          if (!metrics) return null;
          return (
            <div className="px-4 py-3 rounded-xl bg-surface-1 border border-border/60 text-xs text-text-muted mb-3 animate-in fade-in slide-in-from-top-1">
              <div className="flex items-center gap-2 mb-2">
                <BarChart3 className="w-3.5 h-3.5 text-primary" />
                <span className="font-semibold text-text text-xs">
                  {autoSelectedWinner.replace(/_/g, ' ')} selected for <span className="capitalize">{cat.toLowerCase()}</span>
                </span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                <div className="theme-card p-2">
                  <p className="text-[10px] text-text-faint uppercase tracking-wide">SSIM</p>
                  <p className="text-sm font-bold text-text">{metrics.ssim.toFixed(3)}</p>
                </div>
                <div className="theme-card p-2">
                  <p className="text-[10px] text-text-faint uppercase tracking-wide">PSNR</p>
                  <p className="text-sm font-bold text-text">{metrics.psnr_rgb_db.toFixed(1)} dB</p>
                </div>
                <div className="theme-card p-2">
                  <p className="text-[10px] text-text-faint uppercase tracking-wide">Edge IoU</p>
                  <p className="text-sm font-bold text-text">{(metrics.edge_band_iou * 100).toFixed(1)}%</p>
                </div>
                <div className="theme-card p-2">
                  <p className="text-[10px] text-text-faint uppercase tracking-wide">Timing</p>
                  <p className="text-sm font-bold text-text">{metrics.timing_s.toFixed(2)}s</p>
                </div>
              </div>
              <div className="mt-2 flex items-center gap-3 text-[11px]">
                <span className="inline-flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-emerald-500" /> Coverage: {metrics.coverage_pct.toFixed(1)}%
                </span>
                <span className="text-text-faint">
                  Score weights: SSIM 50% · PSNR 25% · Edge IoU 25%
                </span>
              </div>
            </div>
          );
        })()}

        {error && (
          <div className="px-4 py-3 theme-alert-danger rounded-xl flex items-center justify-between text-sm">
            <span>{error}</span>
            <button type="button" onClick={() => setError('')} className="text-current opacity-60 hover:opacity-100"><X className="w-4 h-4" /></button>
          </div>
        )}

        {/* ── Media intake row ── */}
        {!selectedImage && !cameraActive && (
          <div className="theme-card rounded-2xl p-5">
            <div
              onDragOver={handleDragOver} onDragLeave={handleDragLeave} onDrop={handleDrop}
              className={`flex flex-col items-center justify-center border-2 border-dashed rounded-2xl transition-colors py-10 ${dragOver ? 'border-primary bg-primary/10' : 'border-border/50'}`}>
              <Upload className="w-14 h-14 text-primary/40 mb-3" />
              <p className="text-sm text-text-muted mb-5">Drop a product photo here, or choose how to add it</p>
              <div className="flex flex-wrap items-center justify-center gap-3">
                <label className="theme-btn-primary inline-flex items-center gap-2 px-5 py-2.5 cursor-pointer">
                  <Upload className="w-4 h-4" /> Choose Photo
                  <input type="file" accept="image/jpeg,image/png,image/webp,image/gif" onChange={handleImageChange} className="hidden" />
                </label>
                <button type="button" onClick={() => setShowMediaUpload(true)} className="theme-btn-secondary inline-flex items-center gap-2 px-5 py-2.5">
                  <Camera className="w-4 h-4" /> Smart Upload
                </button>
                <button type="button" onClick={handleManualEntry} className="theme-btn-secondary inline-flex items-center gap-2 px-5 py-2.5">
                  <PenLine className="w-4 h-4" /> Manual Entry
                </button>
              </div>
              {!videoFile && (
                <div className="mt-4 flex items-center gap-3">
                  <button type="button" onClick={startCamera} className="theme-btn-secondary inline-flex items-center gap-2 px-4 py-2 text-xs">
                    <Camera className="w-3.5 h-3.5" /> Camera
                  </button>
                  <label className="theme-btn-secondary inline-flex items-center gap-2 px-4 py-2 text-xs cursor-pointer">
                    <Film className="w-3.5 h-3.5" /> Video
                    <input type="file" accept="video/mp4,video/webm" onChange={handleVideoFileChange} className="hidden" />
                  </label>
                </div>
              )}
            </div>
            {!videoFile && (
              <div className="mt-4">
                <label className="text-xs font-medium text-text-muted">Or paste a video link</label>
                <input type="url" value={videoLink} onChange={(e) => setVideoLink(e.target.value)}
                  placeholder="https://..." className="theme-input w-full mt-1 text-sm" />
                    {Object.keys(matrixValues).length === 0 && variantTypes.length > 0 && (
                      <div className="flex gap-1.5 pt-1">
                        <button type="button" onClick={() => {
                          // Auto-fill all suggested options for selected variant types
                          const catVariants = getSuggestedVariants(formData.category);
                          const newOpts = { ...variantOptions };
                          variantTypes.forEach(type => {
                            const cfg = catVariants.find(s => s.key === type);
                            if (cfg?.default_options.length) {
                              newOpts[type] = cfg.default_options;
                            }
                          });
                          setVariantOptions(newOpts);
                        }}
                          className="theme-btn-secondary px-2 py-1 rounded text-[10px] flex items-center gap-1">
                          <Wand2 className="w-3 h-3" /> Fill all options
                        </button>
                        <button type="button" onClick={() => setShowVariantMatrix(true)}
                          className="theme-btn-secondary px-2 py-1 rounded text-[10px] flex items-center gap-1">
                          <Grid2x2 className="w-3 h-3" /> Stock Matrix
                        </button>
                      </div>
                    )}
                  </div>
                )}
          </div>
        )}

        {selectedImage && (
          <form onSubmit={handleSubmit} className="grid grid-cols-1 lg:grid-cols-[1.4fr_1fr] gap-5 items-start">
            {/* ════════════ LEFT: CANVAS STUDIO ════════════ */}
            <div className="theme-card rounded-2xl overflow-hidden">
              <div className="relative bg-surface-1 flex items-center justify-center select-none min-h-[400px]"
                onPointerDown={onCanvasPointerDown}
                onPointerMove={onCanvasPointerMove}
                onPointerUp={onCanvasPointerUp}
                onPointerLeave={onCanvasPointerUp}
                onWheel={onCanvasWheel}>
                {imagePreview ? (
                  <canvas ref={drawCanvasRef} className="max-w-full max-h-full" />
                ) : cameraActive ? (
                  <div className="relative w-full h-full min-h-[400px]">
                    <video ref={videoRef} autoPlay playsInline className="w-full h-full object-cover rounded-xl" />
                    <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-3">
                      <button type="button" onClick={capturePhoto} className="px-6 py-2 theme-btn-primary rounded-full">📸 Capture</button>
                      <button type="button" onClick={stopCamera} className="px-4 py-2 theme-btn-secondary rounded-full">Cancel</button>
                    </div>
                  </div>
                ) : null}
                {!imagePreview && !cameraActive && videoPreviewUrl && (
                  <div className="relative w-full min-h-[400px] flex items-center justify-center bg-black">
                    <video src={videoPreviewUrl} controls className="max-w-full max-h-full rounded-xl" />
                    <Button variant="danger" type="button" onClick={removeVideo}><X className="w-4 h-4" /></Button>
                  </div>
                )}
              </div>

              {/* Canvas toolbar */}
              <div className="border-t border-border/10 bg-surface-1/50 p-3">
                <div className="flex flex-wrap items-center gap-1.5">
                  <button type="button" onClick={() => setCanvasZoom((z) => Math.max(0.1, z - 0.2))} className="theme-btn-secondary px-2 py-1.5 text-xs"><Square className="w-3.5 h-3.5" /></button>
                  <span className="text-xs text-text-muted w-10">{Math.round(canvasZoom * 100)}%</span>
                  <button type="button" onClick={() => setCanvasZoom((z) => Math.min(5, z + 0.2))} className="theme-btn-secondary px-2 py-1.5 text-xs"><Maximize2 className="w-3.5 h-3.5" /></button>
                  <div className="w-px h-5 bg-border/30 mx-1" />
                  <button type="button" onClick={() => setCanvasRotate((r) => r - 90)} className="theme-btn-secondary px-2 py-1.5 text-xs"><RotateCcw className="w-3.5 h-3.5" /></button>
                  <button type="button" onClick={() => setCanvasRotate((r) => r + 90)} className="theme-btn-secondary px-2 py-1.5 text-xs"><RotateCw className="w-3.5 h-3.5" /></button>
                  <button type="button" onClick={() => { setCanvasZoom(1); setCanvasPan({ x: 0, y: 0 }); setCanvasRotate(0); }} className="theme-btn-secondary px-2 py-1.5 text-xs"><RefreshCw className="w-3.5 h-3.5" /></button>
                  <div className="w-px h-5 bg-border/30 mx-1" />
                  <button type="button" onClick={() => setCanvasBg('transparent')} className={`theme-btn-secondary px-2 py-1.5 text-xs ${canvasBg === 'transparent' ? 'bg-primary text-white' : ''}`}>T</button>
                  <button type="button" onClick={() => setCanvasBg('white')} className={`theme-btn-secondary px-2 py-1.5 text-xs ${canvasBg === 'white' ? 'bg-primary text-white' : ''}`}>W</button>
                  <button type="button" onClick={() => setCanvasBg('black')} className={`theme-btn-secondary px-2 py-1.5 text-xs ${canvasBg === 'black' ? 'bg-primary text-white' : ''}`}>B</button>
                  <div className="w-px h-5 bg-border/30 mx-1" />
                  <button type="button" onClick={() => setShowGrid(!showGrid)} className={`theme-btn-secondary px-2 py-1.5 text-xs ${showGrid ? 'bg-primary text-white' : ''}`}><Grid2x2 className="w-3.5 h-3.5" /></button>
                  <div className="w-px h-5 bg-border/30 mx-1" />
                  {IMAGE_TOOLS.slice(0, 6).map((tool) => (
                    <button key={tool.key} type="button" onClick={() => handleProcessTool(tool.key)} disabled={bgLoading !== null}
                      className={`theme-btn-secondary px-2 py-1.5 text-xs ${imageToolToggles[tool.key] ? 'bg-primary text-white' : ''}`}>
                      {bgLoading === tool.key ? <Loader2 className="w-3 h-3 inline animate-spin" /> : null}
                      {tool.label}
                    </button>
                  ))}
                  <div className="w-px h-5 bg-border/30 mx-1" />
                  <button type="button" onClick={handleGenerateAngles} disabled={genAnglesLoading} className="theme-btn-secondary px-2 py-1.5 text-xs">
                    {genAnglesLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />} Angles
                  </button>
                  <button type="button" onClick={removeImage} className="theme-btn-secondary px-2 py-1.5 text-xs text-danger"><X className="w-3.5 h-3.5" /> Remove</button>
                </div>

                {/* Background removal models */}
                <div className="flex flex-wrap items-center gap-1.5 mt-2 pt-2 border-t border-border/10">
                  <span className="text-[11px] font-medium text-text-muted mr-1">BG:</span>
                  {BG_MODELS.map((mdl) => {
                    const selectedCat = formData.category?.toLowerCase() || '';
                    const isBestForCategory = mdl.bestFor.some(cat => selectedCat.includes(cat));
                    const metrics = getStrategyMetrics(mdl.key, selectedCat);
                    return (
                      <div key={mdl.key} className="relative group">
                        <button type="button" onClick={() => handleRemoveBgModel(mdl.key)} disabled={bgLoading !== null}
                          className={`theme-btn-secondary px-2 py-1.5 text-xs relative ${activeBgModel === mdl.key ? 'bg-accent text-white' : ''} ${isBestForCategory ? 'ring-1 ring-emerald-500/40' : ''}`}>
                          {bgLoading === mdl.key ? <Loader2 className="w-3 h-3 animate-spin" /> : null}
                          {mdl.label}
                          {isBestForCategory && (
                            <span className="absolute -top-1.5 -right-1.5 inline-flex items-center px-1 py-0.5 rounded-full bg-emerald-500 text-[8px] font-bold text-white leading-none shadow-sm">
                              Best
                            </span>
                          )}
                        </button>
                        {/* Metrics badge */}
                        {metrics && (
                          <div className="absolute top-full left-1/2 -translate-x-1/2 mt-1 hidden group-hover:flex items-center gap-1 z-50 bg-gray-900 text-white text-[9px] rounded px-1.5 py-1 shadow-xl whitespace-nowrap">
                            <span className="text-emerald-400">{metrics.coverage_pct.toFixed(0)}%</span>
                            <span className="text-gray-500">·</span>
                            <span className="text-gray-300">{metrics.timing_s.toFixed(2)}s</span>
                          </div>
                        )}
                        {/* Hover tooltip */}
                        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 hidden group-hover:block z-50 w-56">
                          <div className="bg-gray-900 text-white text-[11px] rounded-lg px-3 py-2 shadow-xl">
                            <p className="font-semibold text-[12px] mb-1">{mdl.label.replace(' · ', ' — ')}</p>
                            <p className="text-gray-300 leading-relaxed">{mdl.tooltip}</p>
                            {mdl.bestFor.length > 0 && (
                              <div className="mt-1.5 pt-1.5 border-t border-gray-700">
                                <span className="text-emerald-400 font-medium">Best for: </span>
                                <span className="text-gray-300">{mdl.bestFor.map(c => c.charAt(0).toUpperCase() + c.slice(1)).join(', ')}</span>
                              </div>
                            )}
                          </div>
                          <div className="absolute top-full left-1/2 -translate-x-1/2 w-2 h-2 -mt-0.5 rotate-45 bg-gray-900" />
                        </div>
                      </div>
                    );
                  })}
                  <div className="w-px h-5 bg-border/30 mx-1" />
                  {(activeBgPreset || activeBgModel) && (
                    <button type="button" onClick={resetBg} className="theme-btn-secondary px-2 py-1.5 text-xs"><RefreshCw className="w-3 h-3" /></button>
                  )}
                  <div className="w-px h-5 bg-border/30 mx-1" />
                  <button type="button" onClick={() => setFastMode((p) => !p)}
                    className={`theme-btn-secondary px-2 py-1.5 text-xs text-[10px] ${fastMode ? 'bg-accent/15 text-accent border-accent/30' : 'bg-surface-2 text-text-muted border-border'}`}>
                    {fastMode ? '⚡ Fast' : '🎯 Quality'}
                  </button>
                </div>
              </div>

              {angleUrls.length > 0 && (
                <div className="border-t border-border/10 p-3">
                  <p className="text-xs text-text-muted mb-2">{angleUrls.length} AI angle views</p>
                  <div className="flex gap-2 overflow-x-auto pb-1">
                    {angleUrls.map((u, i) => (
                      <div key={i} className="w-20 h-20 rounded-lg overflow-hidden border border-border/30 bg-surface-2 shrink-0">
                        <img src={u} alt={`angle ${i + 1}`} className="w-full h-full object-contain" />
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* ════════════ RIGHT: SMART FORM ════════════ */}
            <div className="space-y-4">
              {/* AI Auto-Fill */}
              <div className="theme-card p-4">
                <h3 className="text-sm font-bold text-text mb-3 flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-primary" /> AI Auto-Fill
                </h3>
                <button type="button" onClick={handleAiFill} disabled={!selectedImage || aiLoading}
                  className="theme-btn-primary w-full py-2.5 disabled:opacity-50 flex items-center justify-center gap-2 text-sm">
                  {aiLoading ? <><Loader2 className="w-4 h-4 animate-spin" /> Analyzing…</> : <><Sparkles className="w-4 h-4" /> {aiFilled ? 'Re-analyze' : 'Analyze Photo'}</>}
                </button>

                {photoAnalysis && (
                  <div className="mt-3 pt-3 border-t border-border/10">
                    <p className="text-[11px] font-medium text-text-muted mb-1.5 flex items-center gap-1">
                      <Eye className="w-3 h-3" /> AI saw in photo
                    </p>
                    {photoAnalysis.dominant_colors && photoAnalysis.dominant_colors.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mb-2">
                        {photoAnalysis.dominant_colors.map((c) => (
                          <span key={c} className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full bg-surface-2 text-[11px] border border-border/30 capitalize">
                            <span className="w-2.5 h-2.5 rounded-full border border-black/10" style={{ background: c }} />
                            {c}
                          </span>
                        ))}
                      </div>
                    )}
                    <p className="text-[11px] text-text-muted">
                      Background: <span className="capitalize font-medium text-text">{photoAnalysis.background || 'unknown'}</span>
                      {photoAnalysis.suggested_bg_preset ? ` · bg cleanup suggested` : ''}
                    </p>
                  </div>
                )}
              </div>

              {/* Product Name */}
              <div className="theme-card p-4">
                <label className="text-sm font-bold text-text mb-2 flex items-center justify-between">
                  Product Name
                  <button type="button" onClick={() => startDictation('name')}
                    className={`theme-btn-secondary px-2 py-1.5 text-xs ${listeningFor === 'name' ? 'bg-danger text-white border-danger' : ''}`}>
                    <Mic className="w-3 h-3" />
                  </button>
                </label>
                <input type="text" value={formData.name} onChange={(e) => setFormData((f) => ({ ...f, name: e.target.value }))}
                  placeholder="AI will auto-detect from photo" className="theme-input w-full text-sm" />
              </div>

              {/* Category */}
              <div className="theme-card p-4">
                <label className="text-sm font-bold text-text mb-2">Category</label>
                <select value={formData.category} onChange={(e) => { const c = e.target.value; setFormData((f) => ({ ...f, category: c })); applyCategoryBaseline(c); }}
                  className="theme-input w-full text-sm">
                  <option value="">AI auto-selects…</option>
                  {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
                </select>
                {formData.category && (() => {
                  const suggested = getSuggestedVariants(formData.category);
                  if (suggested.length === 0) return null;
                  return (
                    <div className="mt-2 flex flex-wrap gap-1">
                      <span className="text-[10px] text-text-faint mr-0.5 self-center">Auto-variants:</span>
                      {suggested.map(s => (
                        <span key={s.key} className="px-1.5 py-0.5 rounded bg-primary/5 text-primary text-[10px] border border-primary/20">
                          {s.name}
                        </span>
                      ))}
                    </div>
                  );
                })()}
              </div>

              {/* Description */}
              <div className="theme-card p-4">
                <label className="text-sm font-bold text-text mb-2 flex items-center justify-between">
                  Description
                  <button type="button" onClick={() => startDictation('description')}
                    className={`theme-btn-secondary px-2 py-1.5 text-xs ${listeningFor === 'description' ? 'bg-danger text-white border-danger' : ''}`}>
                    <Mic className="w-3 h-3" />
                  </button>
                </label>
                <textarea value={formData.description} onChange={(e) => setFormData((f) => ({ ...f, description: e.target.value }))}
                  rows={3} placeholder="AI generates from photo…" className="theme-input w-full text-sm resize-none" />
              </div>

              {/* Tags */}
              <div className="theme-card p-4">
                <label className="text-sm font-bold text-text mb-2">Tags</label>
                <input type="text" value={formData.tags} onChange={(e) => setFormData((f) => ({ ...f, tags: e.target.value }))}
                  placeholder="AI auto-tags from photo" className="theme-input w-full text-sm" />
              </div>

              {/* Variants */}
              <div className="theme-card p-4">
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-bold text-text">Variants</label>
                  <label className="flex items-center gap-1.5 text-xs text-text-muted cursor-pointer">
                    <input type="checkbox" checked={variantsEnabled} onChange={(e) => setVariantsEnabled(e.target.checked)} className="accent-primary" />
                    Enable
                  </label>
                </div>
                {variantsEnabled && (
                  <div className="space-y-2">
                    <div className="flex flex-wrap gap-1.5">
                      {(() => {
                        // Show variant types from config based on category, fallback to common ones
                        const catVariants = formData.category ? getSuggestedVariants(formData.category) : [];
                        const suggestedKeys = catVariants.map(s => s.key);
                        const displayKeys = suggestedKeys.length >= 3 ? suggestedKeys : ['color', 'size', 'material', 'pattern', 'gender', 'fit', 'sleeve_length', 'occasion', 'brand'];
                        return displayKeys.map((key) => (
                          <button key={key} type="button" onClick={() => toggleVariantType(key)}
                            className={`theme-btn-secondary px-2 py-1 rounded-full text-xs ${variantTypes.includes(key) ? '!bg-primary !text-white !border-primary' : ''}`}>
                            {variantLabels[key] || titleCase(key)}
                          </button>
                        ));
                      })()}
                    </div>
                    {variantTypes.map((type) => {
                      const configItem = getSuggestedVariants(formData.category).find(s => s.key === type);
                      const quickOptions = configItem?.default_options || [];
                      return (
                        <div key={type} className="border border-border/20 rounded-lg p-2">
                          <p className="text-xs font-medium text-text mb-1">{variantLabels[type] || titleCase(type)}</p>
                          <div className="flex flex-wrap gap-1 mb-1.5">
                            {(variantOptions[type] || []).map((opt) => (
                              <span key={opt} className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-surface-2 text-xs border border-border/30">
                                {opt}
                                <button type="button" onClick={() => removeOption(type, opt)} className="text-text-muted hover:text-danger"><X className="w-2.5 h-2.5" /></button>
                              </span>
                            ))}
                          </div>
                          {quickOptions.length > 0 && (
                            <div className="flex flex-wrap gap-1 mb-1.5">
                              <span className="text-[10px] text-text-faint mr-0.5 self-center">Quick:</span>
                              {quickOptions.filter(o => !(variantOptions[type] || []).includes(o)).slice(0, 8).map((opt) => (
                                <button key={opt} type="button" onClick={() => {
                                  setVariantOptions(p => ({ ...p, [type]: [...(p[type] || []), opt] }));
                                }}
                                  className="px-1.5 py-0.5 rounded bg-primary/5 text-primary text-[10px] border border-primary/20 hover:bg-primary/10 transition-colors">
                                  +{opt}
                                </button>
                              ))}
                            </div>
                          )}
                          <div className="flex gap-1">
                            <input type="text" value={newOption[type] || ''} onChange={(e) => setNewOption((p) => ({ ...p, [type]: e.target.value }))}
                              onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addOption(type); } }}
                              placeholder={`Add ${titleCase(type).toLowerCase()}`} className="theme-input flex-1 text-xs" />
                            <button type="button" onClick={() => addOption(type)} className="theme-btn-primary px-2 py-1 rounded text-xs"><Plus className="w-3 h-3" /></button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Specs */}
              <div className="theme-card p-4">
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-bold text-text flex items-center gap-2">
                    <ListChecks className="w-4 h-4 text-primary" /> Specifications
                  </label>
                  {specsCount > 0 && (
                    <span className="px-2 py-0.5 rounded-full bg-primary/10 text-primary text-[11px] font-medium">{specsCount} selected</span>
                  )}
                </div>
                <p className="text-xs text-text-muted mb-2">Tap to add product details — no typing needed.</p>
                <button type="button" onClick={() => setShowSpecsSelector(true)}
                  className="w-full theme-btn-secondary inline-flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-medium">
                  <ListChecks className="w-3.5 h-3.5" /> {specsCount > 0 ? 'Edit Specs' : 'Add Specs'}
                </button>
                {specsCount > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {Object.entries(selectedSpecs).flatMap(([group, arr]) =>
                      arr.map((id) => {
                        const opt = SPEC_LABELS[group]?.[id];
                        return opt ? (
                          <span key={`${group}-${id}`} className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-surface-2 text-[11px] border border-border/30">
                            {opt}
                            <button type="button" onClick={() => toggleSpec(group, id)} className="text-text-muted hover:text-danger"><X className="w-2.5 h-2.5" /></button>
                          </span>
                        ) : null;
                      })
                    )}
                  </div>
                )}
              </div>

              {/* Pricing */}
              <div className="theme-card p-4">
                <h3 className="text-sm font-bold text-text mb-3 flex items-center gap-2">
                  <DollarSign className="w-4 h-4 text-primary" /> Pricing &amp; Inventory
                </h3>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-text mb-1">Price *</label>
                    <div className="relative">
                      <span className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted text-sm">$</span>
                      <input type="number" value={formData.price} onChange={(e) => setFormData((f) => ({ ...f, price: e.target.value }))}
                        placeholder="0.00" min="0" step="0.01" required
                        className="theme-input w-full pl-7 pr-3 py-2.5 text-sm" />
                    </div>
                    {aiPriceRange && !formData.price && (
                      <Button variant="secondary" className="mt-1.5 w-full theme-btn-secondary inline-flex items-center justify-center gap-1.5 text-xs !text-primary !/20 py-1.5" type="button" onClick={() => setFormData((f) => ({ ...f, price: String(aiPriceRange!.min + (aiPriceRange!.max - aiPriceRange!.min) / 2) }))}>
                        <Sparkles className="w-3 h-3" /> AI suggests {aiPriceRange.min.toFixed(3)}–{aiPriceRange.max.toFixed(3)} OMR
                      </Button>
                    )}
                    <button type="button" onClick={() => startDictation('price')}
                      className={`mt-1 theme-btn-secondary px-2 py-1.5 text-xs ${listeningFor === 'price' ? 'bg-danger text-white border-danger' : ''}`}>
                      <Mic className="w-3 h-3" /> Say price
                    </button>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-text mb-1">Stock</label>
                    {variantsEnabled ? (
                      <div className="flex items-center gap-2">
                        <input type="number" min="0" value={singleStock} onChange={(e) => setSingleStock(e.target.value)}
                          className="theme-input flex-1 py-2.5 text-sm" />
                        <span className="text-xs text-text-muted">= {computedVariantStock}</span>
                      </div>
                    ) : (
                      <input type="number" value={formData.stock_quantity} onChange={(e) => setFormData((f) => ({ ...f, stock_quantity: e.target.value }))}
                        placeholder="0" min="0" className="theme-input w-full py-2.5 text-sm" />
                    )}
                    <button type="button" onClick={() => startDictation('stock')}
                      className={`mt-1 theme-btn-secondary px-2 py-1.5 text-xs ${listeningFor === 'stock' ? 'bg-danger text-white border-danger' : ''}`}>
                      <Mic className="w-3 h-3" /> Say stock
                    </button>
                  </div>
                </div>
              </div>

              {/* Arabic */}
              <div className="theme-card p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-bold text-text flex items-center gap-1.5"><Globe className="w-4 h-4 text-accent" /> Arabic</h3>
                  <button type="button" onClick={handleTranslate} disabled={translating}
                    className="text-xs theme-btn-secondary px-2 py-1 disabled:opacity-50">
                    {translating ? '…' : 'Auto-translate'}
                  </button>
                </div>
                <input type="text" value={nameAr} onChange={(e) => setNameAr(e.target.value)}
                  placeholder="الاسم بالعربية" className="theme-input w-full text-sm mb-2 text-right" dir="rtl" />
                <textarea value={descriptionAr} onChange={(e) => setDescriptionAr(e.target.value)}
                  rows={2} placeholder="الوصف بالعربية" className="theme-input w-full text-sm resize-none text-right" dir="rtl" />
              </div>

              {/* Draft / Save */}
              <div className="theme-card p-4">
                <div className="flex gap-2">
                  <button type="button" onClick={() => saveDraft(false)} className="theme-btn-secondary flex-1 px-3 py-2 text-sm flex items-center justify-center gap-1">
                    <Save className="w-4 h-4" /> Draft
                  </button>
                  <Button variant="danger" type="button" onClick={clearDraft}>
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
                {draftSavedAt && <p className="text-[10px] text-text-muted mt-1">Saved {new Date(draftSavedAt).toLocaleTimeString()}</p>}
              </div>

              {/* Submit / Verify */}
              <div className="theme-card p-4">
                <label className="flex items-center gap-2 text-xs text-text-muted mb-3 cursor-pointer">
                  <input type="checkbox" checked={createMore} onChange={(e) => setCreateMore(e.target.checked)} className="accent-primary" />
                  Add another after publish
                </label>
                <button type="submit" disabled={loading}
                  className="theme-btn-primary w-full py-3 disabled:opacity-50 flex items-center justify-center gap-2 font-semibold">
                  {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <CheckCircle2 className="w-5 h-5" />}
                  {createMore ? 'Create & Next' : 'Review & Publish'}
                </button>
                <p className="text-xs text-text-faint text-center mt-2">Thank you for using ZOZI!</p>
              </div>
            </div>
          </form>
        )}

        {/* ── Manual entry hint ── */}
        {!selectedImage && (
          <div className="text-center text-xs text-text-faint">
            Prefer typing? Use <span className="text-primary font-medium">Manual Entry</span> above — the AI assist is optional.
          </div>
        )}
      </PanelContent>

      {/* ── Draft restore ── */}
      {showDraftRestore && (
        <div className="fixed inset-0 z-50 flex items-center justify-center theme-overlay p-4" onClick={() => setShowDraftRestore(false)} role="dialog" aria-modal="true">
          <div className="glass-panel border rounded-2xl p-6 shadow-2xl max-w-sm w-full mx-4" onClick={(e) => e.stopPropagation()}>
            <h3 className="font-bold text-text mb-2">Restore draft?</h3>
            <p className="text-sm text-text-muted mb-4">You have an unsaved draft from {draftSavedAt ? new Date(draftSavedAt).toLocaleString() : 'a previous session'}.</p>
            <div className="flex gap-3 justify-end">
              <button type="button" onClick={() => confirmRestoreDraft(false)} className="theme-btn-secondary px-4 py-2">Start Fresh</button>
              <button type="button" onClick={() => confirmRestoreDraft(true)} className="px-4 py-2 theme-btn-primary rounded-lg">Restore</button>
            </div>
          </div>
        </div>
      )}

      {/* ── Smart Media Upload ── */}
      {showMediaUpload && (
        <SmartMediaUpload
          onImagesSelected={handleSmartImages}
          onVoiceStart={() => { setShowMediaUpload(false); setShowVoiceInput(true); }}
          onManualEntry={handleManualEntry}
          onClose={() => setShowMediaUpload(false)}
        />
      )}

      {/* ── Action Picker (Mic / Magic) ── */}
      {showActionPicker && selectedImage && (
        <div className="fixed inset-0 z-50 flex items-center justify-center theme-overlay p-4" onClick={() => setShowActionPicker(false)} role="dialog" aria-modal="true">
          <div className="glass-panel border rounded-2xl shadow-2xl w-full max-w-sm mx-4 overflow-hidden" onClick={(e) => e.stopPropagation()}>
            <div className="p-6 text-center">
              <h2 className="text-lg font-semibold text-text mb-2">Enhance Your Product</h2>
              <p className="text-sm text-text-muted mb-6">Choose how to add product details</p>
              <div className="grid grid-cols-2 gap-4">
                <button className="flex flex-col items-center gap-3 p-6 rounded-xl border-2 border-primary/20 bg-primary/5 hover:bg-primary/10 hover:border-primary transition-all" onClick={() => { setShowActionPicker(false); setShowVoiceInput(true); }}>
                  <Mic className="w-10 h-10 text-primary" />
                  <span className="text-sm font-medium text-text">Voice Detail</span>
                  <span className="text-xs text-text-muted">"A T-shirt, 4 colors..."</span>
                </button>
                <button className="flex flex-col items-center gap-3 p-6 rounded-xl border-2 border-accent/20 bg-accent/5 hover:bg-accent/10 hover:border-accent transition-all" onClick={() => { setShowActionPicker(false); setMagicEditImage(imagePreview); setShowPhotoEditor(true); }}>
                  <Wand2 className="w-10 h-10 text-accent" />
                  <span className="text-sm font-medium text-text">Magic Photo Edit</span>
                  <span className="text-xs text-text-muted">Edit photo &amp; auto-detect</span>
                </button>
              </div>
            </div>
            <div className="px-6 pb-6">
              <button onClick={() => { setShowActionPicker(false); }} className="w-full py-2.5 text-sm theme-btn-secondary">
                Skip — I&apos;ll fill manually
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Voice Product Input / Voice-to-Catalog Pipeline ── */}
      {/* When an image is uploaded, use the full auto pipeline (BG+voice). */}
      {/* Otherwise, use the simpler voice-only input. */}
      {showVoiceInput && selectedImage ? (
        <VoiceToCatalogPipeline
          imageFile={selectedImage}
          onComplete={(data) => {
            // Apply voice + BG A/B test results
            const voiceData = data.extractedData;
            handleVoiceData({
              product_name: voiceData.product_name,
              category: voiceData.category,
              subcategory: voiceData.subcategory,
              colors: voiceData.colors,
              fabric: voiceData.fabric,
              print_text: voiceData.print_text,
              description: voiceData.description,
              suggested_tags: voiceData.suggested_tags,
              variants: voiceData.variants,
              stock_hints: voiceData.stock_hints,
              quantity: voiceData.quantity,
              price: voiceData.price,
            });
            // Apply BG result if available
            if (data.bgBlob) {
              const blobUrl = URL.createObjectURL(data.bgBlob);
              if (processedImageUrl) URL.revokeObjectURL(processedImageUrl);
              setProcessedImageBlob(data.bgBlob);
              setProcessedImageUrl(blobUrl);
              setActiveBgModel(data.bgWinner);
              setImagePreview(blobUrl);
            }
            setShowVoiceInput(false);
          }}
          onClose={() => setShowVoiceInput(false)}
        />
      ) : showVoiceInput ? (
        <VoiceProductInput
          onDataExtracted={handleVoiceData}
          onClose={() => { setShowVoiceInput(false); }}
        />
      ) : null}

      {/* ── Variant Matrix modal ── */}
      {showVariantMatrix && (
        <div className="fixed inset-0 z-50 flex items-center justify-center theme-overlay p-4" onClick={() => { matrixOpenedRef.current = false; setShowVariantMatrix(false); }} role="dialog" aria-modal="true">
          <div className="glass-panel border rounded-2xl shadow-2xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto p-6" onClick={(e) => e.stopPropagation()}>
            <SmartVariantMatrix
              colors={variantTypes.includes('color') ? variantOptions.color || [] : []}
              sizes={variantTypes.includes('size') ? variantOptions.size || ['S', 'M', 'L', 'XL'] : ['One Size']}
              initialValues={matrixValues}
              onChange={(vals) => {
                setMatrixValues(vals);
                // Keep variant types/options in sync.
                const colors = Object.keys(vals);
                const sizes = colors.length ? Object.keys(vals[colors[0]] || {}) : [];
                setVariantOptions((p) => ({ ...p, color: colors, size: sizes }));
                if (!variantTypes.includes('color') && colors.length) setVariantTypes((t) => [...t, 'color']);
                if (!variantTypes.includes('size') && sizes.length) setVariantTypes((t) => [...t, 'size']);
              }}
              onTotalChange={() => {}}
            />
            <button onClick={() => { matrixOpenedRef.current = false; setShowVariantMatrix(false); setShowSpecsSelector(true); }}
              className="mt-4 w-full py-2.5 theme-btn-primary rounded-xl text-sm font-medium">
              Done — Continue to Specs
            </button>
          </div>
        </div>
      )}

      {/* ── Specs Selector modal ── */}
      {showSpecsSelector && (
        <div className="fixed inset-0 z-50 flex items-center justify-center theme-overlay p-4" onClick={() => setShowSpecsSelector(false)} role="dialog" aria-modal="true">
          <div className="glass-panel border rounded-2xl shadow-2xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto p-6" onClick={(e) => e.stopPropagation()}>
            <ProductSpecsSelector
              category={formData.category}
              preselected={selectedSpecs}
              onChange={(specs) => {
                setSelectedSpecs(specs);
                const allLabels: string[] = [];
                Object.values(specs).forEach(arr => arr.forEach(s => allLabels.push(s)));
                setFormData(prev => ({ ...prev, tags: allLabels.join(', ') }));
              }}
            />
            <button onClick={() => { setShowSpecsSelector(false); setShowPricingPanel(true); }}
              className="mt-4 w-full py-2.5 theme-btn-primary rounded-xl text-sm font-medium">
              Next — Finalize Listing
            </button>
          </div>
        </div>
      )}

      {/* ── Photo Editor Modal ── */}
      {showPhotoEditor && magicEditImage && (
        <PhotoEditorModal
          src={magicEditImage}
          fileName="product_photo"
          onApply={(editedFile) => {
            setShowPhotoEditor(false);
            if (processedImageUrl) URL.revokeObjectURL(processedImageUrl);
            const url = URL.createObjectURL(editedFile);
            setProcessedImageBlob(editedFile);
            setProcessedImageUrl(url);
            setImagePreview(url);
            // Auto-trigger AI analysis after edit
            setTimeout(() => handleAiFill(), 300);
          }}
          onClose={() => {
            setShowPhotoEditor(false);
            setShowActionPicker(false);
            // Reset orchestrator phase back to ai_results
            goToAiResults();
          }}
        />
      )}

      {/* ── Smart Pricing Panel modal ── */}
      {showPricingPanel && (
        <div className="fixed inset-0 z-50 flex items-center justify-center theme-overlay p-4" onClick={() => setShowPricingPanel(false)} role="dialog" aria-modal="true">
          <div className="glass-panel border rounded-2xl shadow-2xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto p-6" onClick={(e) => e.stopPropagation()}>
            <SmartPricingPanel
              basePrice={formData.price}
              onPriceChange={(price) => setFormData(f => ({ ...f, price }))}
              aiSuggestedPrice={aiPriceRange ? {
                min: aiPriceRange.min,
                max: aiPriceRange.max,
                suggested: (aiPriceRange.min + aiPriceRange.max) / 2,
              } : undefined}
              onPublish={async () => {
                // One-click publish: this panel already shows the full preview,
                // so skip the redundant verification modal and submit directly.
                setShowPricingPanel(false);
                setPublishing(true);
                await submitProduct();
                setPublishing(false);
              }}
              onSaveDraft={() => { saveDraft(false); setShowPricingPanel(false); }}
              onEditDetails={() => { setShowPricingPanel(false); }}
              onEditImages={() => { setShowPricingPanel(false); }}
              publishing={publishing}
            />
          </div>
        </div>
      )}

      {/* ── Verification modal ── */}
      {showVerification && (
        <VerificationPopup
          summary={verificationSummary}
          onEditDetails={() => { setShowVerification(false); }}
          onUpload={() => { setShowVerification(false); submitProduct(); }}
          onEditImages={() => { setShowVerification(false); if (!selectedImage) setShowMediaUpload(true); }}
          onClose={() => setShowVerification(false)}
        />
      )}

      {/* ── Publish Success modal ── */}
      {showSuccess && publishResult && (
        <ProductPublishSuccess
          productId={publishResult.id}
          productName={publishResult.name}
          listingScore={listingScore}
          countries={listingCountries}
          onAddAnother={() => { setShowSuccess(false); window.location.reload(); }}
          onClose={() => setShowSuccess(false)}
        />
      )}

      {/* UPLOAD ORCHESTRATOR — 5-Step Modal Flow */}
      {/* Step 2: Processing — Dual progress bars for BG removal + AI analysis */}
      {uploadState.phase === 'processing' && (
        <ProcessingModal
          bgProgress={uploadState.processingProgress.bg}
          aiProgress={uploadState.processingProgress.ai}
          bgModel={uploadState.bgModel}
          error={uploadState.processingError}
          onRetry={() => {
            if (uploadState.image) orchestratorSetImage(uploadState.image, uploadState.imagePreview || '');
          }}
          onClose={() => reset()}
        />
      )}

      {/* Photo Edit — Uses existing PhotoEditorModal, returns to ai_results */}
      {uploadState.phase === 'photo_edit' && !showPhotoEditor && (
        // PhotoEditorModal is shown via showPhotoEditor state.
        // When closed, go back to ai_results.
        <div style={{ display: 'none' }} />
      )}

      {/* Step 3: AI Results — Review and edit AI-filled fields */}
      {uploadState.phase === 'ai_results' && (
        <AIResultsModal
          state={uploadState}
          onUpdateField={updateField}
          onNext={() => {
            if (uploadState.name) setFormData(f => ({ ...f, name: uploadState.name }));
            if (uploadState.category) setFormData(f => ({ ...f, category: uploadState.category }));
            if (uploadState.description) setFormData(f => ({ ...f, description: uploadState.description }));
            if (uploadState.price) setFormData(f => ({ ...f, price: uploadState.price }));
            if (uploadState.tags.length) setFormData(f => ({ ...f, tags: uploadState.tags.join(', ') }));
            if (uploadState.subcategory) setFormData(f => ({ ...f, subcategory: uploadState.subcategory }));
            if (uploadState.brand) setFormData(f => ({ ...f, brand: uploadState.brand }));
            // Go to quantity step if we have colors, otherwise go straight to verify
            if (uploadState.colors.length > 0 && uploadState.sizes.length > 0) {
              goToQuantity();
            } else {
              goToVerify();
            }
          }}
          onPhotoEdit={() => {
            if (uploadState.processedImageUrl) {
              setMagicEditImage(uploadState.processedImageUrl);
              setShowPhotoEditor(true);
            } else if (imagePreview) {
              setMagicEditImage(imagePreview);
              setShowPhotoEditor(true);
            }
            goToPhotoEdit();
          }}
          onClose={() => reset()}
        />
      )}

      {/* Step 4: Quantity — Per-color cycling quantity popups */}
      {uploadState.phase === 'quantity' &&
        uploadState.colors.length > 0 &&
        uploadState.currentColorIndex < uploadState.colors.length && (
        <QuantityModal
          color={uploadState.colors[uploadState.currentColorIndex]}
          colorIndex={uploadState.currentColorIndex}
          totalColors={uploadState.colors.length}
          sizes={uploadState.sizes}
          initialQuantities={uploadState.quantityMap[uploadState.colors[uploadState.currentColorIndex]] || {}}
          onSave={(qty) => setQuantityForColor(uploadState.colors[uploadState.currentColorIndex], qty)}
          onNext={advanceColorStep}
          onSkip={() => advanceColorStep()}
        />
      )}

      {/* Step 5: Verify & Publish — Final review before publishing */}
      {uploadState.phase === 'verify' && (
        <VerifyPublishModal
          productName={uploadState.name || formData.name}
          category={uploadState.category || formData.category}
          colors={uploadState.colors}
          variantsSummary={`${uploadState.colors.length > 0 ? uploadState.colors.length + ' colors' : ''}${uploadState.colors.length > 0 && uploadState.sizes.length > 0 ? ' x ' : ''}${uploadState.sizes.length > 0 ? uploadState.sizes.length + ' sizes' : uploadState.sizes.length === 0 && uploadState.colors.length === 0 ? 'None' : ''}`}
          totalStock={uploadState.stockTotal}
          price={uploadState.price || formData.price}
          description={uploadState.description || formData.description}
          imagesCount={selectedImage ? 1 : 0}
          hasVideo={!!videoFile}
          tags={uploadState.tags.length > 0 ? uploadState.tags : formData.tags.split(',').map(t => t.trim()).filter(Boolean)}
          imagePreview={imagePreview}
          processedImageUrl={uploadState.processedImageUrl}
          publishing={publishing}
          onEditDetails={() => goToAiResults()}
          onEditImages={() => {
            if (uploadState.processedImageUrl) {
              setMagicEditImage(uploadState.processedImageUrl);
              setShowPhotoEditor(true);
            } else if (imagePreview) {
              setMagicEditImage(imagePreview);
              setShowPhotoEditor(true);
            }
          }}
          onPublish={async () => {
            // Sync orchestrator state into formData before submitting
            if (uploadState.name) setFormData(f => ({ ...f, name: uploadState.name }));
            if (uploadState.category) setFormData(f => ({ ...f, category: uploadState.category }));
            if (uploadState.description) setFormData(f => ({ ...f, description: uploadState.description }));
            if (uploadState.price) setFormData(f => ({ ...f, price: uploadState.price }));
            if (uploadState.tags.length) setFormData(f => ({ ...f, tags: uploadState.tags.join(', ') }));
            if (uploadState.subcategory) setFormData(f => ({ ...f, subcategory: uploadState.subcategory }));
            if (uploadState.brand) setFormData(f => ({ ...f, brand: uploadState.brand }));
            setPublishing(true);
            await submitProduct();
            setPublishing(false);
          }}
          onClose={() => reset()}
        />
      )}

    </SupplierLayout>
  );
}
