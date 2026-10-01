# Country Intelligence & Auto-Research Feature

Status: Design Reference
Scope: A single-page "Country Dynamics" feature that automatically researches any country in the world from the internet and presents a complete, e-commerce-ready intelligence profile — currency, tax, payments, logistics, consumer behavior, competition, risk, and AI-generated strategy — that can later be fed into the Country Onboarding workflow (see companion document: `COUNTRY_ADMIN_ONBOARDING_SYSTEM.md`).

---

## 1) Overview

This feature lets a non-technical operator type any country name (e.g. "India", "Brazil", "Nigeria") and instantly receive a comprehensive, structured research report covering 20 modules of market intelligence. It is built on a **100% free tech stack**: live public APIs, web search, news RSS, and an optional local open-source LLM for qualitative deep research.

It is the **"understanding" side of the coin**. The companion document covers the **"operating" side** — turning that understanding into a live, configurable country inside the platform.

### Why this exists
Rapid expansion means we will evaluate many countries quickly. Before committing engineering effort to launch a country, we need a fast, repeatable way to answer:
- Is this market worth entering?
- What tax, payment, and logistics model does it require?
- What do consumers expect (COD, wallets, free shipping, languages)?
- What are the legal, fraud, and competitive risks?
- What product mix and entry strategy should we use?

This feature answers all of that from one input field, with free data sources and confidence/verification flags on every uncertain data point.

---

## 2) How It Works (End-to-End Flow)

1. **Input:** Operator enters a country name in the Country Intelligence page (single search field).
2. **Resolve basics:** `REST Countries API` returns official name, ISO codes, capital, currency, languages, calling code, region, flag, coordinates.
3. **Enrich economy:** `World Bank Open Data API` returns latest available GDP, GDP per capita (PPP), inflation, unemployment, literacy, internet users %, urbanization, Gini, etc.
4. **Enrich exchange rate:** `Frankfurter (ECB)` with `open.er-api.com` fallback for live USD conversion.
5. **Enrich cities:** `GeoNames` (free account) preferred; `CountriesNow API` fallback; capital city final fallback.
6. **Context summary:** `Wikipedia API` returns a country overview extract.
7. **Current news:** `Google News RSS` filtered to economy/ecommerce/tax/consumer/payments for the last 24 hours.
8. **Web evidence (optional):** `DuckDuckGo` search surfaces current-year tax, payment-gateway, and regulatory details.
9. **Deep qualitative research (optional):** A local `Ollama` LLM (e.g. `llama3.1` / `llama3.2:3b`) writes the narrative modules — psychology, mindset, community behavior, gateway landscape, regulations, marketing channels, strategic recommendations.
10. **Confidence tagging:** Every qualitative field is returned with `confidence` (`high|medium|low`), `verification_notes`, and `sources` so the system can flag uncertain data for official verification.
11. **Output:**
    - **JSON report** for system integration (country config seeding).
    - **Markdown report** for human reading.
    - **Single-page dashboard** with stat cards, charts, timelines, alerts, and map overlays.

> Important: "Latest" is handled as much as technically possible (live APIs, news RSS, current-year web evidence, latest World Bank data). But tax, law, payment gateways, and regulations change quickly — hence the `confidence`, `verification_notes`, and `sources` fields.

If Ollama is not installed, the script still works: it collects facts, economic data, news, and web evidence, but marks deep qualitative modules as needing AI or manual review.

---

## 3) Free Data Source Stack

| Purpose | Free Source |
|---------|-------------|
| Country basics, currency, language, country code | REST Countries API |
| Latest economic indicators | World Bank Open Data API |
| Latest exchange rates | Frankfurter ECB API + open.er-api fallback |
| Cities | CountriesNow API + optional GeoNames free account |
| Country summary/context | Wikipedia API |
| Latest news of the day | Google News RSS |
| Latest web evidence for tax, payments, rules, behavior | DuckDuckGo search (optional, free) |
| Deep qualitative research (psychology, mindset, gateways, regulations, strategy) | Local free Ollama LLM, no paid key |

Setup:
- `pip install requests duckduckgo-search`
- Optional GeoNames: create free account, set `GEONAMES_USERNAME`.
- Optional Ollama: install from ollama.com, `ollama pull llama3.1` (or `llama3.2:3b` for low RAM).

---

## 4) The 20-Module Intelligence Framework

Every country report is structured into 20 modules. Each module lists the specific data points collected, an e-commerce example, and the recommended presentation format. Below is the full master blueprint.

### 🗂️ MODULE 1: COUNTRY IDENTITY & BASICS

| # | Data Point | Example | Presentation |
|---|-----------|---------|--------------|
| 1.1 | Official Country Name | Republic of India | Header / Title |
| 1.2 | Common/Short Name | India | Searchable tag |
| 1.3 | Country Code (ISO Alpha-2) | IN | Badge/Chip |
| 1.4 | Country Code (ISO Alpha-3) | IND | Badge/Chip |
| 1.5 | Numeric Code | 356 | Hidden field |
| 1.6 | Capital City | New Delhi | Info card |
| 1.7 | Flag (Emoji + Image URL) | 🇮🇳 | Icon |
| 1.8 | Region / Continent | Asia > Southern Asia | Breadcrumb |
| 1.9 | Total Area (km²) | 3,287,263 | Stat card |
| 1.10 | Time Zones | UTC+5:30 | Dropdown selector |
| 1.11 | Calling Code | +91 | Input prefix |
| 1.12 | Google Maps Link | URL | Button |
| 1.13 | Government Type | Federal Parliamentary Republic | Tag |
| 1.14 | Independence / Founding Year | 1947 | Timeline |

