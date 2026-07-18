"""Check .env, installed packages, and HF model availability."""
import sys, os, importlib
import requests as req

# === A. .env HF_API_TOKEN ===
print("=== A. .env HF/AI keys ===")
env_path = ".env"
if os.path.exists(env_path):
    with open(env_path) as f:
        lines = [l.strip() for l in f if any(k in l.upper() for k in ["HF", "OPENAI", "AI_", "_AI"])]
    msg = str(lines) if lines else "none found"
    print(f"  HF/AI env lines: {msg}")
else:
    print("  .env file not found")

# === B. Installed packages ===
print("=== B. Installed AI/image packages ===")
pkgs = ["PIL", "rembg", "gradio_client", "requests", "httpx", "torch", "onnxruntime", "numpy"]
for p in pkgs:
    try:
        m = importlib.import_module(p)
        v = getattr(m, "__version__", "?")
        print(f"  {p}: YES  ({v})")
    except ImportError:
        print(f"  {p}: NOT installed")

# === C. HF Inference API — does the model support API at all? ===
print("=== C. HF Inference API model info ===")
models = {
    "briaai/RMBG-1.4": "Background removal",
    "sudo-ai/zero123-plus": "Multi-angle generation",
}
for model, desc in models.items():
    try:
        r = req.get(f"https://api-inference.huggingface.co/models/{model}", timeout=15)
        info = r.json() if r.headers.get("content-type","").startswith("application/json") else {}
        loaded = info.get("loaded", "?")
        pipeline = info.get("pipeline_tag", "?")
        print(f"  [{r.status_code}] {desc} ({model})")
        print(f"    pipeline_tag={pipeline}  loaded={loaded}")
        if r.status_code == 200 and not loaded:
            print(f"    => Model says 'loaded=false' — may need warm-up")
        elif r.status_code == 503:
            msg = info.get("error", "")
            estimated = info.get("estimated_time", "?")
            print(f"    => 503: {msg} | estimated_time={estimated}")
        elif r.status_code == 404:
            print(f"    => NOT available on free inference API")
    except Exception as e:
        print(f"  {desc}: network error - {e}")

# === D. zero123-plus Space ===
print("=== D. zero123-plus HF Space ===")
for url in [
    "https://huggingface.co/spaces/sudo-ai/zero123plus",
    "https://huggingface.co/sudo-ai/zero123-plus",
]:
    try:
        r2 = req.head(url, timeout=10, allow_redirects=True)
        print(f"  {url}")
        print(f"    => HTTP {r2.status_code}")
    except Exception as e:
        print(f"  {url}: error {e}")

# === E. What does RMBG-1.4 actually return? (check Accept headers) ===
print("=== E. RMBG-1.4 expected output format ===")
print("  Image Segmentation pipeline on HF returns JSON with mask data")
print("  BUT briaai/RMBG-1.4 may override to return binary PNG")
print("  Our code handles: content-type 'image/*' -> direct PNG")
print("  Missing handling: content-type 'application/json' -> parse mask")

