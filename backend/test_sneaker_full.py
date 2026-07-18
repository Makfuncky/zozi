import asyncio, io, json, sys
from services.ai_variant_config import analyze_product_image

fn = "sample_sneaker.jpg"
data = open(fn, "rb").read()
print("loaded", fn, flush=True)

async def main():
    try:
        r = await analyze_product_image(data, filename=fn, generate_copy=True, use_vision=True)
    except Exception as e:
        import traceback; traceback.print_exc(); return
    print("source        :", r.get("source"), flush=True)
    print("name          :", r.get("product_name_hint"), flush=True)
    print("category      :", r.get("suggested_category"), flush=True)
    print("subcategory   :", r.get("suggested_subcategory"), flush=True)
    print("brand         :", r.get("suggested_brand"), flush=True)
    print("attributes    :", r.get("detected_attributes"), flush=True)
    print("description   :", str(r.get("product_description"))[:220], flush=True)
    print("tags          :", r.get("suggested_tags"), flush=True)
    print("variants      :", r.get("suggested_variants"), flush=True)
    print("variant_options:", r.get("variant_options"), flush=True)
    print("variant_labels :", r.get("variant_labels"), flush=True)
    print("english_title :", r.get("english_title"), flush=True)
    print("arabic_title  :", repr(r.get("arabic_title")), flush=True)

asyncio.run(main())
print("DONE", flush=True)

