# Plan: Extend `CountryConfig` with the 10-Module E-Commerce Country Data Model (+ Live Web Research)

## Context

The repo has a mature multi-country system: `CountryConfig` (`backend/models/countries.py`), enhancement models, a live auto-populate service (`services/country_auto_populate.py` — already calls restcountries/World Bank/Nager/VAT APIs behind a circuit breaker), curated reference data (`data/country_curated.py`), and a seed script (`backend/_seed_countries.py`).

A 10-module / 63-field country checklist + an external PostgreSQL `country_ecommerce_profiles` schema was proposed. Goal: capture those fields in our system and **populate them with fresh, researched data from the internet** (avoiding Wikipedia staleness), then fit into the DB.

**Confirmed decisions:**
1. **Extend existing `CountryConfig`** (no new table, no external PG schema).
2. "ENUM" fields = **`String` columns + Python constants** (mirror `fraud_risk_tier`/`economic_tier`); keep SQLite + Postgres compatibility.
3. Data sourcing = **structured free JSON APIs for hard numbers + a separate DuckDuckGo→scrape→Ollama research job for qualitative lists**. (User rejected "heuristic estimates only" and "Google scraping" due to CAPTCHAs.)
4. Research pipeline = **separate offline job** (not inlined into `auto_populate`), reusing the repo's existing local LLM client (`ai_variant_config._ollama_chat`, `http://localhost:11434/v1/chat/completions`, `phi3:mini`) with optional OpenAI fallback via `OPENAI_API_KEY` in `.env`.

**Verified codebase facts:**
- JSON-ish lists stored as **`Text` JSON** (`payment_gateways_json`, `consumer_behavior_profile_json`); `_to_json`/`_from_json` in `controllers/country_controller.py`.
- Seed flow (3 touch points): `auto_populate_country()` dict → `_seed_countries.py` explicit `payload` → `create_admin_country()` explicit column assignment (constructor ~L410–468 + post-commit block ~L510–540).
- `MACRO_BY_COUNTRY` (`data/country_curated.py:5448`) only has `population: None` — rich fields NOT curated; must come from research/APIs.
- Existing free local LLM: `ai_variant_config._OLLAMA_BASE_URL`, `_OLLAMA_TEXT_MODEL`, `_ollama_chat(model, content, ...)`. `OPENAI_API_KEY=` present (empty) in `.env`.
- No DuckDuckGo usage yet; `ai_search_service.py` is product search only.

## Field mapping

**Reuse existing `CountryConfig` columns (do NOT duplicate):** `code`(alpha-2), `name`, `official_name`, `alpha3`, `capital`, `region`, `subregion`, `timezone`, `flag_url`, `population`, `internet_penetration_pct`, `urbanization_pct`, `mobile_subs_per_100`, `currency`, `currency_symbol`, `currency_name`, `exchange_rate_to_usd`, `gdp_per_capita_usd`, `economic_tier`, `tax_type`, `tax_name`, `tax_rate`, `tax_inclusive`, `tax_exempt_categories_json`, `tax_reduced_rates_json`, `payment_methods_json`, `payment_gateways_json`, `logistics_providers_json`, `cod_enabled`, `cod_max_amount`, `cod_verification_required`, `cod_remittance_days`, `fraud_risk_tier`, `address_format_json`, `legal_entity_required`(=local entity required), `consumer_protection_days`, `data_privacy_framework`, `legal_rules_json`, `product_restrictions_json`, `confidence_score`, `data_residency_tier`, `supported_languages_json`, `measurement_system`, `working_days_json`, `phone_code`(=phone country code), `public_holidays_json`, `consumer_behavior_profile_json`(already has digital_wallet_penetration/prefers_cod/mobile_commerce_likely).