---

### 🗂️ MODULE 2: DEMOGRAPHICS & POPULATION

| # | Data Point | Example | Presentation |
|---|-----------|---------|--------------|
| 2.1 | Total Population | 1.44 Billion | Big stat card |
| 2.2 | Population Growth Rate | 0.8% / year | Trend arrow ↑↓ |
| 2.3 | Median Age | 28.7 years | Gauge chart |
| 2.4 | Age Distribution (0-14, 15-64, 65+) | 25%, 68%, 7% | Pie chart |
| 2.5 | Urban vs Rural Split | 35% Urban / 65% Rural | Donut chart |
| 2.6 | Gender Ratio | 1.08 M : 1 F | Bar chart |
| 2.7 | Literacy Rate | 77.7% | Progress bar |
| 2.8 | Top 10 Cities (by population) | Mumbai, Delhi, Bangalore... | Ranked table |
| 2.9 | Top 5 E-commerce Ready Cities | Bangalore, Mumbai, Delhi, Hyderabad, Pune | Highlighted cards with reasoning |
| 2.10 | Ethnic / Racial Composition | Diverse, 2000+ ethnic groups | Tag cloud |
| 2.11 | Religious Composition | Hindu 79%, Muslim 14%, etc. | Pie chart |
| 2.12 | Expatriate / Foreign Worker % | 0.5% | Stat card |

---

### 🗂️ MODULE 3: ECONOMY & WEALTH

| # | Data Point | Example | Presentation |
|---|-----------|---------|--------------|
| 3.1 | GDP (Nominal) | $3.94 Trillion | Stat card |
| 3.2 | GDP Per Capita (PPP) | $9,183 | Stat card |
| 3.3 | GDP Growth Rate | 6.5% | Trend line |
| 3.4 | Inflation Rate | 5.1% | Warning indicator |
| 3.5 | Unemployment Rate | 7.2% | Gauge |
| 3.6 | Income Distribution (Gini Coefficient) | 35.7 | Scale bar |
| 3.7 | Middle Class Size (% of pop) | ~30% (400M people) | Highlighted stat |
| 3.8 | Average Monthly Salary | $600 USD | Stat card |
| 3.9 | Average Disposable Income | $250-$400/month | Range slider visual |
| 3.10 | Poverty Rate | 10.5% | Alert badge |
| 3.11 | Wealth Tiers Breakdown | Ultra-rich 1%, Upper-middle 10%, Middle 30%, Lower 59% | Stacked bar |
| 3.12 | Currency Name | Indian Rupee | Text |
| 3.13 | Currency Code (ISO) | INR | Badge |
| 3.14 | Currency Symbol | ₹ | Icon |
| 3.15 | Exchange Rate (vs USD) | 1 USD = 83.2 INR | Live ticker |
| 3.16 | Currency Stability (1yr trend) | Depreciating ~3%/yr | Sparkline |
| 3.17 | Foreign Exchange Controls | Partial restrictions | Alert tag |

---

### 🗂️ MODULE 4: TAX SYSTEM & DUTIES

| # | Data Point | Example | Presentation |
|---|-----------|---------|--------------|
| 4.1 | Tax System Type | GST (Goods & Services Tax) | Tag |
| 4.2 | Standard Tax Rate | 18% | Big stat |
| 4.3 | Tax Slabs / Tiers | 0%, 5%, 12%, 18%, 28% | Tiered table |
| 4.4 | Tax on Digital Goods | 18% | Info card |
| 4.5 | Tax on Physical Goods | 5%-28% (category-based) | Category table |
| 4.6 | Import / Customs Duty | 10%-30% (varies by HS code) | Range table |
| 4.7 | Customs Threshold (De Minimis) | ₹50,000 (~$600) | Alert box |
| 4.8 | Who Pays Duty? (DDP vs DDU) | Customer pays at door (DDU common) | Flow diagram |
| 4.9 | Tax Registration Requirement | GSTIN needed for >₹40L turnover | Checklist |
| 4.10 | Foreign Company Tax Obligation | Need local entity or agent | Alert box |
| 4.11 | Withholding Tax on Cross-border | 10%-20% | Info card |
| 4.12 | Tax Filing Frequency | Monthly / Quarterly | Calendar icon |
| 4.13 | Tax Authority Name | Central Board of Direct Taxes (CBDT) | Link |
| 4.14 | Free Trade Agreements | ASEAN, SAFTA, bilateral deals | Tag list |

---

### 🗂️ MODULE 5: CONSUMER PSYCHOLOGY & MINDSET

| # | Data Point | Example | Presentation |
|---|-----------|---------|--------------|
| 5.1 | General Mindset Toward Online Shopping | "Trust but verify" – growing but cautious | Narrative card |
| 5.2 | Price Sensitivity Level | HIGH (8/10) | Rating scale |
| 5.3 | Brand Loyalty Level | MEDIUM – switch for discounts | Rating scale |
| 5.4 | Status / Prestige Buying | YES – luxury brands signal success | Tag |
| 5.5 | Family Influence on Purchases | VERY HIGH – joint family decisions | Rating scale |
| 5.6 | Peer / Social Proof Influence | HIGH – reviews & word-of-mouth critical | Rating scale |
| 5.7 | FOMO (Fear of Missing Out) Factor | HIGH during sales events | Rating scale |
| 5.8 | Trust in Foreign Brands | MEDIUM – prefer known global names | Gauge |
| 5.9 | Trust in New/Unknown Brands | LOW – need heavy social proof | Gauge |
| 5.10 | Bargaining / Negotiation Culture | YES – expect discounts, coupons | Tag |
| 5.11 | Impulse vs Planned Buying Ratio | 40% impulse / 60% planned | Pie chart |
| 5.12 | Research Before Purchase | HIGH – compare 3-5 sites before buying | Info card |
| 5.13 | Emotional vs Rational Buying | 60% emotional / 40% rational | Split bar |
| 5.14 | Attitude Toward "Made in [Country]" | Patriotic buying trend (e.g., "Make in India") | Tag |
| 5.15 | Generational Differences | Gen-Z: digital-first; 40+: prefer COD | Comparison table |

