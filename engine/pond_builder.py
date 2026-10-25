import os
import json
import re
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone

# ==========================================
# ENVIRONMENT CONFIGURATION
# ==========================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
SITE_BASE_URL = os.environ.get("SITE_BASE_URL", "https://hanifsalman11.github.io/pond-liner-index").rstrip("/")
INDEXNOW_KEY = os.environ.get("INDEXNOW_KEY", "d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3").strip()
CUSTOM_POND = os.environ.get("CUSTOM_POND", "").strip()
PAGES_PER_RUN = int(os.environ.get("PAGES_PER_RUN", "3"))

DOCS_DIR = "docs"
DATA_DIR = "data"
PUBLISHED_FILE = os.path.join(DATA_DIR, "published_ponds.json")
MONETIZATION_FILE = os.path.join(DATA_DIR, "monetization.json")

# Format: (Pond / Equipment Name, Length Ft, Width Ft, Max Depth Ft, Waterfall Weir Inches, Pipe Dia Inches)
SEED_PONDS = [
    ("10x15x3 Ft Backyard Koi Pond & Waterfall Setup", 15.0, 10.0, 3.0, 18, 2.0),
    ("8x12x2.5 Ft Garden Water Feature & Goldfish Pond", 12.0, 8.0, 2.5, 12, 1.5),
    ("12x20x3.5 Ft Dedicated Koi Pond & Stream Setup", 20.0, 12.0, 3.5, 24, 2.0),
    ("6x8x2 Ft Compact Patio & Courtyard Water Garden", 8.0, 6.0, 2.0, 8, 1.25),
    ("15x25x4 Ft Large Estate Koi Pond & Bog Filter", 25.0, 15.0, 4.0, 30, 2.5),
    ("10x10x3 Ft Square Zen Deck Koi Pond Setup", 10.0, 10.0, 3.0, 16, 1.5),
    ("4x6x2 Ft Small Preformed-Style Liner Patio Pond", 6.0, 4.0, 2.0, 8, 1.0),
    ("20x30x4.5 Ft Trophy Koi & Natural Swim Pond", 30.0, 20.0, 4.5, 36, 3.0),
    ("Aquascape AquaForce 2700 GPH Solids-Handling Pump", 12.0, 8.0, 2.5, 14, 1.5),
    ("Aquascape AquaForce 5200 GPH Waterfall & Skimmer Pump", 16.0, 11.0, 3.0, 24, 2.0),
    ("Aquascape SLD 4000-7000 Variable Flow Pond Pump", 18.0, 12.0, 3.5, 26, 2.0),
    ("OASE AquaMax Eco Premium 3000 GPH Koi Pond Pump", 14.0, 9.0, 3.0, 16, 1.5),
    ("OASE AquaMax Eco Premium 4000 GPH Waterfall Pump", 16.0, 10.0, 3.0, 20, 2.0),
    ("OASE BioSmart 5000 & 10000 Flow-Through Filter System", 15.0, 10.0, 3.0, 18, 1.5),
    ("OASE FiltoClear 4000 & 8000 Pressurized UV Bio-Filter", 14.0, 10.0, 3.0, 16, 2.0),
    ("Laguna Max-Flo 2400 GPH Waterfall & Filter Pump", 12.0, 8.0, 2.5, 14, 1.5),
    ("Laguna Max-Flo 4280 GPH High-Efficiency Koi Pump", 16.0, 11.0, 3.0, 22, 2.0),
    ("Laguna Pressure-Flo 3000 & 4000 UV Pond Filter", 12.0, 9.0, 2.5, 14, 1.5),
    ("Atlantic Water Gardens TT3000 & TT4000 TidalWave Pump", 15.0, 10.0, 3.0, 20, 2.0),
    ("Atlantic Water Gardens FastFalls 24-Inch Spillway Setup", 16.0, 10.0, 3.0, 24, 2.0),
    ("Savio Skimmerfilter & Livingponds 16-Inch Waterfall", 14.0, 10.0, 3.0, 16, 2.0),
    ("TetraPond Debris-Handling 1900 & 3000 GPH Pump Setup", 11.0, 8.0, 2.5, 12, 1.5),
    ("Alpine Corporation 3100 GPH Cyclone Waterfall Pump", 13.0, 9.0, 2.5, 18, 1.5),
    ("PondMax PV2700 & PF3600 Pressurized UV Filter Setup", 12.0, 8.0, 3.0, 14, 1.5),
    ("14-Foot Pondless Waterfall Stream & Basin Vault Setup", 14.0, 4.0, 2.0, 22, 2.0),
    ("Upflow Wetland Bog Filter & Koi Pond Sizing (12x16 Ft)", 16.0, 12.0, 3.5, 22, 2.0),
    ("3,000 Gallon Predator-Safe Deep Koi Pond (12x15x3.5 Ft)", 15.0, 12.0, 3.5, 20, 2.0),
    ("1,500 Gallon Backyard Water Garden (9x13x2.5 Ft)", 13.0, 9.0, 2.5, 14, 1.5),
    ("5,000 Gallon Dedicated Koi Sanctuary (16x22x4.0 Ft)", 22.0, 16.0, 4.0, 28, 2.5),
    ("Firestone PondGard 45-Mil EPDM Liner & Underlayment", 15.0, 10.0, 3.0, 18, 2.0)
]


def load_json(filepath, default):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARN] Could not parse {filepath}: {e}")
    return default