**NEW columns on `CountryConfig`:**
- M1: `iso_numeric`(String3), `timezones_json`(Text list), `major_cities_json`(Text list[{name,population}]), `geographic_challenges_json`(Text list)
- M2: `median_age`(Int), `life_expectancy`(Num4,1), `inflation_rate_pct`(Num5,2), `average_monthly_income_usd`(Num10,2), `wealth_distribution_json`(Text{gini,...}), `banking_penetration_pct`(Num5,2), `exchange_rate_volatility`(String const)
- M3: `import_customs_duty_avg_pct`(Num5,2), `de_minimis_threshold_usd`(Num10,2), `shipping_duty_norm`(String const DDP/DDU/MIXED), `tax_registration_threshold_usd`(Num12,2)
- M4: `top_payment_gateways_json`(Text list — distinct from legacy `payment_gateways_json`), `credit_card_penetration_pct`(Num5,2), `digital_wallet_penetration_pct`(Num5,2 — also mirror into `consumer_behavior_profile_json`), `cod_prevalence_level`(String const), `cod_rejection_rate_pct`(Num5,2), `bnpl_popularity_level`(String const), `fraud_chargeback_risk`(String const — complements `fraud_risk_tier`)
- M5: `standard_phone_length`(Int), `dominant_local_couriers_json`(Text list), `avg_domestic_delivery_days`(Int), `weekend_delivery_enabled`(Bool default False), `return_logistics_ease`(String const), `postal_code_required`(Bool default True)
- M6: `primary_trust_factors_json`(Text list), `price_vs_quality_sensitivity`(String const), `brand_loyalty_index`(String const), `community_influence_level`(String const), `sustainability_consciousness`(String const), `impulse_vs_planned_buying`(String const)
- M7: `top_ecommerce_categories_json`(Text list), `major_shopping_holidays_json`(Text list — distinct from `public_holidays_json`), `device_usage_pct_json`(Text{mobile,desktop}), `app_vs_web_preference`(String const)
- M8: `dominant_search_engine`(String), `top_social_media_platforms_json`(Text list), `dominant_messaging_app`(String), `influencer_marketing_effectiveness`(String const), `ad_restriction_level`(String const)
- M9: `cookie_consent_strictness`(String const), `restricted_product_categories_json`(Text list — distinct from `product_restrictions_json`), `terms_requirements_json`(Text list)
- M10: `dominant_ecommerce_giants_json`(Text list), `standard_free_shipping_threshold_usd`(Num10,2), `support_expectation_level`(String const)

Constants module: `backend/data/country_profile_enums.py` → `PREVALENCE_LEVELS`, `RISK_LEVELS`, `SENSITIVITY_TYPES`, `DUTY_NORMS`, `LOGISTICS_EASE`, `EXCHANGE_VOLATILITY`, `SUPPORT_EXPECTATION`, `APP_WEB_PREF`.

## Implementation Tasks (ordered)

### T1 — Constants
Add `backend/data/country_profile_enums.py` with the const tuples above.

### T2 — Model columns
In `backend/models/countries.py` add the NEW columns (types: String/Numeric/Integer/Boolean/Text; JSON-ish = Text default `"[]"`/`"{}"`). No edits to existing columns. Verify no dup of `phone_code`/`legal_entity_required`.

### T3 — Alembic migration (backend-agnostic)
Generate `backend/alembic/versions/<rev>_extend_country_config_10_modules.py` with `op.add_column("country_configs", ...)` using `sa.String/Numeric/Integer/Boolean/Text` only. Append to current real head (repo has merge heads — check `alembic heads` first). No PG-specific DDL.

### T4 — Structured-API enrichment in `auto_populate_country()`
Extend `services/country_auto_populate.py` to pull hard numbers from free JSON APIs it already calls / can add:
- `iso_numeric`, `timezones` → from `get_curated_country()` (restcountries-derived).
- `median_age`, `life_expectancy` → World Bank indicators `SP.DYN.MED.AG` / `SP.DYN.LE00.IN` (extend `fetch_world_bank_data` indicators map).
- `inflation_rate_pct` → World Bank `FP.CPI.TOTL.ZG`.
- Keep GDP/population/internet as-is. Add these keys to the returned `result` dict.