---

### 🗂️ MODULE 6: CONSUMPTION PREFERENCES

| # | Data Point | Example | Presentation |
|---|-----------|---------|--------------|
| 6.1 | Top 10 Product Categories (by demand) | Electronics, Fashion, Grocery, Beauty... | Ranked list |
| 6.2 | Average Order Value (AOV) | $25-$45 | Stat card |
| 6.3 | Quality vs Price Priority | Price-first for mass; Quality for premium | Split view |
| 6.4 | Sustainability / Eco-consciousness | LOW-MEDIUM (growing in metros) | Gauge |
| 6.5 | Preference for Local vs International | Mixed – local for food, intl for tech | Comparison |
| 6.6 | Size / Fit Preferences | Specific to body types, modest wear in some regions | Info card |
| 6.7 | Color / Design Preferences | Bright colors, gold accents, cultural motifs | Visual palette |
| 6.8 | Packaging Expectations | Gift wrapping important during festivals | Tag |
| 6.9 | Subscription / Repeat Purchase Rate | LOW – prefer one-time buys | Stat |
| 6.10 | Bulk / Wholesale Buying Culture | HIGH – family-size packs preferred | Tag |
| 6.11 | Seasonal Product Demand | Winter wear (North), AC/fans (South), etc. | Calendar heatmap |
| 6.12 | Halal / Kosher / Vegetarian Requirements | 30%+ vegetarian; Halal important for Muslim segment | Alert tags |
| 6.13 | Prohibited / Restricted Products | Alcohol banned in some states; beef restrictions | Red alert box |

---

### 🗂️ MODULE 7: SHOPPING SEASONALITY & EVENTS

| # | Data Point | Example | Presentation |
|---|-----------|---------|--------------|
| 7.1 | Major Shopping Festivals | Diwali, Holi, Eid, Christmas | Calendar timeline |
| 7.2 | E-commerce Specific Sales Events | Big Billion Days (Flipkart), Great Indian Festival (Amazon) | Highlighted cards |
| 7.3 | Global Sales Events Participation | Black Friday, Cyber Monday, 11.11 | Tags |
| 7.4 | Payday Shopping Cycles | 1st-5th of month (salary week) | Recurring highlight |
| 7.5 | Wedding Season Impact | Oct-Feb: massive gold, clothing, gift demand | Seasonal banner |
| 7.6 | Back-to-School Season | April-June (varies by state) | Calendar tag |
| 7.7 | Religious Fasting Periods | Ramadan, Navratri – altered buying patterns | Alert |
| 7.8 | Monsoon / Weather Impact | Jun-Sep: indoor shopping spikes, logistics delays | Weather icon |
| 7.9 | Peak Shopping Hours | 8 PM - 12 AM (post-work browsing) | Clock visual |
| 7.10 | Peak Shopping Days | Weekends, Sunday highest | Bar chart |

---

### 🗂️ MODULE 8: DIGITAL LANDSCAPE & INTERNET

| # | Data Point | Example | Presentation |
|---|-----------|---------|--------------|
| 8.1 | Internet Penetration Rate | 52% (750M+ users) | Progress bar |
| 8.2 | Mobile vs Desktop Split | 85% Mobile / 15% Desktop | Donut chart |
| 8.3 | Average Internet Speed | 60 Mbps (mobile) | Gauge |
| 8.4 | Smartphone Penetration | 45%+ and growing | Stat card |
| 8.5 | Dominant OS (Android vs iOS) | Android 95% / iOS 5% | Pie chart |
| 8.6 | Top Social Media Platforms | YouTube, WhatsApp, Instagram, Facebook | Ranked icons |
| 8.7 | Social Media Usage (hrs/day) | 2.5 hours average | Stat card |
| 8.8 | E-commerce App Preferences | Flipkart, Amazon, Meesho, Myntra | Ranked list |
| 8.9 | Search Engine Preference | Google 98% | Stat |
| 8.10 | Email Open / Engagement Rate | LOW – WhatsApp preferred for communication | Alert |
| 8.11 | Video Commerce / Live Shopping | Growing – YouTube, Instagram Live | Trend tag |
| 8.12 | AI / Chatbot Acceptance | MEDIUM – prefer human support | Gauge |

---

### 🗂️ MODULE 9: PAYMENT INFRASTRUCTURE