def save_json(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    return re.sub(r"[\s-]+", "-", text).strip("-")


def safe_float(val, default=12.0):
    try:
        cleaned = re.sub(r"[^0-9.]", "", str(val))
        return float(cleaned) if cleaned else float(default)
    except Exception:
        return float(default)


def build_amazon_url(search_keywords, mon_cfg):
    domain = mon_cfg.get("marketplace_domain", "www.amazon.com")
    tag = mon_cfg.get("amazon_associate_tag", "YOUR_AMAZON_TAG-20")
    encoded_q = urllib.parse.quote_plus(search_keywords)
    return f"https://{domain}/s?k={encoded_q}&tag={tag}"


def discover_google_pond_queries():
    """Mengambil kueri kalkulator ukuran terpal kolam & pompa air terjun dari Google Autocomplete US."""
    discovered = []
    seeds = [
        "pond liner calculator for ",
        "what size pond pump for ",
        "koi pond filter size for ",
        "aquascape pond pump "
    ]
    for seed in seeds:
        try:
            url = f"http://suggestqueries.google.com/complete/search?client=firefox&hl=en&gl=us&q={urllib.parse.quote(seed)}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for suggestion in data[1]:
                    cleaned = suggestion.lower()
                    for pref in seeds:
                        if "calculator" in pref or "what size" in pref:
                            cleaned = cleaned.replace(pref, "")
                    cleaned = re.sub(
                        r"\b(calculator|size|sizing|gph|chart|review|reddit|for)\b",
                        "",
                        cleaned
                    ).strip()
                    if 5 <= len(cleaned) <= 42:
                        discovered.append((cleaned.title(), 14.0, 10.0, 3.0, 18, 2.0))
        except Exception as e:
            print(f"[WARN] Google Suggest notice: {e}")
    return discovered


def build_deterministic_pond_data(pond_tuple):
    """Mesin Fisika Geometri EPDM Liner & Hidrolik Air Terjun GPH (100% bebas gagal)."""
    item_name, len_ft, wid_ft, depth_ft, weir_in, pipe_in = pond_tuple

    # Rumus Ukuran Terpal EPDM Liner (dengan 2 kaki overlap tepi batu di setiap sisi):
    # Liner Length = Pond Length + (2 * Max Depth) + 2 ft
    # Liner Width  = Pond Width  + (2 * Max Depth) + 2 ft
    liner_len_ft = int(round(len_ft + (2.0 * depth_ft) + 2.0))
    liner_wid_ft = int(round(wid_ft + (2.0 * depth_ft) + 2.0))
    underlay_sqft = int(round(liner_len_ft * liner_wid_ft))

    # Rumus Volume Galon Kolam (dengan faktor kontur rak tanaman/bahu miring 0.80):
    # Gallons = Length * Width * Max_Depth * 0.80 * 7.48052 gal/cu.ft
    est_gallons = int(round((len_ft * wid_ft * depth_ft * 0.80 * 7.48052), -1))

    # Kebutuhan GPH Pompa: Ambil nilai tertinggi antara:
    # 1. Sirkulasi penuh kolam setiap 1 jam (est_gallons GPH)
    # 2. Aliran air terjun (125 GPH per inci lebar weir spillway)
    waterfall_gph = weir_in * 125
    target_net_gph = max(est_gallons, waterfall_gph)
    # Tambahkan 25% kompensasi TDH (Total Dynamic Head loss dari tinggi air terjun + gesekan pipa)
    recommended_pump_gph = int(round(target_net_gph * 1.25, -2))

    # Ukuran lampu UV-C Clarifier untuk mengatasi ganggang hijau (Green Water Algae)
    if est_gallons <= 1500:
        uv_watts = 18
    elif est_gallons <= 3000:
        uv_watts = 36
    elif est_gallons <= 5000:
        uv_watts = 55
    else:
        uv_watts = 75

    return {
        "pond_name": item_name,
        "seo_title": f"{item_name} EPDM Liner Size, Gallons & Pump GPH Calculator (2026)",
        "meta_description": f"Calculate exact 45-mil EPDM pond liner size ({liner_wid_ft}'×{liner_len_ft}'), water volume ({est_gallons:,} gallons), waterfall pump flow ({recommended_pump_gph:,} GPH), and {uv_watts}W UV bio-filter for {item_name}.",
        "specs": {
            "pond_length_ft": len_ft,
            "pond_width_ft": wid_ft,
            "max_depth_ft": depth_ft,
            "liner_length_ft": liner_len_ft,
            "liner_width_ft": liner_wid_ft,
            "underlayment_sqft": underlay_sqft,
            "estimated_gallons": est_gallons,
            "waterfall_weir_inches": weir_in,
            "recommended_pump_gph": recommended_pump_gph,
            "recommended_pipe_inches": pipe_in,
            "recommended_uv_watts": uv_watts
        },
        "hydro_verdict": f"Excavating a {wid_ft}' W × {len_ft}' L × {depth_ft}' deep basin ({item_name}) holds approximately {est_gallons:,} US Gallons (accounting for marginal plant shelves) and requires a {liner_wid_ft} ft × {liner_len_ft} ft ({underlay_sqft} sq. ft.) 45-mil fish-safe EPDM liner with geotextile underlayment. To turn over the pond volume hourly and feed an {weir_in}-inch waterfall spillway ({waterfall_gph:,} GPH sheet flow) against vertical head pressure, install a {recommended_pump_gph:,} GPH solids-handling pump plumbed with {pipe_in}-inch kink-free PVC hose and a {uv_watts}W UV-C pressurized bio-filter.",
        "hardware_bundle": [
            {
                "badge": f"{liner_wid_ft}'×{liner_len_ft}' 45-Mil EPDM",
                "title": f"{liner_wid_ft} ft × {liner_len_ft} ft 45-Mil Fish-Safe EPDM Rubber Pond Liner + Non-Woven Underlayment",
                "price_range": "$189 - $799",
                "amazon_query": f"{liner_wid_ft}x{liner_len_ft} 45 Mil EPDM Pond Liner Underlayment Fish Safe",
                "pond_note": f"Includes a 1-foot perimeter overlap on all 4 sides to anchor securely beneath coping stones without ground-settling tears."
            },
            {
                "badge": f"{recommended_pump_gph:,} GPH Waterfall Pump",
                "title": f"{recommended_pump_gph:,} GPH Asynchronous Solids-Handling Koi Pond & Waterfall Pump",
                "price_range": "$149 - $489",
                "amazon_query": f"{recommended_pump_gph} GPH Koi Pond Waterfall Pump Solids Handling",
                "pond_note": f"Delivers {target_net_gph:,}+ GPH net flow at the top of your {weir_in}-inch waterfall weir after overcoming vertical head and pipe friction."
            },
            {
                "badge": f"{uv_watts}W UV Bio-Filter",
                "title": f"{est_gallons + 1500:,}-Gallon Pressurized Biological Pond Filter with {uv_watts}W UV-C Clarifier",
                "price_range": "$159 - $469",
                "amazon_query": f"Pressurized Pond Bio Filter {uv_watts}W UV Clarifier Koi",
                "pond_note": f"Eliminates single-cell green water algae and converts toxic fish ammonia/nitrites via backwashable bio-media."
            },
            {
                "badge": f"{weir_in}\" Weir & {pipe_in}\" Hose",
                "title": f"{weir_in}-Inch BioFalls Spillway Weir Box + {pipe_in}-Inch Black Kink-Free Spiral PVC Pond Tubing",
                "price_range": "$89 - $249",
                "amazon_query": f"{weir_in} Inch Waterfall Spillway Weir {pipe_in} Inch Kink Free Pond Tubing",
                "pond_note": f"Smooth-bore {pipe_in}\" spiral PVC prevents friction head loss and creates a thick, aerated {weir_in}\" sheet waterfall."
            }
        ],
        "construction_checklist": [
            f"Always lay non-woven polypropylene Geotextile Underlayment ({underlay_sqft} sq. ft.) beneath your 45-mil EPDM rubber liner to shield against sharp roots, rocks, and hydrostatic ground-frost heave.",
            f"Excavate your Koi pond to at least 3.0 feet deep ({depth_ft}' target) in cold or predator-prone regions; shallow ponds under 24 inches allow raccoons and blue herons to wade in and catch fish.",
            f"Use {pipe_in}-inch Schedule 40 or Black Kink-Free Flexible PVC pipe rather than corrugated sump-pump hose; corrugated ribs create severe turbulence and cut {recommended_pump_gph:,} GPH pump flow by up to 35%.",
            "Place your submersible pump inside a mechanical pond skimmer box (or elevated 4 inches off the deepest bottom floor on a flat stone) so a plumbing leak outside the pond can never drain the entire basin dry."
        ],
        "faqs": [
            {
                "q": f"How do I calculate the exact pond liner size for {item_name}?",
                "a": f"Use the standard excavation formula: Liner Length = Pond Length ({len_ft}') + (2 × Max Depth [{depth_ft}']) + 2 ft overlap = {liner_len_ft} feet. Liner Width = Pond Width ({wid_ft}') + (2 × Max Depth [{depth_ft}']) + 2 ft overlap = {liner_wid_ft} feet. Order a {liner_wid_ft}' × {liner_len_ft}' 45-mil EPDM sheet."
            },
            {
                "q": f"How many GPH pump do I need for a {est_gallons:,}-gallon pond with an {weir_in}-inch waterfall?",
                "a": f"A healthy Koi pond requires turning over the entire {est_gallons:,}-gallon volume at least once per hour, while an {weir_in}-inch waterfall weir requires {waterfall_gph:,} GPH (125 GPH per inch of width) for a full cascading sheet. Accounting for 25% vertical head and pipe friction loss, choose a pump rated around {recommended_pump_gph:,} GPH at 0-ft head."
            },
            {
                "q": f"Should I use 45-mil EPDM or 20-mil PVC/HDPE liner for {item_name}?",
                "a": f"Professional pond builders exclusively recommend 45-mil Fish-Safe EPDM synthetic rubber. Unlike stiff 20-mil PVC (which plasticizer-hardens and cracks under UV sunlight in 5–7 years), 45-mil EPDM stretches 300% around shelf contours and lasts 30 to 40+ years."
            }
        ]
    }


def generate_pond_data(pond_tuple):
    """Memanggil Gemini 2.5 Flash API; jika gagal otomatis memakai Deterministic Hydro-Geometric Engine."""
    if not GEMINI_API_KEY:
        return build_deterministic_pond_data(pond_tuple)

    item_name, len_ft, wid_ft, depth_ft, weir_in, pipe_in = pond_tuple
    liner_len = int(round(len_ft + (2.0 * depth_ft) + 2.0))
    liner_wid = int(round(wid_ft + (2.0 * depth_ft) + 2.0))
    underlay_sqft = int(round(liner_len * liner_wid))
    est_gal = int(round((len_ft * wid_ft * depth_ft * 0.80 * 7.48052), -1))
    rec_gph = int(round(max(est_gal, weir_in * 125) * 1.25, -2))
    uv_w = 18 if est_gal <= 1500 else (36 if est_gal <= 3000 else 55)

    prompt = f"""
You are a Certified Master Aquascape Contractor & Hydraulic Water Garden Engineer. Create an accurate 2026 EPDM pond liner size, gallon volume, waterfall GPH flow rate, and UV bio-filter sizing guide for: "{item_name}".
Baseline reference specs: Basin={wid_ft}' W x {len_ft}' L x {depth_ft}' D, Liner Needed={liner_wid}' x {liner_len}' ({underlay_sqft} sq ft), Volume={est_gal} Gallons, Waterfall Weir={weir_in} Inches, Recommended Pump={rec_gph} GPH ({pipe_in}\" Pipe), UV Clarifier={uv_w}W.
Return ONLY a valid JSON object matching this exact schema:
{{
  "pond_name": "{item_name}",
  "seo_title": "{item_name} EPDM Liner Size, Gallons & Pump GPH Calculator (2026)",
  "meta_description": "Calculate exact 45-mil EPDM pond liner dimensions, water volume in gallons, waterfall GPH pump flow, and UV bio-filter sizing for {item_name}.",
  "specs": {{
    "pond_length_ft": {len_ft},
    "pond_width_ft": {wid_ft},
    "max_depth_ft": {depth_ft},
    "liner_length_ft": {liner_len},
    "liner_width_ft": {liner_wid},
    "underlayment_sqft": {underlay_sqft},
    "estimated_gallons": {est_gal},
    "waterfall_weir_inches": {weir_in},
    "recommended_pump_gph": {rec_gph},
    "recommended_pipe_inches": {pipe_in},
    "recommended_uv_watts": {uv_w}
  }},
  "hydro_verdict": "3-sentence technical summary stating pond gallons, exact EPDM liner feet dimensions, waterfall GPH flow requirement, pipe diameter, and UV clarifier wattage.",
  "hardware_bundle": [
    {{
      "badge": "45-Mil EPDM Liner",
      "title": "Exact {liner_wid}' x {liner_len}' 45-Mil Fish-Safe EPDM Pond Liner + Underlayment",
      "price_range": "$189 - $799",
      "amazon_query": "{liner_wid}x{liner_len} 45 Mil EPDM Pond Liner Underlayment",
      "pond_note": "1-sentence puncture resistance and overlap note"
    }},
    {{
      "badge": "Waterfall & Koi Pump",
      "title": "Exact {rec_gph} GPH Solids-Handling Waterfall & Koi Pond Pump",
      "price_range": "$149 - $489",
      "amazon_query": "{rec_gph} GPH Koi Pond Waterfall Pump",
      "pond_note": "1-sentence head pressure and turnover note"
    }},
    {{
      "badge": "UV Pressurized Bio-Filter",
      "title": "Pressurized Biological Pond Filter with {uv_w}W UV-C Clarifier",
      "price_range": "$159 - $469",
      "amazon_query": "Pressurized Pond Bio Filter {uv_w}W UV Clarifier",
      "pond_note": "1-sentence ammonia conversion and green water clarity note"
    }},
    {{
      "badge": "Spillway & Kink-Free Hose",
      "title": "{weir_in}-Inch Waterfall Spillway Weir + {pipe_in}-Inch Kink-Free Spiral PVC Tubing",
      "price_range": "$89 - $249",
      "amazon_query": "{weir_in} Inch Waterfall Spillway {pipe_in} Inch Pond Tubing",
      "pond_note": "1-sentence friction loss prevention note"
    }}
  ],
  "construction_checklist": [
    "Step 1 regarding geotextile underlayment protection under 45-mil EPDM",
    "Step 2 regarding 3-foot minimum depth for predator and winter freeze safety",
    "Step 3 regarding smooth-bore spiral PVC vs corrugated hose friction loss",
    "Step 4 regarding skimmer placement and check valve installation"
  ],
  "faqs": [
    {{"q": "What size pond liner do I need for {item_name}?", "a": "Exact L + 2D + 2 overlap formula in feet."}},
    {{"q": "How many GPH pump do I need for {est_gal} gallons and an {weir_in}-inch waterfall?", "a": "Exact GPH calculation combining turnover and 125 GPH/inch weir flow."}},
    {{"q": "What size UV clarifier and bio-filter do I need for {est_gal} gallons?", "a": "Exact UV watts and biological filter rating for Koi vs Goldfish."}}
  ]
}}
"""

    for model_id in ["gemini-2.5-flash", "gemini-2.0-flash"]:
        try:
            endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={GEMINI_API_KEY}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.2,
                    "responseMimeType": "application/json"
                }
            }
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=35) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                raw_text = result["candidates"][0]["content"]["parts"][0]["text"].strip()
                raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
                raw_text = re.sub(r"\s*```$", "", raw_text)
                parsed = json.loads(raw_text)
                if "specs" in parsed and "hardware_bundle" in parsed:
                    return parsed
        except Exception as e:
            print(f"[WARN] Gemini ({model_id}) notice for '{item_name}': {e}")

    return build_deterministic_pond_data(pond_tuple)


