# AI Providers Integration Plan

## Context

The `backend/providers/` directory exists with `providers/ai/` subdirectory but contains **no `.py` source files** — only `__pycache__` compiled `.pyc` files from previously existing modules. The `services/ai/` directory contains shim files that re-export from `providers.*` modules. These shims will fail at runtime because the source files are missing.

The reference implementations exist in `Working_API/zozi_ai_image_service/` (6 bg removal model files: `br_05.py` through `br_13.py`) and `Working_API/zozi_ai_upload_session/` (variant config + upload auto script). The task is to consolidate all AI provider implementations into `backend/providers/`.

## Known Previous Modules (from pyc files)

Based on `__pycache__` contents, the `providers/` package previously had these modules:

**Root level:**
- `_base.py` — shared base classes
- `bg_remover.py` — background removal logic
- `config.py` — provider configuration
- `finance_ai.py` — finance AI tasks
- `image.py` — image processing pipeline
- `ocr.py` — OCR for bills/receipts
- `__init__.py` — package init

**`ai/` subpackage:**
- `vision.py` — vision model for product detection
- `text.py` — text model for variant/name extraction
- `__init__.py` — subpackage init

## Shim Import Map (must be preserved)

| Shim file | Imports from `providers.*` |
|---|---|
| `services/ai/bg_removal_service.py` | `providers.bg_remover`: `remove_background`, `remove_background_preset`, `remove_background_model`, `magic_erase`, `AVAILABLE_MODELS`, `VALID_STRATEGIES`, `CleanEdgeRefiner`, `SceneAnalyzer`, `HandRemover`, `HoleFiller`, `ThinPartHandler`, `HumanPreserver`, `EdgeShaver`, `GlobalBackgroundBleeder`, `ArtifactIsolator`, `FloatingArtifactRemover`, `BottomTextEraser`, `WoodBackgroundRemover` |
| `services/ai/image_ai_service.py` | `providers.image`: `remove_background`, `generate_angles` |
| `services/ai/ocr_parser.py` | `providers.ocr`: `parse_bill_text`, `parse_statement_csv` |
| `services/ai/llm_finance.py` | `providers.finance_ai`: `FinanceAIResult`, `parse_email_to_ledger`, `extract_bill_fields`, `suggest_reconciliation_match` |
| `services/ai/ai_variant_config.py` | `providers.ai.vision`: `suggest_price`, `normalize_category`, `VariantConfig`, `analyze_product_image` |
| `services/ai/ai_variant_config.py` | `providers.ai.text`: `_ollama_chat`, `_OLLAMA_TEXT_MODEL`, `_extract_json` |

## Target Structure

```
backend/providers/
├── __init__.py
├── _base.py                  # Shared base classes, config, utilities
├── bg_remover.py             # Image background removal (consolidated from br_05-br_13)
├── image.py                  # Image processing pipeline (from br_13 variant pipeline)
├── ocr.py                    # OCR for bills/receipts
├── finance_ai.py             # Finance AI tasks
├── text.py                   # Image-to-text / product description / variant finding
├── vision.py                 # Vision AI for product analysis
├── chatbot.py                # Chatbot with vectorization
├── search.py                 # Advance search engine + AI filtering
├── geo.py                    # IP detection + location + country detection
├── map.py                    # Map and location provider
├── country.py                # Country details search AI
├── analytics.py              # AI analysis for admin analytics
├── config.py                 # Provider configuration (was previously a pyc)
├── ai/
│   ├── __init__.py
│   ├── vision.py             # Vision model for product detection
│   └── text.py               # Text model for variant/name extraction
└── __pycache__/
```

## Tasks

### 1. Create `providers/__init__.py`
- Define package-level exports for all provider modules
- Re-export key classes/functions from each module
- Must match the previous `__init__.py` that existed (based on pyc)

### 2. Create `providers/_base.py`
- Shared base classes: `BaseProvider`, `BaseAIProvider`
- Shared config loading from `utils.config.settings`
- Shared error handling and logging utilities
- Shared HTTP client setup
- This module existed previously (pyc confirms `_base.cpython-310.pyc`)

### 3. Create `providers/config.py`
- Provider configuration dataclasses
- Model selection logic (which rembg model to use based on image type)
- Environment variable loading for API keys, model paths
- This module existed previously (pyc confirms `config.cpython-310.pyc`)