| # | Data Point | Example | Presentation |
|---|-----------|---------|--------------|
| 9.1 | Most Popular Payment Method | UPI (Unified Payments Interface) | #1 Highlighted card |
| 9.2 | Top 5 Payment Gateways | Razorpay, PayU, CCAvenue, PhonePe, Paytm | Ranked list |
| 9.3 | Credit/Debit Card Penetration | 35% of adults | Stat card |
| 9.4 | Digital Wallet Usage | PhonePe, Google Pay, Paytm – VERY HIGH | Tag cloud |
| 9.5 | Cash on Delivery (COD) % | 40-50% of e-commerce orders | Big alert stat |
| 9.6 | Bank Transfer / Net Banking | 15% of transactions | Stat |
| 9.7 | Buy Now Pay Later (BNPL) | Growing – Simpl, LazyPay, Amazon Pay Later | Trend tag |
| 9.8 | EMI / Installment Culture | VERY HIGH – "No Cost EMI" expected | Highlighted |
| 9.9 | International Card Acceptance | Visa, Mastercard accepted; Amex limited | Tag list |
| 9.10 | Cryptocurrency Status | Banned / Restricted / Taxed | Alert badge |
| 9.11 | Average Transaction Value | $15-$30 online | Stat card |
| 9.12 | Payment Failure Rate | 5-8% (UPI much lower) | Warning indicator |
| 9.13 | Refund Processing Time | 5-7 business days expected | Info card |
| 9.14 | Currency Conversion Fees | 2-3.5% on international cards | Info card |

---

### 🗂️ MODULE 10: LOGISTICS & SHIPPING

| # | Data Point | Example | Presentation |
|---|-----------|---------|--------------|
| 10.1 | Top Courier / Logistics Companies | Delhivery, BlueDart, DTDC, India Post | Ranked list |
| 10.2 | Average Delivery Time (Metro) | 1-3 days | Stat card |
| 10.3 | Average Delivery Time (Rural) | 5-10 days | Stat card |
| 10.4 | Shipping Cost Expectation | FREE shipping expected (subsidized) | Alert |
| 10.5 | Free Shipping Threshold | Orders above ₹499-₹999 | Info card |
| 10.6 | Same-Day / Next-Day Availability | Metro cities only | Tag |
| 10.7 | Last-Mile Delivery Quality | MEDIUM – address issues in rural areas | Gauge |
| 10.8 | Package Tracking Expectation | MANDATORY – real-time tracking expected | Alert |
| 10.9 | COD Availability by Region | Urban: Yes; Remote: Limited | Map overlay |
| 10.10 | Return Pickup Service | Expected – doorstep pickup for returns | Info card |
| 10.11 | Customs Clearance Time (Imports) | 3-7 days | Stat card |
| 10.12 | Warehousing Hubs | Mumbai, Delhi NCR, Bangalore, Hyderabad | Map pins |
| 10.13 | Packaging Regulations | Plastic ban in some states; eco-packaging push | Alert |

---

### 🗂️ MODULE 11: LEGAL, RULES & REGULATIONS

| # | Data Point | Example | Presentation |
|---|-----------|---------|--------------|
| 11.1 | E-commerce Registration Requirement | FDI rules, local entity needed for marketplace | Checklist |
| 11.2 | Consumer Protection Law | Consumer Protection Act 2019 | Info card |
| 11.3 | Mandatory Return/Refund Window | 7-10 days (platform dependent) | Stat card |
| 11.4 | Data Privacy Law | Digital Personal Data Protection Act (DPDP) 2023 | Alert card |
| 11.5 | Data Localization Requirement | Critical data must stay in-country | Red alert |
| 11.6 | Cookie / Tracking Consent Rules | Consent-based (similar to GDPR) | Info card |
| 11.7 | Advertising Standards / Restrictions | No misleading claims; ASCI guidelines | Checklist |
| 11.8 | Product Labeling Requirements | MRP, manufacturing date, FSSAI (food), BIS (electronics) | Checklist |
| 11.9 | Prohibited / Restricted Items for Sale | Alcohol, tobacco, weapons, certain drugs | Red alert box |
| 11.10 | Intellectual Property / Trademark Laws | Trademark Act 1999; strict on counterfeits | Info card |
| 11.11 | Anti-Trust / Competition Law | Competition Act 2002 – no predatory pricing | Alert |
| 11.12 | GST Invoice Requirements | Mandatory GSTIN on all invoices | Checklist |
| 11.13 | Foreign Exchange Regulations (FEMA) | RBI guidelines on cross-border payments | Alert |
| 11.14 | Age Verification Requirements | 18+ for certain products (alcohol, tobacco) | Tag |
| 11.15 | Environmental / E-Waste Regulations | E-waste management rules apply to electronics | Info card |

---

### 🗂️ MODULE 12: LANGUAGE & COMMUNICATION

| # | Data Point | Example | Presentation |
|---|-----------|---------|--------------|
| 12.1 | Official Language(s) | Hindi, English | Tag badges |
| 12.2 | Regional / State Languages | Tamil, Telugu, Bengali, Marathi, etc. (22 scheduled) | Expandable list |
| 12.3 | Primary E-commerce Language | English + Hindi (Hinglish) | Highlighted |
| 12.4 | Localization Requirement | Product descriptions in 5+ languages for reach | Checklist |
| 12.5 | Script / Writing System | Devanagari, Tamil, Bengali scripts | Visual samples |
| 12.6 | Number / Date Format | DD/MM/YYYY; Indian numbering (Lakh, Crore) | Info card |
| 12.7 | Measurement System | Metric (kg, cm, liters) | Tag |
| 12.8 | Customer Support Language Expectation | Hindi + English minimum; regional preferred | Alert |
| 12.9 | RTL (Right-to-Left) Requirement | No (but YES for Arabic/Urdu markets) | Boolean flag |
| 12.10 | Tone / Formality in Communication | Formal with elders; casual with Gen-Z | Info card |

---

### 🗂️ MODULE 13: COMMUNITY & SOCIAL STRUCTURE