def build_pond_html_page(data, slug, mon_cfg):
    pond_name = data.get("pond_name", "Koi Pond & Waterfall")
    sp = data.get("specs", {})
    len_ft = round(safe_float(sp.get("pond_length_ft", 15.0), 15.0), 1)
    wid_ft = round(safe_float(sp.get("pond_width_ft", 10.0), 10.0), 1)
    depth_ft = round(safe_float(sp.get("max_depth_ft", 3.0), 3.0), 1)
    liner_len = int(safe_float(sp.get("liner_length_ft", 23), 23))
    liner_wid = int(safe_float(sp.get("liner_width_ft", 18), 18))
    underlay_sqft = int(safe_float(sp.get("underlayment_sqft", liner_len * liner_wid), 414))
    est_gal = int(safe_float(sp.get("estimated_gallons", 2690), 2690))
    weir_in = int(safe_float(sp.get("waterfall_weir_inches", 18), 18))
    rec_gph = int(safe_float(sp.get("recommended_pump_gph", 3400), 3400))
    pipe_in = round(safe_float(sp.get("recommended_pipe_inches", 2.0), 2.0), 2)
    uv_w = int(safe_float(sp.get("recommended_uv_watts", 36), 36))

    header_cta = mon_cfg.get("header_cta", {})
    header_cta_url = build_amazon_url(header_cta.get("search_query", "45+Mil+EPDM+Pond+Liner+Waterfall+Pump"), mon_cfg)

    schema_graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "SoftwareApplication",
                "name": f"{pond_name} EPDM Liner & Waterfall GPH Calculator",
                "applicationCategory": "UtilitiesApplication",
                "operatingSystem": "Web Browser",
                "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}
            },
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": f.get("q", ""),
                        "acceptedAnswer": {"@type": "Answer", "text": f.get("a", "")}
                    } for f in data.get("faqs", [])
                ]
            }
        ]
    }

    bundle_html = ""
    for item in data.get("hardware_bundle", []):
        amz_url = build_amazon_url(item.get("amazon_query", item.get("title", "45 Mil EPDM Pond Liner")), mon_cfg)
        bundle_html += f"""
        <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col justify-between hover:border-teal-500/60 transition">
          <div>
            <div class="flex items-center justify-between gap-2 mb-2">
              <span class="text-xs font-bold uppercase tracking-wider bg-teal-500/10 text-teal-400 border border-teal-500/20 px-2.5 py-0.5 rounded">{item.get('badge', 'Pond Gear')}</span>
              <span class="text-sm font-bold text-emerald-400">{item.get('price_range', '$89+')}</span>
            </div>
            <h3 class="text-base font-bold text-white mt-2">{item.get('title', '')}</h3>
            <p class="text-xs text-slate-400 mt-2 leading-relaxed">🐟 {item.get('pond_note', '')}</p>
          </div>
          <a href="{amz_url}" target="_blank" rel="nofollow sponsored" class="mt-5 block text-center bg-teal-500 hover:bg-teal-400 text-slate-950 font-extrabold py-2.5 px-4 rounded-lg text-sm transition shadow-lg">
            Check Price on Amazon →
          </a>
        </div>"""

    # Build Standard Pond Dimensions vs Liner & Pump Reference Matrix Table
    pond_tiers = [
        ("6' × 8' × 2.0' Patio Pond", "12' × 14' EPDM (168 ft²)", "~575 Gallons", "1,200 GPH (1\" Pipe)", "9W – 13W UV"),
        ("8' × 12' × 2.5' Water Garden", "15' × 19' EPDM (285 ft²)", "~1,435 Gallons", "2,200 GPH (1.5\" Pipe)", "18W UV Clarifier"),
        ("10' × 15' × 3.0' Koi Pond", "18' × 23' EPDM (414 ft²)", "~2,690 Gallons", "3,500 GPH (2.0\" Pipe)", "36W UV Clarifier"),
        ("12' × 20' × 3.5' Koi Pond", "21' × 29' EPDM (609 ft²)", "~5,025 Gallons", "5,500 GPH (2.0\" Pipe)", "55W UV Clarifier"),
        ("15' × 25' × 4.0' Estate Pond", "25' × 35' EPDM (875 ft²)", "~8,975 Gallons", "9,000 GPH (2.5\"–3\" Pipe)", "75W–110W UV")
    ]
    matrix_rows_html = ""
    for p_dim, l_dim, gal_s, pump_s, uv_s in pond_tiers:
        matrix_rows_html += f"""
        <tr class="border-b border-slate-800 hover:bg-slate-800/40">
          <td class="py-3 px-4 font-bold text-white">{p_dim}</td>
          <td class="py-3 px-4 font-bold text-teal-400">{l_dim}</td>
          <td class="py-3 px-4 text-slate-300">{gal_s}</td>
          <td class="py-3 px-4 text-emerald-400 font-semibold">{pump_s}</td>
          <td class="py-3 px-4 text-xs text-slate-300">{uv_s}</td>
        </tr>"""

    checklist_html = ""
    for idx, step_text in enumerate(data.get("construction_checklist", []), start=1):
        checklist_html += f"""
        <label class="flex items-start gap-3.5 bg-slate-900 border border-slate-800 rounded-xl p-4 cursor-pointer hover:border-slate-700 transition">
          <input type="checkbox" class="mt-1 w-5 h-5 accent-teal-500 rounded cursor-pointer pond-check">
          <span class="text-sm text-slate-200 leading-relaxed"><strong>Pond Step {idx}:</strong> {step_text}</span>
        </label>"""

    faqs_html = "".join([
        f"<div class='bg-slate-900 border border-slate-800 rounded-xl p-5'><h3 class='font-bold text-white text-base mb-2'>{f.get('q', '')}</h3><p class='text-sm text-slate-300 leading-relaxed'>{f.get('a', '')}</p></div>"
        for f in data.get("faqs", [])
    ])

    canonical_url = f"{SITE_BASE_URL}/{slug}.html"
    amz_domain = mon_cfg.get("marketplace_domain", "www.amazon.com")
    amz_tag = mon_cfg.get("amazon_associate_tag", "YOUR_AMAZON_TAG-20")

    html = f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{data.get('seo_title', pond_name)}</title>
  <meta name="description" content="{data.get('meta_description', '')}">
  <link rel="canonical" href="{canonical_url}">
  <meta property="og:title" content="{data.get('seo_title', pond_name)}">
  <meta property="og:description" content="{data.get('meta_description', '')}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{canonical_url}">
  <script src="https://cdn.tailwindcss.com"></script>
  <script type="application/ld+json">{json.dumps(schema_graph)}</script>