### 4. Create `providers/bg_remover.py`
- Consolidate all 6 reference files (`br_05.py` through `br_13.py`) into a single unified module
- Include all model variants: `isnet-general-use`, `u2net`, `birefnet-general-lite`, `u2net_cloth_seg`, `briaai-rmbg-1.4`, `birefnet-massive`, `birefnet-hrsod`, `sam2`, `vitmatte`
- Include all pipeline classes: `CleanEdgeRefiner`, `SceneAnalyzer`, `HandRemover`, `HoleFiller`, `ThinPartHandler`, `HumanPreserver`, `EdgeShaver`, `GlobalBackgroundBleeder`, `ArtifactIsolator`, `FloatingArtifactRemover`, `BottomTextEraser`, `WoodBackgroundRemover`
- Include `AVAILABLE_MODELS`, `VALID_STRATEGIES`
- Public API (must match shim expectations):
  - `remove_background(image_bytes, model=None, strategy=None)` -> returns processed image bytes
  - `remove_background_preset(image_bytes, preset_name)` -> uses preset model list
  - `remove_background_model(image_bytes, model_name)` -> uses specific model
  - `magic_erase(image_bytes, mask)` -> inpainting-based erasure
  - `AVAILABLE_MODELS` (list)
  - `VALID_STRATEGIES` (list)
  - All pipeline classes listed above

### 5. Create `providers/image.py`
- Image processing pipeline (from `br_13.py` variant testing pipeline)
- Public API (must match shim expectations):
  - `remove_background(image_bytes)` -> delegates to bg_remover
  - `generate_angles(image_bytes, product_name, category)` -> returns multi-angle descriptions
- Integrate with `bg_remover.py` for the actual removal logic

### 6. Create `providers/ocr.py`
- OCR system for scanning bills and receipts
- Public API (must match shim expectations):
  - `parse_bill_text(image_bytes)` -> extracted bill fields (date, total, vendor, items)
  - `parse_statement_csv(csv_bytes)` -> parsed financial statement data
- Use `services/ai/ocr_parser.py` as the shim reference for expected return types

### 7. Create `providers/finance_ai.py`
- Finance AI for task automation (email-to-ledger, bill field extraction, reconciliation)
- Public API (must match shim expectations):
  - `FinanceAIResult` (dataclass)
  - `parse_email_to_ledger(email_text)` -> ledger entries
  - `extract_bill_fields(image_bytes)` -> bill fields
  - `suggest_reconciliation_match(transaction, candidates)` -> best match
- Use `services/ai/llm_finance.py` as the shim reference

### 8. Create `providers/text.py`
- Image-to-text for product image reading, description, tags, product name identification, variant finding
- Public API (must match shim expectations):
  - `_ollama_chat(prompt, model)` -> LLM response
  - `_OLLAMA_TEXT_MODEL` (str constant)
  - `_extract_json(text)` -> parsed JSON from LLM output
- Integrate with `zozi_variant_config.json` structure for variant detection
- Use `upload_auto_05.py` as reference for the product detection pipeline

### 9. Create `providers/vision.py`
- Vision AI for product image analysis
- Public API (must match shim expectations):
  - `suggest_price(image_bytes, product_name, category)` -> suggested price
  - `normalize_category(product_name, description)` -> normalized category
  - `VariantConfig` (dataclass)
  - `analyze_product_image(image_bytes, filename, generate_copy, use_vision)` -> analysis result
- Integrate with `zozi_variant_config.json` for variant configuration
- Use `upload_auto_05.py` as reference

### 10. Create `providers/ai/__init__.py`
- Subpackage init that re-exports from `vision` and `text`

### 11. Create `providers/ai/vision.py`
- Vision model for product detection
- Must expose: `suggest_price`, `normalize_category`, `VariantConfig`, `analyze_product_image`

### 12. Create `providers/ai/text.py`
- Text model for variant/name extraction
- Must expose: `_ollama_chat`, `_OLLAMA_TEXT_MODEL`, `_extract_json`

### 13. Create `providers/chatbot.py`
- Chatbot with vectorization for product search and customer chat
- Integrate with existing `controllers/chatbot_controller.py` and `services/chat_system.py`
- Include vector search using product embeddings
- Provide: `ChatbotProvider` class with `process_query(query, session_id)` method