| # | Data Point | Example | Presentation |
|---|-----------|---------|--------------|
| 13.1 | Family Structure | Joint family common; nuclear growing in cities | Info card |
| 13.2 | Decision-Making Unit | Family / household (not individual) | Tag |
| 13.3 | Caste / Class Sensitivity | Sensitive topic – avoid in marketing | Red alert |
| 13.4 | Gender Roles in Purchasing | Women: household, fashion; Men: electronics, auto | Info card |
| 13.5 | Community / Group Buying Culture | WhatsApp groups for deals; community buying | Tag |
| 13.6 | Influencer / Celebrity Impact | VERY HIGH – Bollywood, cricket stars, YouTubers | Rating |
| 13.7 | Religious / Cultural Sensitivities | Avoid beef imagery, respect festivals, modesty norms | Red alert box |
| 13.8 | Festival Gifting Culture | Diwali, Raksha Bandhan – massive gifting demand | Highlighted |
| 13.9 | Trust in Word-of-Mouth | EXTREMELY HIGH – personal recommendations > ads | Rating |
| 13.10 | Review / Rating Culture | Growing – read reviews but write fewer | Gauge |

---

### 🗂️ MODULE 14: MARKETING & ADVERTISING LANDSCAPE

| # | Data Point | Example | Presentation |
|---|-----------|---------|--------------|
| 14.1 | Most Effective Ad Channel | YouTube video ads, Instagram Reels | Ranked list |
| 14.2 | Influencer Marketing Effectiveness | HIGH – micro-influencers (10K-100K) best ROI | Rating |
| 14.3 | Email Marketing Effectiveness | LOW – 2-5% open rate | Warning |
| 14.4 | WhatsApp Marketing | VERY HIGH – primary communication channel | Highlighted |
| 14.5 | SMS Marketing | MEDIUM – OTP + offers still work | Tag |
| 14.6 | TV / Traditional Media Impact | Still HIGH in Tier 2/3 cities | Info card |
| 14.7 | Affiliate Marketing Maturity | Growing – CouponDunia, GoPaisa | Tag |
| 14.8 | SEO / Organic Search Behavior | Google search in English + Hindi | Info card |
| 14.9 | Ad Spend Per Capita | $3-$5 annually | Stat card |
| 14.10 | Best Time to Run Ads | 7 PM - 11 PM; Weekends | Clock visual |
| 14.11 | Content Format Preference | Short video (Reels/Shorts) > Images > Text | Ranked |
| 14.12 | Loyalty / Rewards Program Response | HIGH – cashback, points, coupons loved | Tag |

---

### 🗂️ MODULE 15: COMPETITION & MARKET LANDSCAPE

| # | Data Point | Example | Presentation |
|---|-----------|---------|--------------|
| 15.1 | Top 5 E-commerce Platforms | Amazon, Flipkart, Meesho, Myntra, Nykaa | Ranked cards |
| 15.2 | Market Share Breakdown | Amazon 30%, Flipkart 28%, Others 42% | Pie chart |
| 15.3 | Niche / Vertical Players | Nykaa (beauty), PharmEasy (health), BigBasket (grocery) | Tag list |
| 15.4 | Social Commerce Platforms | Meesho, Instagram Shopping, WhatsApp Business | Tags |
| 15.5 | D2C Brand Ecosystem | Growing – Mamaearth, boAt, Sugar | Info card |
| 15.6 | Price Comparison Behavior | HIGH – use PriceDekho, MySmartPrice | Alert |
| 15.7 | Market Entry Barriers | FDI restrictions, local competition, logistics | Checklist |
| 15.8 | White Space / Untapped Niches | Tier 3 cities, vernacular commerce, B2B | Opportunity cards |

---

### 🗂️ MODULE 16: CUSTOMER SERVICE EXPECTATIONS

| # | Data Point | Example | Presentation |
|---|-----------|---------|--------------|
| 16.1 | Preferred Support Channel | WhatsApp > Phone > Email > Chat | Ranked list |
| 16.2 | Expected Response Time | < 2 hours (WhatsApp); < 24 hrs (email) | SLA card |
| 16.3 | Language for Support | Hindi + English minimum | Tag |
| 16.4 | Return / Refund Expectation | 7-10 day no-questions return | Info card |
| 16.5 | Compensation Culture | Expect discount/coupon for inconvenience | Tag |
| 16.6 | Social Media Complaint Behavior | HIGH – public shaming on Twitter/X common | Alert |
| 16.7 | Warranty / Guarantee Expectation | 1-year standard for electronics | Info card |
| 16.8 | After-Sales Service Importance | VERY HIGH – installation, setup support | Rating |

---

### 🗂️ MODULE 17: TECHNOLOGY & INFRASTRUCTURE

| # | Data Point | Example | Presentation |
|---|-----------|---------|--------------|
| 17.1 | Cloud / Hosting Regulations | Data must be stored in-country (for some sectors) | Alert |
| 17.2 | CDN / Server Location Recommendation | Mumbai, Delhi, Bangalore data centers | Map pins |
| 17.3 | App Store Preferences | Google Play dominant (95%+) | Stat |
| 17.4 | PWA vs Native App Preference | App preferred; PWA for low-storage users | Info card |
| 17.5 | Browser Usage | Chrome 90%+, Safari 5% | Pie chart |
| 17.6 | Screen Size / Resolution Common | 6.1"-6.7" smartphones dominant | Info card |
| 17.7 | Low-Bandwidth Optimization Need | YES – 40%+ on 3G/4G in rural | Alert |
| 17.8 | UPI / API Integration Standards | NPCI guidelines for UPI | Technical doc link |

---

### 🗂️ MODULE 18: NEWS & CURRENT CONTEXT