### T5 — Live web research service (NEW) `backend/services/country_research.py`
3-step pipeline, per user's architecture, but reusing repo clients:
- **Search:** `duckduckgo-search` `DDGS().text(query, max_results=...)` (free, no CAPTCHA like Google). Queries target fresh data with year + specific terms (e.g. `"{country} e-commerce payment gateways 2024"`, `"{country} de minimis threshold customs VAT"`, `"{country} top logistics couriers delivery returns"`, `"{country} internet penetration social media dominant app"`, `"{country} shopping holidays consumer trust factors"`).
- **Scrape:** `requests` + `bs4.BeautifulSoup`, strip script/style/nav/footer, cap ~1500 chars/source, `User-Agent` header, `timeout=10`, `time.sleep` between queries.
- **Structure:** call repo's `_ollama_chat(_OLLAMA_TEXT_MODEL, prompt, ...)` (OpenAI-compatible `/v1/chat/completions`) with a strict system prompt forcing the 10-module JSON (same schema as field mapping). Fallback: if `OPENAI_API_KEY` set and Ollama down, use `openai` client (`gpt-4o-mini`, `response_format=json_object`). If neither available → return `{"error":"no_llm"}` and skip (do not fabricate).
- `research_country(code)` → returns the structured dict + `metadata` (sources count, date). Persist to `backend/data/research/{CODE}_research.json` for audit/retry. **Do NOT** auto-merge into DB here (separate ingest step).

### T6 — Research router + ingestion
- `backend/routers/country_research.py`: `POST /countries/{code}/research` (admin) runs `research_country` and stores JSON to disk; `POST /countries/{code}/research/apply` merges the JSON into the country's `CountryConfig` (update columns + `confidence_score`). `GET /countries/{code}/research` returns current JSON.
- Add a merge helper in `controllers/country_controller.py` (`apply_research_to_country(code, data, db)`) that maps the 10-module JSON → columns (scalars `data.get(...)`, lists via `_to_json`). Guard: only overwrite when value present and non-`N/A`.
- Offline CLI: `python -m services.country_research OM AE US` for batch backfill.

### T7 — Seed payload + controller + schema (for structured fields)
- `_seed_countries.py` payload: add NEW structured keys from `result` (T4).
- `controllers/country_controller.py` `create_admin_country()`: add explicit assignments for each NEW column (scalars `payload.get`, JSON `_to_json(payload.get)`).
- `backend/routers/countries.py`: extend `CountryCreateBody` + `_country_public_payload` (return new fields, grouped under `profile`).

### T8 — Dependency note
`duckduckgo-search`, `beautifulsoup4` — add to `requirements.txt` if not present (`requests` already used). Document `ollama run phi3:mini` as the free local LLM prerequisite; `OPENAI_API_KEY` optional.

## Validation
1. `alembic upgrade head` on local SQLite succeeds; `from db.models import CountryConfig` imports.
2. `python -m _seed_countries OM AE US --overwrite` populates structured NEW fields; SQL spot-check `iso_numeric`, `median_age`, `de_minimis_threshold_usd` non-null.
3. Research job: with Ollama running, `python -m services.country_research OM` creates `backend/data/research/OM_research.json` with the 10-module keys; `POST /countries/OM/research/apply` merges; `GET /countries/OM` shows values. Verify no `N/A` strings written as column values (guard skips them).
4. OpenAI fallback: set `OPENAI_API_KEY`, stop Ollama, re-run research → still produces JSON.
5. Run `backend/test_models.py` / `test_schemas.py` (or repo equivalents); ensure no regression.
6. Confirm no duplicate columns (`phone_country_code`/`local_entity_required` NOT added).

## Risks / Open Questions
- **Ollama not running in CI/local**: research job must degrade gracefully (skip + log), never fabricate. Seeding (T7) still works without research (structured APIs only).
- **LLM extraction accuracy**: prompt must forbid hallucination; instruct "N/A"/null when absent. `confidence_score` should reflect researched vs estimated. Human review recommended for launch-critical countries.
- **Scraper fragility**: sites block bots; cap chars, rotate queries, add polite delays. DDG HTML may change — `duckduckgo-search` abstracts this; monitor.
- **Merge-heads in Alembic**: verify `alembic heads` before generating T3 migration.
- **Cost**: Ollama = free local; OpenAI fallback ~$0.002/country — acceptable, opt-in.
- **Frontend Country Ledger tabs** to surface these fields: out of scope (data layer + ingestion only).
- **Downstream consumers** (3D-Secure from `fraud_chargeback_risk`, DDP/DDU pricing from `shipping_duty_norm`+`de_minimis_threshold_usd`, support routing from `dominant_messaging_app`): deferred.
