from __future__ import annotations

import os
import argparse
import importlib.util
import json
import re
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
PRODUCT_DIR = REPO_ROOT / "documents" / "snap" / "Product"
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".avif"}

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from fastapi.testclient import TestClient


class SmokeFailure(RuntimeError):
    pass


def print_section(title: str) -> None:
    print(f"\n=== {title} ===")


def load_app() -> Any:
    module_spec = importlib.util.spec_from_file_location("zozi_backend_main", BACKEND_ROOT / "main.py")
    if module_spec is None or module_spec.loader is None:
        raise SmokeFailure("Unable to load backend main module")
    main = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(main)
    return main.app


def login(client: TestClient, username: str, password: str) -> dict[str, str]:
    response = client.post(
        "/auth/login",
        data={"username": username, "password": password},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    if response.status_code != 200:
        raise SmokeFailure(f"Login failed for {username}: HTTP {response.status_code} {response.text}")
    data = response.json()
    return {"Authorization": f"Bearer {data['access_token']}"}


def register_or_login(client: TestClient, email: str, username: str, password: str) -> dict[str, str]:
    response = client.post(
        "/auth/register",
        json={"email": email, "username": username, "password": password, "role": "supplier"},
    )
    if response.status_code not in (200, 201, 400):
        raise SmokeFailure(f"Register failed for {email}: HTTP {response.status_code} {response.text}")
    return login(client, email, password)


def existing_path(name: str) -> Path | None:
    path = PRODUCT_DIR / name
    return path if path.exists() else None


def build_groups() -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    covered_files: set[str] = set()

    def add_group(
        group_id: str,
        label: str,
        file_names: list[str],
        expected_category: str | None = None,
        expected_variant: str | None = None,
        expected_colors: list[str] | None = None,
        expected_name_keywords: list[str] | None = None,
        expected_description_keywords: list[str] | None = None,
    ) -> None:
        files = [existing_path(name) for name in file_names]
        resolved = [path for path in files if path is not None]
        if not resolved:
            return
        for path in resolved:
            covered_files.add(path.resolve().as_posix())
        groups.append(
            {
                "id": group_id,
                "label": label,
                "files": resolved,
                "expected_category": expected_category,
                "expected_variant": expected_variant,
                "expected_colors": expected_colors or [],
                "expected_name_keywords": expected_name_keywords or [],
                "expected_description_keywords": expected_description_keywords or [],
            }
        )

    add_group(
        "bar",
        "Bar / bra set",
        ["bar_1.jpg", "bar_2.webp"],
        expected_category="Fashion",
        expected_variant="apparel",
        expected_name_keywords=["bra"],
        expected_description_keywords=["fashion", "bra"],
    )
    add_group(
        "bikini",
        "Bikini set",
        ["bikini_1.webp", "bikini_2.webp", "bikini_3.webp", "bikini_4.webp", "bikini_5.webp"],
        expected_category="Fashion",
        expected_variant="apparel",
        expected_colors=["White"],
        expected_name_keywords=["bikini"],
        expected_description_keywords=["fashion", "bikini"],
    )
    add_group(
        "lingerie",
        "Lingerie set",
        ["lingerie_1.avif", "lingerie_2.webp", "lingerie_3.jpg", "look-book-boobs.avif"],
        expected_category="Fashion",
        expected_variant="apparel",
        expected_colors=["Black"],
        expected_name_keywords=["lingerie"],
        expected_description_keywords=["fashion", "lingerie"],
    )
    add_group(
        "tshirt",
        "T-shirt set",
        ["T-shirt.jpg", "T-shirt_2.webp", "T-shirt_3.webp", "T-shirt_4.jpg", "T-shirt_5.webp"],
        expected_category="Fashion",
        expected_variant="apparel",
        expected_name_keywords=["shirt", "t shirt"],
        expected_description_keywords=["fashion", "shirt"],
    )
    add_group(
        "cupboard",
        "Wooden cupboard",
        ["brown-rectangular-wooden-cupboard.jpg"],
        expected_category="Furniture",
        expected_variant="home-furniture",
        expected_colors=["Brown"],
        expected_name_keywords=["cupboard"],
        expected_description_keywords=["furniture", "cupboard"],
    )
    add_group(
        "chevron-wardrobe",
        "Chevron wardrobe",
        ["1012-750x650.jpg"],
        expected_category="Furniture",
        expected_variant="home-furniture",
        expected_colors=["Brown"],
        expected_name_keywords=["wardrobe", "cupboard"],
        expected_description_keywords=["furniture", "wardrobe"],
    )
    add_group(
        "gray-wardrobe",
        "Gray wardrobe",
        ["4-750x650.jpg"],
        expected_category="Furniture",
        expected_variant="home-furniture",
        expected_colors=["Gray", "Silver"],
        expected_name_keywords=["wardrobe", "cupboard"],
        expected_description_keywords=["furniture", "wardrobe"],
    )
    add_group(
        "kiyomi-sofa",
        "Kiyomi sofa",
        ["KIYOMI-GREY-MAIN-1.jpg"],
        expected_category="Furniture",
        expected_variant="home-furniture",
        expected_colors=["Gray"],
        expected_name_keywords=["sofa"],
        expected_description_keywords=["furniture", "sofa"],
    )
    add_group(
        "thea-sofa",
        "Thea sofa",
        ["Thea+3+Seater+Sofa+with+Reversible+Chaise.webp"],
        expected_category="Furniture",
        expected_variant="home-furniture",
        expected_name_keywords=["sofa", "chaise"],
        expected_description_keywords=["furniture", "sofa"],
    )
    add_group(
        "neutral-chaise-sofa",
        "Neutral chaise sofa",
        ["168372845-163452422-HC01062021_01-2100.webp"],
        expected_category="Furniture",
        expected_variant="home-furniture",
        expected_colors=["Beige", "White", "Silver"],
        expected_name_keywords=["sofa", "chaise"],
        expected_description_keywords=["furniture", "sofa"],
    )
    add_group(
        "skincare-banner",
        "Skincare banner",
        ["main-banner-csk.webp"],
        expected_category="Beauty",
        expected_name_keywords=["skin", "skincare", "elixir"],
        expected_description_keywords=["beauty", "skin"],
    )
    add_group(
        "ferrari-sunglasses-black",
        "Ferrari sunglasses black batch",
        [
            "WhatsApp Image 2026-03-28 at 21.43.24.jpeg",
            "WhatsApp Image 2026-03-28 at 21.43.24 (1).jpeg",
            "WhatsApp Image 2026-03-28 at 21.43.24 (2).jpeg",
            "WhatsApp Image 2026-03-28 at 21.43.24 (3).jpeg",
            "WhatsApp Image 2026-03-28 at 21.43.24 (4).jpeg",
            "WhatsApp Image 2026-03-28 at 21.43.24 (5).jpeg",
        ],
        expected_category="Accessories",
        expected_variant="universal",
        expected_colors=["Black"],
        expected_name_keywords=["sunglasses"],
        expected_description_keywords=["accessor", "sunglasses"],
    )
    add_group(
        "ferrari-sunglasses-brown",
        "Ferrari sunglasses brown batch",
        [
            "WhatsApp Image 2026-03-28 at 21.43.25.jpeg",
            "WhatsApp Image 2026-03-28 at 21.43.25 (1).jpeg",
            "WhatsApp Image 2026-03-28 at 21.43.25 (2).jpeg",
            "WhatsApp Image 2026-03-28 at 21.43.25 (3).jpeg",
        ],
        expected_category="Accessories",
        expected_variant="universal",
        expected_colors=["Brown", "Black"],
        expected_name_keywords=["sunglasses"],
        expected_description_keywords=["accessor", "sunglasses"],
    )
    add_group(
        "casio-watch-silver-batch",
        "Casio watch silver batch",
        [
            "WhatsApp Image 2026-03-28 at 21.43.34.jpeg",
            "WhatsApp Image 2026-03-28 at 21.43.34 (1).jpeg",
            "WhatsApp Image 2026-03-28 at 21.43.34 (2).jpeg",
        ],
        expected_category="Accessories",
        expected_variant="universal",
        expected_colors=["Silver", "Black"],
        expected_name_keywords=["watch"],
        expected_description_keywords=["accessor", "watch"],
    )
    add_group(
        "casio-watch-mixed-batch",
        "Casio watch mixed batch",
        [
            "WhatsApp Image 2026-03-28 at 21.43.35.jpeg",
            "WhatsApp Image 2026-03-28 at 21.43.35 (1).jpeg",
            "WhatsApp Image 2026-03-28 at 21.43.35 (2).jpeg",
            "WhatsApp Image 2026-03-28 at 21.43.35 (3).jpeg",
            "WhatsApp Image 2026-03-28 at 21.43.35 (4).jpeg",
            "WhatsApp Image 2026-03-28 at 21.43.35 (5).jpeg",
        ],
        expected_category="Accessories",
        expected_variant="universal",
        expected_colors=["Blue", "White", "Silver", "Black"],
        expected_name_keywords=["watch"],
        expected_description_keywords=["accessor", "watch"],
    )
    add_group(
        "casio-watch-silver-single",
        "Casio watch silver single",
        ["WhatsApp Image 2026-03-28 at 21.43.36.jpeg"],
        expected_category="Accessories",
        expected_variant="universal",
        expected_colors=["Silver", "Black"],
        expected_name_keywords=["watch"],
        expected_description_keywords=["accessor", "watch"],
    )
    add_group(
        "necklace-v-pendant",
        "V pendant necklace batch",
        [
            "WhatsApp Image 2026-03-28 at 21.45.00.jpeg",
            "WhatsApp Image 2026-03-28 at 21.45.00 (1).jpeg",
            "WhatsApp Image 2026-03-28 at 21.45.00 (2).jpeg",
            "WhatsApp Image 2026-03-28 at 21.45.00 (3).jpeg",
        ],
        expected_category="Accessories",
        expected_variant="universal",
        expected_colors=["Silver", "White"],
        expected_name_keywords=["necklace"],
        expected_description_keywords=["accessor", "necklace"],
    )
    add_group(
        "necklace-angel-pendant",
        "Angel pendant necklace batch",
        [
            "WhatsApp Image 2026-03-28 at 21.45.01.jpeg",
            "WhatsApp Image 2026-03-28 at 21.45.01 (1).jpeg",
            "WhatsApp Image 2026-03-28 at 21.45.01 (2).jpeg",
            "WhatsApp Image 2026-03-28 at 21.45.01 (3).jpeg",
            "WhatsApp Image 2026-03-28 at 21.45.01 (4).jpeg",
        ],
        expected_category="Accessories",
        expected_variant="universal",
        expected_colors=["Silver", "White"],
        expected_name_keywords=["necklace"],
        expected_description_keywords=["accessor", "necklace"],
    )

    whatsapp_groups: dict[str, list[Path]] = defaultdict(list)
    pattern = re.compile(r"^(WhatsApp Image \d{4}-\d{2}-\d{2} at \d{2}\.\d{2}\.\d{2})")
    for path in sorted(PRODUCT_DIR.iterdir()):
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        match = pattern.match(path.name)
        if match:
            whatsapp_groups[match.group(1)].append(path)

    for group_name, files in sorted(whatsapp_groups.items()):
        if files and all(path.resolve().as_posix() in covered_files for path in files):
            continue
        groups.append(
            {
                "id": re.sub(r"[^a-z0-9]+", "-", group_name.lower()).strip("-"),
                "label": group_name,
                "files": files,
                "expected_category": None,
                "expected_variant": None,
                "expected_colors": [],
                "expected_name_keywords": [],
                "expected_description_keywords": [],
            }
        )

    return groups


def request_ai_suggestions(client: TestClient, headers: dict[str, str], paths: list[Path]) -> dict[str, Any]:
    files: Any
    if len(paths) == 1:
        path = paths[0]
        with path.open("rb") as handle:
            files = {"image": (path.name, handle.read(), "application/octet-stream")}
            response = client.post(
                "/ai/suggest",
                data={"name": "", "description": ""},
                files=files,
                headers=headers,
            )
    else:
        file_payload = []
        for path in paths:
            with path.open("rb") as handle:
                file_payload.append(("images", (path.name, handle.read(), "application/octet-stream")))
        response = client.post(
            "/ai/suggest",
            data={"name": "", "description": ""},
            files=file_payload,
            headers=headers,
        )

    if response.status_code != 200:
        raise SmokeFailure(f"AI suggest failed for {[path.name for path in paths]}: HTTP {response.status_code} {response.text}")
    payload = response.json()
    if not isinstance(payload, dict):
        raise SmokeFailure(f"Unexpected AI response for {[path.name for path in paths]}: {payload!r}")
    return payload


def primary_color(payload: dict[str, Any]) -> str:
    candidates = payload.get("color_candidates") or []
    if isinstance(candidates, list) and candidates:
        return str(candidates[0])
    color = payload.get("color") or ""
    if isinstance(color, str) and color.strip():
        return color.split(",")[0].strip()
    return ""


def analyze_result(group: dict[str, Any], payload: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    actual_name = str(payload.get("name") or "").strip()
    actual_description = str(payload.get("description") or "").strip()

    if not actual_name:
        errors.append("Missing inferred product name")
    if not actual_description:
        errors.append("Missing generated description")
    if not isinstance(payload.get("tags"), list) or len(payload.get("tags") or []) < 2:
        warnings.append("Tag list is sparse")

    expected_category = group.get("expected_category")
    actual_category = payload.get("category")
    if expected_category and actual_category != expected_category:
        warnings.append(f"Expected category {expected_category}, got {actual_category}")

    expected_variant = group.get("expected_variant")
    actual_variant = payload.get("variant_template")
    if expected_variant and actual_variant != expected_variant:
        warnings.append(f"Expected variant template {expected_variant}, got {actual_variant}")

    expected_colors = group.get("expected_colors") or []
    actual_primary_color = primary_color(payload)
    if expected_colors and actual_primary_color not in expected_colors:
        warnings.append(f"Expected color in {expected_colors}, got {actual_primary_color or 'none'}")

    expected_name_keywords = [str(value).lower() for value in (group.get("expected_name_keywords") or []) if str(value).strip()]
    if expected_name_keywords and not any(keyword in actual_name.lower() for keyword in expected_name_keywords):
        warnings.append(f"Expected name to mention one of {expected_name_keywords}, got {actual_name or 'none'}")

    expected_description_keywords = [str(value).lower() for value in (group.get("expected_description_keywords") or []) if str(value).strip()]
    if expected_description_keywords and not any(keyword in actual_description.lower() for keyword in expected_description_keywords):
        warnings.append(
            f"Expected description to mention one of {expected_description_keywords}, got {actual_description[:120] or 'none'}"
        )

    if actual_category == "Fashion" and actual_variant not in {"apparel", "kids", "footwear"}:
        warnings.append(f"Fashion item resolved to variant template {actual_variant}")
    if actual_category == "Furniture" and actual_variant != "home-furniture":
        warnings.append(f"Furniture item resolved to variant template {actual_variant}")

    return errors, warnings


def compact_result(group: dict[str, Any], payload: dict[str, Any], errors: list[str], warnings: list[str]) -> dict[str, Any]:
    status = "FAIL" if errors else "WARN" if warnings else "OK"
    return {
        "id": group["id"],
        "label": group["label"],
        "status": status,
        "files": [path.name for path in group["files"]],
        "expectations": {
            "category": group.get("expected_category"),
            "variant_template": group.get("expected_variant"),
            "colors": group.get("expected_colors") or [],
            "name_keywords": group.get("expected_name_keywords") or [],
            "description_keywords": group.get("expected_description_keywords") or [],
        },
        "result": {
            "name": payload.get("name"),
            "category": payload.get("category"),
            "color": payload.get("color"),
            "color_candidates": payload.get("color_candidates"),
            "tags": payload.get("tags"),
            "material_suggestions": payload.get("material_suggestions"),
            "variant_template": payload.get("variant_template"),
            "variant_options": payload.get("variant_options"),
            "description": payload.get("description"),
        },
        "errors": errors,
        "warnings": warnings,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run grouped AI image suggestion smoke coverage against product snapshot assets.")
    parser.add_argument("--output", default="artifacts/ai_image_group_smoke.json", help="Path to write the JSON smoke summary.")
    parser.add_argument("--limit", type=int, default=0, help="Optional number of groups to run for faster iteration.")
    parser.add_argument("--strict", action="store_true", help="Exit with code 1 if warnings are present.")
    args = parser.parse_args()

    if not PRODUCT_DIR.exists():
        raise SmokeFailure(f"Product snapshot directory not found: {PRODUCT_DIR}")

    print_section("Load App")
    app = load_app()
    run_tag = str(int(time.time()))
    email = f"ai.image.smoke.{run_tag}@zozi.test"
    username = f"ai_image_smoke_{run_tag}"
    password = os.environ.get("ZOZI_SMOKE_PASSWORD", "AiImageSmoke123!")

    groups = build_groups()
    if args.limit > 0:
        groups = groups[: args.limit]
    if not groups:
        raise SmokeFailure("No image groups were discovered for the smoke run")

    results: list[dict[str, Any]] = []
    total_errors = 0
    total_warnings = 0

    with TestClient(app, raise_server_exceptions=True) as client:
        print_section("Auth")
        headers = register_or_login(client, email, username, password)

        print_section("Groups")
        for index, group in enumerate(groups, start=1):
            payload = request_ai_suggestions(client, headers, group["files"])
            errors, warnings = analyze_result(group, payload)
            total_errors += len(errors)
            total_warnings += len(warnings)
            result = compact_result(group, payload, errors, warnings)
            results.append(result)

            status = "FAIL" if errors else "WARN" if warnings else "OK"
            print(
                f"[{index:02d}/{len(groups):02d}] {status} {group['label']}: "
                f"{payload.get('name')} | {payload.get('category')} | {payload.get('color')} | {payload.get('variant_template')}"
            )
            for item in errors:
                print(f"  error: {item}")
            for item in warnings:
                print(f"  warning: {item}")

    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "product_dir": str(PRODUCT_DIR),
        "group_count": len(results),
        "curated_group_count": sum(1 for group in results if any((group.get("expectations") or {}).values())),
        "error_count": total_errors,
        "warning_count": total_warnings,
        "results": results,
    }

    output_path = REPO_ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print_section("Summary")
    print(f"Wrote {output_path}")
    print(f"Groups: {len(results)} | Errors: {total_errors} | Warnings: {total_warnings}")

    if total_errors or (args.strict and total_warnings):
        raise SystemExit(1)


if __name__ == "__main__":
    main()