| # | Data Point | Example | Presentation |
|---|-----------|---------|--------------|
| 18.1 | Current Economic News | Inflation trends, RBI rate decisions | News feed card |
| 18.2 | Political Stability | Stable / Election year / Unrest | Status badge (🟢🟡🔴) |
| 18.3 | Recent Regulatory Changes | New e-commerce rules, tax amendments | Alert feed |
| 18.4 | Natural Disasters / Disruptions | Monsoon floods, pandemic impact | Warning banner |
| 18.5 | Consumer Sentiment Index | Optimistic / Cautious / Pessimistic | Gauge |
| 18.6 | Trending Products / Viral Items | Current viral product categories | Trending tags |
| 18.7 | Exchange Rate Volatility (Current) | Stable / Volatile | Sparkline |

---

### 🗂️ MODULE 19: RISK & COMPLIANCE MATRIX

| # | Data Point | Example | Presentation |
|---|-----------|---------|--------------|
| 19.1 | Fraud / Chargeback Rate | MEDIUM-HIGH (COD rejections 15-20%) | Risk meter |
| 19.2 | Counterfeit Product Prevalence | HIGH in fashion, electronics | Alert |
| 19.3 | Cybersecurity Threat Level | MEDIUM | Risk badge |
| 19.4 | Sanctions / Trade Restrictions | None / Partial / Full | Status badge |
| 19.5 | Political Risk to Business | LOW / MEDIUM / HIGH | Traffic light |
| 19.6 | Currency Risk (Repatriation) | LOW – freely convertible | Tag |
| 19.7 | Legal Dispute Resolution | Arbitration preferred; slow courts | Info card |

---

### 🗂️ MODULE 20: STRATEGIC RECOMMENDATIONS (AI-Generated)

| # | Data Point | Example | Presentation |
|---|-----------|---------|--------------|
| 20.1 | Market Entry Strategy | Start with Metro cities → expand Tier 2 | Roadmap |
| 20.2 | Pricing Strategy | Competitive + heavy discounting initially | Info card |
| 20.3 | Recommended Product Mix | Fashion + Electronics + Beauty first | Priority list |
| 20.4 | Recommended Payment Stack | UPI + COD + Cards + BNPL | Checklist |
| 20.5 | Recommended Marketing Mix | 60% Social, 20% Influencer, 10% SEO, 10% Email | Pie chart |
| 20.6 | Localization Priority | Hindi → Tamil → Telugu → Bengali | Ordered list |
| 20.7 | Key Success Factors | Free shipping, COD, fast delivery, WhatsApp support | Checklist |
| 20.8 | Key Risks to Mitigate | COD rejection, returns, regulatory changes | Alert list |
| 20.9 | Estimated Time to Profitability | 18-24 months | Timeline |
| 20.10 | Recommended Budget Allocation | Marketing 40%, Logistics 25%, Tech 20%, Ops 15% | Pie chart |


### Module Priority Summary
- Critical (🔴): Identity, Demographics, Economy, Tax, Psychology, Digital, Payments, Logistics, Legal.
- High (🟡): Seasonality, Language, Community, Marketing, Competition, Customer Service, Risk.
- Medium (🟢): Technology, News, Strategic Recommendations.

Total: 20 modules × ~200+ data points.

---

## 5) Presentation Format Guide (Single-Page Dashboard)

### UI Element Usage
| Element | Use For |
|---------|---------|
| Stat Cards (big number + label) | Population, GDP, Tax Rate, AOV |
| Gauge / Progress Bars | Internet penetration, Price sensitivity, Trust levels |
| Pie / Donut Charts | Age distribution, Payment split, Market share |
| Ranked Lists | Top cities, Top payment methods, Top categories |
| Traffic Light Badges (🟢🟡🔴) | Risk levels, Political stability, Compliance status |
| Alert Boxes (Red/Yellow) | Legal restrictions, COD %, Data localization |
| Calendar / Timeline | Shopping festivals, Seasons, Peak hours |
| Comparison Tables | Urban vs Rural, Gen-Z vs 40+, Local vs Foreign |
| Checklists | Compliance requirements, Registration steps |
| Map Overlays | Warehouse hubs, Delivery zones, City targeting |
| Trend Sparklines | Currency, GDP growth, Inflation |
| Tag Clouds / Chips | Languages, Platforms, Product categories |
| Narrative Cards | Psychology, Mindset, Cultural notes |

### Backend / Database JSON Structure
```json
{
  "country_code": "IN",
  "modules": {
    "identity": { }, "demographics": { }, "economy": { },
    "tax": { }, "psychology": { }, "consumption": { },
    "seasonality": { }, "digital": { }, "payments": { },
    "logistics": { }, "legal": { }, "language": { },
    "community": { }, "marketing": { }, "competition": { },
    "customer_service": { }, "technology": { }, "news": { },
    "risk": { }, "strategy": { }
  },
  "last_updated": "2026-07-25",
  "data_sources": ["REST Countries API", "World Bank", "OpenAI Research"]
}
```

### E-commerce System Integration Mapping
| Data Point | System Use |
|------------|------------|
| Currency + Exchange Rate | Dynamic pricing, checkout display |
| Tax Slabs | Cart tax calculation |
| Payment Methods | Checkout gateway selection |
| COD % | Enable/disable COD option |
| Language | UI localization, product descriptions |
| Cities | Shipping zone configuration |
| Return Window | Return policy display |
| Prohibited Items | Product listing filters |
| Peak Hours | Ad scheduling, server scaling |
| Size Preferences | Size chart localization |
| Festival Calendar | Automated sale campaigns |

---

## 6) Worked Example: Pakistan Market Gap Analysis