</head>
<body class="bg-slate-950 text-slate-100 antialiased min-h-screen flex flex-col">
  <header class="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-30">
    <div class="max-w-5xl mx-auto px-4 py-3.5 flex items-center justify-between">
      <a href="index.html" class="text-lg font-black tracking-tight text-white flex items-center gap-2">
        <span class="bg-teal-500 text-slate-950 px-2 py-0.5 rounded font-black">POND</span>LinerIndex
      </a>
      <a href="{header_cta_url}" target="_blank" rel="nofollow sponsored" class="text-xs sm:text-sm bg-teal-500 hover:bg-teal-400 text-slate-950 font-extrabold px-3.5 py-2 rounded-lg transition">
        {header_cta.get('cta_text', 'Shop EPDM Liners & Pumps →')}
      </a>
    </div>
  </header>

  <main class="max-w-5xl mx-auto px-4 py-10 flex-1 w-full">
    <div class="mb-8">
      <div class="flex flex-wrap items-center gap-2.5 mb-3">
        <span class="text-xs font-extrabold uppercase tracking-widest bg-teal-500 text-slate-950 px-3 py-1 rounded-full">Liner: {liner_wid}' × {liner_len}' (45-Mil)</span>
        <span class="text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-3 py-1 rounded-full">Volume: ~{est_gal:,} Gal | Pump: {rec_gph:,} GPH</span>
        <span class="text-xs font-semibold bg-slate-800 text-slate-300 px-3 py-1 rounded-full">{weir_in}" Waterfall | {uv_w}W UV Bio-Filter</span>
      </div>
      <h1 class="text-3xl sm:text-4xl font-black text-white leading-tight">{data.get('seo_title', pond_name)}</h1>
      <div class="mt-4 bg-slate-900 border-l-4 border-teal-500 p-4 rounded-r-xl text-sm text-slate-200 leading-relaxed">
        <strong>Aquascape Hydraulic & Liner Sizing Verdict:</strong> {data.get('hydro_verdict', '')}
      </div>
    </div>

    <!-- INTERACTIVE EPDM LINER SIZE, GALLON VOLUME & WATERFALL GPH CALCULATOR -->
    <section class="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 mb-12 shadow-2xl">
      <h2 class="text-xl font-extrabold text-white mb-2">Interactive {pond_name} Liner, Gallon & GPH Calculator</h2>
      <p class="text-xs text-slate-400 mb-6">Slide your excavated pond length, width, maximum depth, and waterfall spillway width to compute exact 45-mil EPDM liner dimensions, water gallons, pump GPH, and UV clarifier wattage.</p>

      <div class="grid md:grid-cols-2 gap-8 items-center">
        <div class="space-y-5">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <div class="flex justify-between text-xs font-medium mb-1">
                <label for="lenSlider" class="text-slate-300">Pond Length (Ft)</label>
                <span class="text-teal-400 font-bold"><span id="lenVal">{len_ft}</span> ft</span>
              </div>
              <input id="lenSlider" type="range" min="4" max="35" step="1" value="{int(len_ft)}" class="w-full accent-teal-500 cursor-pointer">
            </div>
            <div>
              <div class="flex justify-between text-xs font-medium mb-1">
                <label for="widSlider" class="text-slate-300">Pond Width (Ft)</label>
                <span class="text-teal-400 font-bold"><span id="widVal">{wid_ft}</span> ft</span>
              </div>
              <input id="widSlider" type="range" min="4" max="25" step="1" value="{int(wid_ft)}" class="w-full accent-teal-500 cursor-pointer">
            </div>
          </div>

          <div>
            <div class="flex justify-between text-sm font-medium mb-1.5">
              <label for="depthSlider" class="text-slate-300">Maximum Excavated Depth (Feet — Min 3.0' for Koi)</label>
              <span class="text-teal-400 font-bold"><span id="depthVal">{depth_ft}</span> ft</span>
            </div>
            <input id="depthSlider" type="range" min="1.5" max="5.0" step="0.5" value="{depth_ft}" class="w-full accent-teal-500 cursor-pointer">
          </div>

          <div>
            <div class="flex justify-between text-sm font-medium mb-1.5">
              <label for="weirSlider" class="text-slate-300">Waterfall Spillway Weir Width (Inches @ 125 GPH/in)</label>
              <span class="text-teal-400 font-bold"><span id="weirVal">{weir_in}</span>" Spillway</span>
            </div>
            <input id="weirSlider" type="range" min="6" max="42" step="2" value="{weir_in}" class="w-full accent-teal-500 cursor-pointer">
          </div>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div class="bg-slate-950 border border-teal-500/30 rounded-xl p-4">
            <span class="text-xs uppercase text-teal-400 font-bold">Required EPDM Liner</span>
            <div id="linerOut" class="text-xl sm:text-2xl font-black text-white mt-1">{liner_wid}' × {liner_len}'</div>
            <p id="galOut" class="text-xs text-teal-400 font-semibold mt-1">Volume: ~{est_gal:,} Gallons</p>
          </div>

          <div class="bg-slate-950 border border-emerald-500/30 rounded-xl p-4">
            <span class="text-xs uppercase text-emerald-400 font-bold">Pump & UV Bio-Filter</span>
            <div id="gphOut" class="text-xl sm:text-2xl font-black text-emerald-400 mt-1">{rec_gph:,} GPH</div>
            <p id="uvPipeOut" class="text-xs text-slate-300 font-semibold mt-1">{uv_w}W UV | {pipe_in}" Kink-Free Pipe</p>
          </div>
        </div>
      </div>

      <div class="mt-6 bg-teal-950/40 border border-teal-500/30 rounded-xl p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div id="pondAdviceBanner" class="text-sm text-teal-100 font-medium"></div>
        <a id="dynamicPondBtn" href="{header_cta_url}" target="_blank" rel="nofollow sponsored" class="shrink-0 bg-teal-500 hover:bg-teal-400 text-slate-950 font-extrabold px-4 py-2.5 rounded-lg text-xs uppercase tracking-wider transition">
          Shop Matched Liner & Pump on Amazon →
        </a>
      </div>
    </section>

    <!-- 4-CARD HARDWARE BUNDLE -->
    <section class="mb-12">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-2xl font-extrabold text-white">Complete {pond_name} Liner, Pump & Bio-Filter Kit</h2>
        <span class="text-xs text-slate-400">45-Mil Fish-Safe EPDM & Continuous-Duty Rated</span>
      </div>
      <div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">{bundle_html}</div>
    </section>

    <!-- POND SIZE & LINER MATRIX TABLE -->
    <section class="mb-12">
      <h2 class="text-2xl font-extrabold text-white mb-4">Koi Pond Dimensions, EPDM Liner Sheet, GPH Pump & UV Sizing Chart</h2>
      <div class="overflow-x-auto bg-slate-900 border border-slate-800 rounded-xl">
        <table class="w-full text-left border-collapse text-sm">
          <thead>
            <tr class="border-b border-slate-800 bg-slate-950/60 text-slate-400 uppercase text-xs">
              <th class="py-3.5 px-4">Excavated Basin Size</th>
              <th class="py-3.5 px-4 text-teal-400">45-Mil EPDM Liner Sheet</th>
              <th class="py-3.5 px-4">Net Water Volume</th>
              <th class="py-3.5 px-4 text-emerald-400">Recommended Pump & Pipe</th>
              <th class="py-3.5 px-4">UV-C Clarifier</th>
            </tr>
          </thead>
          <tbody>{matrix_rows_html}</tbody>
        </table>
      </div>
    </section>

    <!-- CONSTRUCTION CHECKLIST -->
    <section class="mb-12">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-2xl font-extrabold text-white">Master Pond Builder Excavation & Plumbing Checklist</h2>
        <span id="pondBadge" class="text-xs font-bold bg-slate-800 text-teal-400 px-3 py-1 rounded-full">0 / 4 Completed</span>
      </div>
      <div class="space-y-3">{checklist_html}</div>
    </section>

    <!-- FAQ -->
    <section class="mb-12">
      <h2 class="text-2xl font-extrabold text-white mb-5">Frequently Asked Questions ({pond_name})</h2>
      <div class="space-y-4">{faqs_html}</div>
    </section>
  </main>

  <footer class="border-t border-slate-800 py-8 text-center text-xs text-slate-500 px-4">
    <p>© {datetime.now(timezone.utc).year} PondLinerIndex. Independent Koi Pond Geometrics & Waterfall Hydraulics Database. As an Amazon Associate, we earn from qualifying purchases.</p>
  </footer>

  <script>
    const amzDomain = "{amz_domain}";
    const amzTag = "{amz_tag}";

    const lenSlider = document.getElementById('lenSlider');
    const widSlider = document.getElementById('widSlider');
    const depthSlider = document.getElementById('depthSlider');
    const weirSlider = document.getElementById('weirSlider');
    const lenVal = document.getElementById('lenVal');
    const widVal = document.getElementById('widVal');
    const depthVal = document.getElementById('depthVal');
    const weirVal = document.getElementById('weirVal');
    const linerOut = document.getElementById('linerOut');
    const galOut = document.getElementById('galOut');
    const gphOut = document.getElementById('gphOut');
    const uvPipeOut = document.getElementById('uvPipeOut');
    const pondAdviceBanner = document.getElementById('pondAdviceBanner');
    const dynamicPondBtn = document.getElementById('dynamicPondBtn');

    function recalculatePond() {{
      const lFt = parseFloat(lenSlider.value);
      const wFt = parseFloat(widSlider.value);
      const dFt = parseFloat(depthSlider.value);
      const weirIn = parseInt(weirSlider.value, 10);

      lenVal.textContent = lFt;
      widVal.textContent = wFt;
      depthVal.textContent = dFt.toFixed(1);
      weirVal.textContent = weirIn;

      const reqLinerL = Math.ceil(lFt + (2.0 * dFt) + 2.0);
      const reqLinerW = Math.ceil(wFt + (2.0 * dFt) + 2.0);
      const underlaySqFt = reqLinerL * reqLinerW;

      const estGals = Math.round((lFt * wFt * dFt * 0.80 * 7.48052) / 10) * 10;
      const weirFlowGph = weirIn * 125;
      const netFlowNeeded = Math.max(estGals, weirFlowGph);
      const ratedPumpGph = Math.ceil((netFlowNeeded * 1.25) / 100) * 100;

      let pipeDia = '1.5"';
      if (ratedPumpGph <= 1500) pipeDia = '1.25"';
      else if (ratedPumpGph <= 3200) pipeDia = '1.5"';
      else if (ratedPumpGph <= 6000) pipeDia = '2.0"';
      else pipeDia = '2.5"';

      let uvWatts = 18;
      if (estGals <= 1500) uvWatts = 18;
      else if (estGals <= 3200) uvWatts = 36;
      else if (estGals <= 5500) uvWatts = 55;
      else uvWatts = 75;

      linerOut.textContent = `${{reqLinerW}}' × ${{reqLinerL}}' (${{underlaySqFt}} ft²)`;
      galOut.textContent = `Volume: ~${{estGals.toLocaleString()}} Gallons`;
      gphOut.textContent = `${{ratedPumpGph.toLocaleString()}} GPH`;
      uvPipeOut.textContent = `${{uvWatts}}W UV | ${{pipeDia}} Kink-Free Pipe`;

      pondAdviceBanner.innerHTML = `🐟 <strong>Build Spec:</strong> Order a <strong>${{reqLinerW}}' × ${{reqLinerL}}' 45-Mil EPDM Liner</strong> with underlayment, a <strong>${{ratedPumpGph.toLocaleString()}} GPH Waterfall Pump</strong>, and a <strong>${{uvWatts}}W Pressurized UV Bio-Filter</strong>.`;
      dynamicPondBtn.href = `https://${{amzDomain}}/s?k=${{reqLinerW}}x${{reqLinerL}}+45+Mil+EPDM+Pond+Liner+${{ratedPumpGph}}+GPH+Waterfall+Pump&tag=${{amzTag}}`;
    }}

    lenSlider.addEventListener('input', recalculatePond);
    widSlider.addEventListener('input', recalculatePond);
    depthSlider.addEventListener('input', recalculatePond);
    weirSlider.addEventListener('input', recalculatePond);
    recalculatePond();

    const checks = document.querySelectorAll('.pond-check');
    const badge = document.getElementById('pondBadge');
    checks.forEach(ch => {{
      ch.addEventListener('change', () => {{
        const done = Array.from(checks).filter(c => c.checked).length;
        badge.textContent = `${{done}} / ${{checks.length}} Completed`;
      }});
    }});
  </script>
</body>
</html>"""

    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(os.path.join(DOCS_DIR, f"{slug}.html"), "w", encoding="utf-8") as f:
        f.write(html)


def rebuild_portal_sitemap_and_rss(published, mon_cfg):
    header_cta = mon_cfg.get("header_cta", {})
    header_cta_url = build_amazon_url(header_cta.get("search_query", "45+Mil+EPDM+Pond+Liner+Waterfall+Pump"), mon_cfg)

    cards_html = ""
    for item in reversed(published):
        cards_html += f"""
        <a href="{item['slug']}.html" class="block bg-slate-900 border border-slate-800 hover:border-teal-500/60 rounded-xl p-5 transition group">
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs font-black uppercase bg-teal-500 text-slate-950 px-2.5 py-0.5 rounded">Liner: {item.get('liner_dim', '18x23 ft')}</span>
            <span class="text-xs text-slate-400">~{item.get('gallons', 2690):,} Gal | {item.get('pump_gph', 3400):,} GPH</span>
          </div>
          <h2 class="text-base font-bold text-white group-hover:text-teal-400 transition">{item['pond_name']}</h2>
          <p class="text-xs text-slate-400 mt-2 line-clamp-2">{item['description']}</p>
          <span class="inline-block mt-4 text-xs font-extrabold text-teal-400">Calculate Liner Size, Gallons & GPH →</span>
        </a>"""

    index_html = f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>PondLinerIndex — Koi Pond EPDM Liner Size, Gallons & Waterfall GPH Calculator (2026)</title>
  <meta name="description" content="Calculate exact 45-mil EPDM pond liner dimensions, water volume in gallons, waterfall spillway GPH flow rate, and UV bio-filter sizing for Aquascape, OASE, Laguna, and Atlantic water gardens.">
  <link rel="canonical" href="{SITE_BASE_URL}/">
  <link rel="alternate" type="application/rss+xml" title="PondLinerIndex RSS Feed" href="{SITE_BASE_URL}/rss.xml">
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex flex-col">
  <header class="border-b border-slate-800 bg-slate-900/80 sticky top-0 z-30 backdrop-blur">
    <div class="max-w-5xl mx-auto px-4 py-3.5 flex items-center justify-between">
      <div class="text-lg font-black text-white flex items-center gap-2">
        <span class="bg-teal-500 text-slate-950 px-2 py-0.5 rounded font-black">POND</span>LinerIndex
      </div>
      <a href="{header_cta_url}" target="_blank" rel="nofollow sponsored" class="text-xs sm:text-sm bg-teal-500 hover:bg-teal-400 text-slate-950 font-extrabold px-3.5 py-2 rounded-lg transition">
        {header_cta.get('cta_text', 'Shop EPDM Liners & Pumps →')}
      </a>
    </div>
  </header>

  <main class="max-w-5xl mx-auto px-4 py-12 flex-1 w-full">
    <div class="text-center max-w-2xl mx-auto mb-10">
      <h1 class="text-3xl sm:text-5xl font-black text-white tracking-tight">Koi Pond EPDM Liner, Gallon & Waterfall Pump Database</h1>
      <p class="text-slate-400 mt-3 text-base sm:text-lg">Select your pond dimensions or pump/filter model below to calculate exact 45-mil EPDM liner sheet size, water volume in gallons, waterfall GPH flow, and UV clarifier wattage.</p>
      <div class="mt-6">
        <input id="filterInput" type="text" placeholder="Search pond size or brand (e.g. 10x15x3 Koi Pond, Aquascape AquaForce, OASE BioSmart, Laguna, Waterfall...)" class="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3.5 text-sm text-white focus:outline-none focus:border-teal-500">
      </div>
    </div>

    <div id="pondGrid" class="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">{cards_html}</div>
  </main>

  <footer class="border-t border-slate-800 py-8 text-center text-xs text-slate-500">
    <p>© {datetime.now(timezone.utc).year} PondLinerIndex. As an Amazon Associate, we earn from qualifying purchases.</p>
  </footer>

  <script>
    const filterInput = document.getElementById('filterInput');
    const cards = Array.from(document.getElementById('pondGrid').children);
    filterInput.addEventListener('input', (e) => {{
      const q = e.target.value.toLowerCase();
      cards.forEach(c => {{
        c.style.display = c.textContent.toLowerCase().includes(q) ? 'block' : 'none';
      }});
    }});
  </script>
</body>
</html>"""

    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(os.path.join(DOCS_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    urls_xml = f"""  <url>
    <loc>{SITE_BASE_URL}/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>\n"""

    for item in published:
        urls_xml += f"""  <url>
    <loc>{SITE_BASE_URL}/{item['slug']}.html</loc>
    <lastmod>{item.get('date', today)}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>\n"""

    with open(os.path.join(DOCS_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(f"""<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls_xml}</urlset>""")

    rss_items = ""
    for item in list(reversed(published))[:30]:
        rss_items += f"""    <item>
      <title>{item['title']}</title>
      <link>{SITE_BASE_URL}/{item['slug']}.html</link>
      <guid>{SITE_BASE_URL}/{item['slug']}.html</guid>
      <description>{item['description']}</description>
    </item>\n"""

    rss_xml = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>PondLinerIndex Koi Pond & Waterfall Sizing Database</title>
    <link>{SITE_BASE_URL}/</link>
    <description>Interactive Koi Pond EPDM Liner Size, Gallon Volume & Waterfall Pump GPH Calculators</description>
    <atom:link href="{SITE_BASE_URL}/rss.xml" rel="self" type="application/rss+xml" />
    <atom:link href="https://pubsubhubbub.appspot.com/" rel="hub" />
{rss_items}  </channel>
</rss>"""

    with open(os.path.join(DOCS_DIR, "rss.xml"), "w", encoding="utf-8") as f:
        f.write(rss_xml)

    with open(os.path.join(DOCS_DIR, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_BASE_URL}/sitemap.xml\n")

    with open(os.path.join(DOCS_DIR, f"{INDEXNOW_KEY}.txt"), "w", encoding="utf-8") as f:
        f.write(INDEXNOW_KEY)


def notify_search_engines(new_urls):
    if not SITE_BASE_URL or not new_urls:
        return
    parsed_host = urllib.parse.urlparse(SITE_BASE_URL).netloc
    payload = {
        "host": parsed_host,
        "key": INDEXNOW_KEY,
        "keyLocation": f"{SITE_BASE_URL}/{INDEXNOW_KEY}.txt",
        "urlList": new_urls
    }
    try:
        req = urllib.request.Request(
            "https://api.indexnow.org/indexnow",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            print(f"[INDEXNOW] Pushed {len(new_urls)} URLs (HTTP {resp.status})")
    except Exception as e:
        print(f"[WARN] IndexNow ping notice: {e}")

    try:
        hub_data = urllib.parse.urlencode({
            "hub.mode": "publish",
            "hub.url": f"{SITE_BASE_URL}/rss.xml"
        }).encode("utf-8")
        req_hub = urllib.request.Request(
            "https://pubsubhubbub.appspot.com/",
            data=hub_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST"
        )
        with urllib.request.urlopen(req_hub, timeout=15) as resp_hub:
            print(f"[WEBSUB] Google PubSubHubbub ping status: {resp_hub.status}")
    except Exception as e:
        print(f"[WARN] WebSub ping notice: {e}")


def main():
    published = load_json(PUBLISHED_FILE, [])
    mon_cfg = load_json(MONETIZATION_FILE, {})
    published_slugs = {item["slug"] for item in published}

    candidates = []
    if CUSTOM_POND:
        candidates.append((CUSTOM_POND.strip(), 15.0, 10.0, 3.0, 18, 2.0))
    candidates.extend(SEED_PONDS)
    candidates.extend(discover_google_pond_queries())

    new_urls = []
    count = 0

    for pond_tuple in candidates:
        if count >= PAGES_PER_RUN:
            break
        p_name = pond_tuple[0]
        slug = slugify(f"{p_name}-liner-gph-calculator")
        if slug in published_slugs:
            continue

        print(f"[ENGINE] Generating pond liner & waterfall GPH calculator for: {p_name}...")
        try:
            data = generate_pond_data(pond_tuple)
            build_pond_html_page(data, slug, mon_cfg)
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            sp = data.get("specs", {})
            l_w = int(safe_float(sp.get("liner_width_ft", 18), 18))
            l_l = int(safe_float(sp.get("liner_length_ft", 23), 23))

            published.append({
                "pond_name": data.get("pond_name", p_name),
                "slug": slug,
                "title": data.get("seo_title", f"{p_name} Pond Calculator"),
                "description": data.get("meta_description", ""),
                "liner_dim": f"{l_w}'×{l_l}'",
                "gallons": int(safe_float(sp.get("estimated_gallons", 2690), 2690)),
                "pump_gph": int(safe_float(sp.get("recommended_pump_gph", 3400), 3400)),
                "date": today
            })
            published_slugs.add(slug)
            if SITE_BASE_URL:
                new_urls.append(f"{SITE_BASE_URL}/{slug}.html")
            count += 1
            time.sleep(2)
        except Exception as e:
            print(f"[ERROR] Failed building {p_name}: {e}")

    save_json(PUBLISHED_FILE, published)
    rebuild_portal_sitemap_and_rss(published, mon_cfg)
    if new_urls and SITE_BASE_URL:
        new_urls.append(f"{SITE_BASE_URL}/")
        notify_search_engines(new_urls)
    print(f"[DONE] Published {count} new koi pond liner & waterfall pump calculator pages.")


if __name__ == "__main__":
    main()
