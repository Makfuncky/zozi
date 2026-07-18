import asyncio, io, json
from PIL import Image
from services.ai_variant_config import analyze_product_image

files = ["sample_sneaker.jpg", "sample_tshirt.jpg", "sample_watch.jpg"]

async def main():
    for fn in files:
        try:
            data = open(fn, "rb").read()
        except Exception:
            continue
        print("=" * 70)
        print("IMAGE:", fn)
        try:
            r = await analyze_product_image(data, filename=fn, generate_copy=True, use_vision=True)
        except Exception as e:
            import traceback; traceback.print_exc(); continue
        print("source        :", r.get("source"))
        print("name          :", r.get("product_name_hint"))
        print("category      :", r.get("suggested_category"))
        print("subcategory   :", r.get("suggested_subcategory"))
        print("brand         :", r.get("suggested_brand"))
        print("attributes    :", r.get("detected_attributes"))
        print("description   :", str(r.get("product_description"))[:200])
        print("tags          :", r.get("suggested_tags"))
        print("variants      :", r.get("suggested_variants"))
        print("variant_options:", r.get("variant_options"))
        print("variant_labels :", r.get("variant_labels"))
        print("english_title :", r.get("english_title"))
        print("arabic_title  :", r.get("arabic_title"))

asyncio.run(main())