The Pakistan research (see `PAKISTAN_MARKET_PROBLEM.md`) is a real example of this feature's output translated into action. It demonstrates how country intelligence drives strategy.

### Key Gaps Identified
1. **Trust & Returns** — COD dominates 55-65% of orders but with 12-18% return/refusal rates (fashion up to 25%, electronics ~10%). Customers fear scams, fakes, slow refunds.
2. **Supplier Cash-Flow & Payouts** — sellers on Daraz/social commerce wait weeks for payouts; small shops lack working capital.
3. **Tier-2/3 City Coverage** — Karachi/Lahore/Islamabad ≈66% of orders; 200+ other cities ≈24%, underserved with weak logistics and trust.
4. **Payment Infrastructure** — mobile wallets (JazzCash + Easypaisa) exceed card share 3-4x; many stores lack native wallet flows.
5. **Conversion & Abandonment** — cart abandonment ~72% from hidden fees, poor mobile UX, distrust.
6. **Social Commerce Fragmentation** — up to 35% of sales via Facebook/Instagram/WhatsApp, unstructured and scam-prone.
7. **Product-Category Gaps** — Fashion (~30%, highest returns/counterfeit), Electronics (~22%, warranty disputes), Beauty (~12%, fastest growing, halal/indie underserved), Home (~10%), Groceries (~8%), Books (~5%), Other (~13%).

### Strategic USP (derived by the feature)
"Trust Delivered — Transparent pricing, verified fulfillment, and instant supplier payouts." Position as a trust-first marketplace for underserved cities and suppliers, NOT a head-on Daraz competitor. Wallet-first checkout, FastPay (24-48h payouts), True Final Price Guarantee, local verified shop networks.

### Returns Reduction Playbook (30-90 days)
- **Root causes:** product mismatch, counterfeits, poor info, hidden costs, slow refunds, transit damage, COD/impulse, weak warranties, social fraud.
- **Product controls:** tight SKU curation, verified suppliers only, grading/certification.
- **UX controls:** True Final Price, size/fit tools, high-quality visuals, variant clarity.
- **Trust signals:** Verified Dispatch Video, seller transparency, escrow/wallet hold.
- **Fulfillment:** standardized packaging, QC at pickup, transit insurance.
- **Policy:** clear short returns window, fast refunds/instant credit, replacement-first, local pickup.
- **Supplier incentives:** FastPay conditional on verified dispatch + low disputes; chargebacks for avoidable returns; quality bonus.
- **Experiments:** True Final Price A/B (+8-15% conversion), Verified Dispatch Pilot (-30-50% returns), Size Guidance Widget (-25% size returns), Replacement-First SLA (-40% refunds), COD Reduction Campaign (+20-30% prepaid), Packaging Upgrade (-50% damage).

### QC Pipeline (applies to Pakistan & Oman)
Pre-Dispatch QC → In-Transit Protection → Post-Delivery Verification → Returns Intake & Grading → Refurbish/Certify/Resell, with SOPs, KPIs, supplier scorecards, and a 30-day pilot plan.

This example shows how the auto-research feature produces not just data, but a prioritized, executable market-entry and operations plan — exactly what feeds the Country Onboarding wizard.

---

## 7) Output Formats Produced

- **JSON** — normalized 20-module structure with `confidence`, `verification_notes`, `sources` on qualitative fields; ideal for seeding `country_configs` during onboarding.
- **Markdown** — human-readable narrative report.
- **Single-page dashboard** — the operator-facing UI with all presentation elements above.

### Qualitative Module Schema (returned by Ollama / flagged for review)
Modules 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20 each return a structured object with domain fields plus `confidence`, `verification_notes`, and `sources`. Example keys: `tax_system_overview`, `standard_tax_percentage`, `tax_slabs`; `price_sensitivity_1_to_10`, `brand_loyalty_1_to_10`; `most_popular_payment_method`, `top_payment_gateways`, `cod_percentage`; `market_entry_strategy`, `recommended_product_mix`, `recommended_payment_stack`.

---

## 8) Research Engine Internals (Script Architecture)

The reference implementation is `free_country_ecommerce_research.py`, a single self-contained Python script (class `FreeEcommerceCountryResearch`). It is the engine behind the single-page feature and can run locally or server-side.

### 8.1 Method Pipeline
| Method | Responsibility |
|--------|----------------|
| `fetch_basic()` | Resolves country via REST Countries API (fullText first, fallback to partial match); extracts name, codes, capital, currency, calling code, region, flag, languages, maps, coordinates. |
| `worldbank_latest(indicator)` | Fetches the newest available year for a World Bank indicator (iterates 1960→current year, keeps highest-year non-null value). |
| `fetch_economy()` | Pulls ~11 indicators (population, urbanization, literacy, internet users %, GDP, GDP/capita PPP, growth, inflation, unemployment, Gini, debt, current account) + currency + live exchange rate. |
| `fetch_exchange(code)` | Frankfurter ECB primary; `open.er-api.com` fallback; fixed 1.0 for USD. |
| `fetch_cities()` | GeoNames (if username) → CountriesNow API → capital-city fallback; sorted by population. |
| `fetch_wikipedia()` | Wikipedia REST summary (with search fallback) for narrative context. |
| `fetch_news()` | Google News RSS filtered to economy/ecommerce/tax/consumer/payments; tries last-1-day first, falls back to broader query. |
| `fetch_web_evidence()` | DuckDuckGo search per qualitative module (recent-month window) for tax/payments/rules/behavior; compacted to title/href/snippet. |
| `build_ai_input()` | Assembles basic facts, demographics, economy, news titles, and compacted web evidence into the AI payload. |
| `build_prompt()` | Wraps facts + `AI_SCHEMA` into a strict "return ONLY valid JSON" instruction; truncates >90k chars. |
| `generate_ai_modules()` | Calls local Ollama `/api/chat` (temperature 0.2, num_ctx 8192, `format: json`); selects installed model automatically; parses JSON robustly. |
| `placeholder_modules()` | If Ollama is unavailable, marks each qualitative module `raw_evidence_only` or `needs_local_ai_or_manual_research` with `confidence: low`. |
| `apply_ai_modules()` | Merges AI output (or placeholders + raw evidence) into the final report. |
| `build_meta()` | Records generation time, resolved name, freshness (exchange date, World Bank latest years, news count, evidence module count), data sources, and a disclaimer. |
| `write_markdown()` | Emits a human-readable markdown report (per-module JSON blocks). |
| `run()` | Orchestrates the full sequence and writes both JSON + Markdown files. |

