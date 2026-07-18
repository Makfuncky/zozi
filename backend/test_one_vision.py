import asyncio, io, json, sys
from PIL import Image
from services.ai_variant_config import analyze_product_image, _ollama_chat
import base64

fn = "sample_sneaker.jpg"
data = open(fn, "rb").read()
print("loaded", fn, len(data), flush=True)

async def quick():
    b64 = base64.b64encode(data).decode()
    out = await _ollama_chat('moondream:latest', 'Describe this product photo in 2 sentences.', images=[b64], num_predict=200, temperature=0.2)
    print("MOONDREAM:", repr(out)[:400], flush=True)

asyncio.run(quick())
print("done", flush=True)

