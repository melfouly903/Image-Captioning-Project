import re
import unicodedata

# ─── Franco-Arabic → Arabic transliteration dictionary ──────
FRANCO_DICT = {
    "2": "أ", "3": "ع", "5": "خ", "6": "ط", "7": "ح", "8": "غ",
    "9": "ق", "4": "ص",
    "ksr": "كسر", "zero": "زيرو", "battery": "بطارية",
    "screen": "شاشة", "original": "أصلي", "copy": "كوبي",
    "condition": "حالة", "new": "جديد", "used": "مستعمل",
    "broken": "مكسور", "crack": "خدش", "box": "كرتون",
    "charger": "شاحن", "water": "ماء", "proof": "بروف",
    "gb": "جيجا", "ram": "رام", "sim": "شريحة",
    "storage": "مساحة", "dual": "شريحتين",
    "iphone": "آيفون", "samsung": "سامسونج",
    "huawei": "هواوي", "xiaomi": "شاومي", "oppo": "أوبو",
    "realme": "ريلمي", "vivo": "فيفو", "nokia": "نوكيا",
    "tecno": "تكنو", "infinix": "إنفينكس", "honor": "هونر",
}

# ─── Arabic stop words ───────────────────────────────────────
ARABIC_STOPWORDS = {
    "في", "من", "على", "إلى", "عن", "مع", "هذا", "هذه", "التي", "الذي",
    "كان", "كانت", "يكون", "هو", "هي", "هم", "هن", "أنا", "أنت", "نحن",
    "لا", "ما", "لم", "لن", "إن", "أن", "كل", "بعد", "قبل", "حتى",
    "لكن", "أو", "ثم", "فقط", "جداً", "جدا", "غير", "بدون", "بكل",
    "وكل", "فكل", "فإن", "إذا", "عند", "عندما", "حيث", "لأن", "لكي",
    "وهو", "وهي", "وهم", "فهو", "فهي", "وفي", "ومن", "وعلى", "وأن",
    "يا", "ال", "و", "ف", "ب", "ل", "ك",
    "تواصل", "واتس", "واتساب", "اتصل", "عاوز", "ممكن", "تعال",
    "هنا", "هناك", "دلوقتي", "دلوقت", "بسرعة",
}

# ─── Condition keywords ──────────────────────────────────────
CONDITION_KEYWORDS = {
    "positive": [
        "كسر زيرو", "زيرو", "جديد", "ممتاز", "رائع", "نظيف", "ناصع",
        "كامل مشتملاته", "معاه الكرتونة", "بالعلبة", "بكامل مشتملاته",
        "بدون خدش", "مفيهوش خدش", "مش مغير حاجة", "بطارية ١٠٠",
        "بطارية 100", "waterproof", "وتر بروف", "استخدام خفيف",
        "استعمال بسيط", "حالة الله اكبر",
    ],
    "negative": [
        "مكسور", "خدش", "مغير", "مغيرة", "مغير شاشة", "مغير بطارية",
        "يحتاج صيانة", "صيانة", "تعبان", "عيب", "مشكلة", "مش شغال",
        "الشاشة مكسورة", "كسر", "قطع غيار",
    ],
}

def clean_arabic_text(text: str) -> str:
    """Full NLP pipeline for Arabic + Franco-Arabic text."""
    if not isinstance(text, str) or not text.strip():
        return ""

    text = text.lower()
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r'[\u064B-\u065F\u0670]', '', text)

    for franco, arabic in FRANCO_DICT.items():
        text = re.sub(r'\b' + re.escape(franco) + r'\b', arabic, text, flags=re.IGNORECASE)

    text = re.sub(r'[أإآاٱ]', 'ا', text)
    text = re.sub(r'ة', 'ه', text)
    text = re.sub(r'ى', 'ي', text)
    text = re.sub(r'ؤ', 'و', text)
    text = re.sub(r'ئ', 'ي', text)

    eastern = '٠١٢٣٤٥٦٧٨٩'
    western = '0123456789'
    for e, w in zip(eastern, western):
        text = text.replace(e, w)

    text = re.sub(r'http\S+|www\S+', '', text)
    text = re.sub(r'\S+@\S+', '', text)
    text = re.sub(r'01[0-9]{9}', '', text)  # Egyptian phone numbers
    text = re.sub(r'\+?[0-9]{10,15}', '', text)
    text = re.sub(r'[^\u0600-\u06FF0-9a-zA-Z\s%]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    tokens = text.split()
    tokens = [t for t in tokens if t not in ARABIC_STOPWORDS and len(t) > 1]

    return ' '.join(tokens)

def extract_features_from_text(text: str) -> dict:
    """Extract structured features from description."""
    raw = text.lower() if isinstance(text, str) else ""

    bat = re.search(r'بطاري[هة]\s*(\d{2,3})', raw)
    battery = int(bat.group(1)) if bat else None

    stor = re.search(r'(\d{2,3})\s*(?:جيجا|gb)', raw)
    storage = int(stor.group(1)) if stor else None

    ram_m = re.search(r'(\d{1,2})\s*(?:رام|ram)', raw)
    ram = int(ram_m.group(1)) if ram_m else None

    pos_count = sum(1 for kw in CONDITION_KEYWORDS["positive"] if kw in raw)
    neg_count = sum(1 for kw in CONDITION_KEYWORDS["negative"] if kw in raw)

    has_box = int(any(k in raw for k in ["كرتون", "علبه", "بوكس", "box"]))
    has_charger = int(any(k in raw for k in ["شاحن", "charger"]))

    dur = re.search(r'(\d+)\s*(?:شهر|شهور|أشهر)', raw)
    usage_months = int(dur.group(1)) if dur else None

    return {
        "battery_pct": battery,
        "storage_gb": storage,
        "ram_gb": ram,
        "positive_signals": pos_count,
        "negative_signals": neg_count,
        "has_box": has_box,
        "has_charger": has_charger,
        "usage_months": usage_months,
    }