### 8.2 Web-Evidence Query Map
Each qualitative module is backed by targeted DuckDuckGo queries (e.g. `"{country} ecommerce tax VAT GST rate {year}"`, `"{country} import duty de minimis threshold ecommerce {year}"`, `"{country} popular payment gateways digital wallets COD {year}"`, `"{country} top ecommerce marketplaces market share {year}"`). Queries use `timelimit="m"` (recent month) with a retry without the limit on failure.

### 8.3 Ollama Prompt Guardrails
The AI is explicitly instructed:
- Use only provided facts, latest news titles, and web evidence.
- **Do not invent exact legal or tax numbers** — use `"unknown"` for missing fields.
- Mention uncertainty in `verification_notes` unless evidence clearly supports a number.
- Return ONLY valid JSON (no markdown, no comments, no trailing commas).
- Low temperature (0.2) for factual consistency; 8k context window.

### 8.4 Model Auto-Selection
If the requested `OLLAMA_MODEL` isn't installed, the engine matches by base name (e.g. `llama3`) or falls back to the first available local model. Recommended: `llama3.1`; low-RAM alternative `llama3.2:3b`.

### 8.5 Report Module Structure
```
meta
module_01_country_identity      (+ wikipedia_summary)
module_02_demographics
module_03_economy_wealth
module_04_tax_duties
module_05_consumer_psychology
module_06_consumption_preferences
module_07_shopping_seasonality
module_08_digital_landscape
module_09_payment_infrastructure
module_10_logistics_shipping
module_11_legal_regulations
module_12_language_communication
module_13_community_social
module_14_marketing_advertising
module_15_competition
module_16_customer_service
module_17_technology_infrastructure
module_18_news_current_context   (+ latest_news_rss)
module_19_risk_compliance
module_20_strategic_recommendations
appendix_web_evidence
```

### 8.6 How "Latest" Is Achieved
| Data Type | Freshness Method |
|-----------|-----------------|
| Country code, currency, language | REST Countries |
| Population, GDP, inflation, unemployment | World Bank latest available year |
| Exchange rate | Frankfurter ECB latest business day, fallback open.er-api |
| News | Google News RSS, tries last 1 day first |
| Tax, payments, rules | DuckDuckGo search evidence from recent month |
| AI analysis | Uses collected latest evidence + current date |

---

## 9) Production Safety & Verification Logic

This feature is a research aid, not an authority. For a production commerce system, never blindly use AI-generated legal/tax/payment values.

### 9.1 Confidence Decision Tree
```
If confidence = high AND source is official:
    use directly

If confidence = medium:
    use as default but flag for review

If confidence = low:
    require manual verification before enabling
    checkout, tax, shipping, or payment rules
```

### 9.2 Recommended System Usage (field → action)
| Report Field | E-commerce Use |
|--------------|----------------|
| `currency_code` | Set checkout currency |
| `exchange_rate_usd` | Convert prices |
| `module_04_tax_duties` | Configure tax rules |
| `module_09_payment_infrastructure` | Show/hide payment gateways |
| `module_09...cod_percentage` | Enable/disable COD |
| `module_10_logistics_shipping` | Configure shipping zones and couriers |
| `module_11_legal_regulations` | Show return/privacy/tax-invoice rules |
| `module_12_language_communication` | Localize website language |
| `module_07_shopping_seasonality` | Schedule campaigns |
| `module_05_consumer_psychology` | Adjust UI, discounts, trust badges |
| `module_19_risk_compliance` | Trigger fraud-review rules |
| `module_20_strategic_recommendations` | Admin market-entry insights |

### 9.3 Official Sources for Higher Accuracy
For critical production data, verify against per-country official sources: tax authority, customs authority, central bank, payment-gateway documentation, government consumer-protection agency, official statistics bureau, and legal compliance database. The free automated engine is the systematic foundation; official verification closes the remaining gap before publish.

---

## 10) Relationship to the Companion Feature

The intelligence produced here is the **input** to `COUNTRY_ADMIN_ONBOARDING_SYSTEM.md`:
- Research modules 3 (currency/exchange), 4 (tax), 9 (payments), 10 (logistics), 11 (legal KYC), 19 (risk) map directly to `country_configs` fields and the heuristic engine's defaults.
- The Onboarding Wizard can auto-populate a new country's configuration package from this JSON, then route it through draft → approve → publish.
- Confidence flags tell the admin which values must be verified by compliance before publishing.

---

## 11) Operating Principles
- Any country in the world can be researched with one input — no code changes.
- All data sources are free; no paid API key required for core operation.
- Uncertainty is explicit: never present unverified tax/law/gateway data as final.
- Output is both human-readable and machine-actionable (JSON → onboarding seed).
