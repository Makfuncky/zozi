"""Quick batch test of AI suggest endpoint for all product groups."""
import os

import requests

BASE = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\documents\snap\Product"

GROUPS = {
    "bar_bra": ["bar_1.jpg", "bar_2.webp"],
    "bikini": ["bikini_1.webp", "bikini_2.webp", "bikini_3.webp"],
    "lingerie": ["lingerie_1.avif", "lingerie_2.webp", "lingerie_3.jpg"],
    "furniture_cupboard": ["1012-750x650.jpg", "brown-rectangular-wooden-cupboard.jpg", "4-750x650.jpg"],
    "sofa": ["KIYOMI-GREY-MAIN-1.jpg", "Thea+3+Seater+Sofa+with+Reversible+Chaise.webp"],
    "beauty": ["main-banner-csk.webp"],
}


def main() -> None:
    token_res = requests.post(
        "http://localhost:8000/auth/login",
        data={"username": "supplier@zozi.com", "password": "supplier123"},
    )
    token = token_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    for name, files in GROUPS.items():
        form_files = []
        try:
            for i, filename in enumerate(files):
                path = os.path.join(BASE, filename)
                if not os.path.exists(path):
                    print(f"[{name}] MISSING: {filename}")
                    continue
                key = "image" if i == 0 else "images"
                form_files.append((key, (filename, open(path, "rb"), "image/jpeg")))

            data = {"name": "", "description": ""}
            response = requests.post(
                "http://localhost:8000/ai/suggest",
                data=data,
                files=form_files,
                headers=headers,
            )
            if response.ok:
                payload = response.json()
                print(f"[{name}]")
                print(f"  name: {payload.get('name')}")
                print(f"  category: {payload.get('category')}")
                print(f"  color: {payload.get('color')}")
                print(f"  color_candidates: {payload.get('color_candidates')}")
                tags = payload.get("tags_string", "")
                print(f"  tags: {tags[:100]}")
                print(f"  variant_template: {payload.get('variant_template')}")
                print(f"  variant_options: {payload.get('variant_options')}")
                print(f"  material_suggestions: {payload.get('material_suggestions')}")
                desc = payload.get("description", "")
                print(f"  description: {desc[:150]}...")
                print()
            else:
                print(f"[{name}] FAILED: {response.status_code} {response.text[:200]}")
                print()
        finally:
            for _, file_data in form_files:
                file_data[1].close()


if __name__ == "__main__":
    main()