### 14. Create `providers/search.py`
- Advance search engine with AI-powered filtering and vectorization
- Integrate with existing `services/ai/advanced_search_engine.py` and `services/search/advanced_filter_service.py`
- Include semantic search, fuzzy matching, and filter parsing
- Provide: `AdvancedSearchEngine` class (matching existing interface)

### 15. Create `providers/geo.py`
- IP address detection for customer location and country detection
- Integrate with existing `services/country/country_detection.py` and `utils/ip_utils.py`
- Include GeoIP2 lookup, ipapi.co fallback, private IP detection
- Provide: `CountryDetectionService` class (matching existing interface)

### 16. Create `providers/map.py`
- Map and location provider system
- Integrate with existing `services/logistics/map_service.py` and `location_service/geo_resolver.py`
- Include forward/reverse geocoding, distance calculations
- Provide: `LocationProvider` class with `resolve_ip(ip)` and `reverse_geocode(lat, lon)` methods

### 17. Create `providers/country.py`
- Country details search AI system
- Integrate with existing `services/country/` modules
- Include country data lookup, currency, capital, languages, etc.
- Provide: `CountrySearchProvider` class with `search_country(query)` and `get_country_details(code)` methods

### 18. Create `providers/analytics.py`
- AI analysis for admin analytics
- Integrate with existing `routers/admin_analytics.py` and `controllers/admin_controller.py`
- Include dashboard metrics, chatbot analytics, product performance analysis
- Provide: `AnalyticsProvider` class with methods for each analytics endpoint

### 19. Verify `services/ai/` shims
- Verify all shim files in `services/ai/` correctly re-export from the new `providers/` modules
- Fix any import mismatches

### 20. Verify `services/ai/__init__.py`
- Ensure all re-exports are correct and complete

## Key Design Decisions

1. **Consolidation over duplication**: The 6 `br_*.py` files in `Working_API/` contain overlapping functionality. They should be consolidated into `providers/bg_remover.py` with model selection logic rather than maintaining separate files.

2. **Shim preservation**: The existing `services/ai/*.py` shim files must continue to work. They import from `providers.*` and re-export. The new `providers/` modules must expose the exact same public API that the shims expect.

3. **No breaking changes**: All existing import paths through `services/ai/` must continue to work without modification to any controller or router code.

4. **Reference files are source material**: The `Working_API/` files are not to be moved — they are reference implementations. New files in `providers/` should be written based on them but adapted to the backend's architecture.

5. **`providers/config.py` must exist**: The pyc file confirms a `config` module existed previously. It should contain provider-level configuration (model selection, API keys, environment variables).

## Risks

1. **Missing source files**: The `providers/` directory has `.pyc` files but no `.py` source files. The original source may have been deleted or moved. The pyc files can provide some insight into what was there but cannot be fully decompiled.

2. **Dependency compatibility**: The reference files use `rembg`, `opencv`, `pillow`, `numpy` etc. These are all in `requirements.txt` so no new dependencies are needed.

3. **API contract mismatches**: The shim files expect specific function signatures from `providers.*` modules. These must be matched exactly.

4. **`providers/image.py` vs `providers/bg_remover.py` overlap**: Both `image.py` and `bg_remover.py` expose `remove_background()`. The `image.py` version delegates to `bg_remover.py` for the actual logic.

## Validation

1. Run `python -c "from providers.bg_remover import remove_background, AVAILABLE_MODELS, VALID_STRATEGIES"` to verify bg_remover imports
2. Run `python -c "from providers.image import remove_background, generate_angles"` to verify image module
3. Run `python -c "from providers.ocr import parse_bill_text, parse_statement_csv"` to verify OCR module
4. Run `python -c "from providers.finance_ai import FinanceAIResult, parse_email_to_ledger, extract_bill_fields, suggest_reconciliation_match"` to verify finance module
5. Run `python -c "from providers.ai.vision import suggest_price, normalize_category, VariantConfig, analyze_product_image"` to verify vision module
6. Run `python -c "from providers.ai.text import _ollama_chat, _OLLAMA_TEXT_MODEL, _extract_json"` to verify text module
7. Run `python -c "from providers import bg_remover, image, ocr, finance_ai, text, vision, chatbot, search, geo, map, country, analytics"` to verify package init
8. Run existing test suite to verify no regressions
9. Verify all `services/ai/` shims import correctly