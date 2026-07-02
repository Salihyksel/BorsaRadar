from typing import Any, Dict, List, Set
import ahocorasick
import structlog

logger = structlog.get_logger(__name__)

_AC_AUTOMATON = None

def _get_automaton():
    """DB'deki sirketler+aliaslar tablosundan Aho-Corasick otomatini kurar.
    Basarisiz olursa None doner, cagiran taraf HISSE_MAP'e fallback yapar."""
    global _AC_AUTOMATON
    if _AC_AUTOMATON is not None:
        return _AC_AUTOMATON
    try:
        import pymysql
        import config
        conn = pymysql.connect(
            host=config.DB_HOST, user=config.DB_USER, password=config.DB_PASS,
            database=config.DB_NAME, port=config.DB_PORT, charset="utf8mb4",
        )
        cur = conn.cursor()
        cur.execute("""
            SELECT sa.alias, s.ticker FROM sirket_aliaslar sa
            JOIN sirketler s ON sa.sirket_id = s.id
            WHERE s.aktif = 1
        """)
        rows = cur.fetchall()
        conn.close()

        automaton = ahocorasick.Automaton()
        for alias, ticker in rows:
            automaton.add_word(alias.lower(), (alias.lower(), ticker))
        automaton.make_automaton()
        _AC_AUTOMATON = automaton
        logger.info("entity_matcher.automaton.kuruldu", alias_sayisi=len(rows))
        return _AC_AUTOMATON
    except Exception as exc:
        logger.warning("entity_matcher.automaton.hata", hata=str(exc))
        return None


# ---------------------------------------------------------------------------
# Şirket adı → ticker eşlemesi (direkt isim geçişleri)
# ---------------------------------------------------------------------------
HISSE_MAP: Dict[str, str] = {
    # Bankacılık
    "akbank": "AKBNK", "akbnk": "AKBNK",
    "garanti": "GARAN", "garan": "GARAN",
    "garanti bbva": "GARAN", "bbva garanti": "GARAN",
    "halkbank": "HALKB", "halkb": "HALKB",
    "iş bankası": "ISCTR", "işbank": "ISCTR", "isctr": "ISCTR",
    "vakıfbank": "VAKBN", "vakbn": "VAKBN",
    "yapı kredi": "YKBNK", "ykbnk": "YKBNK",
    # Holding
    "anadolu grubu": "AGHOL", "anadolu group": "AGHOL", "aghol": "AGHOL",
    "doğan": "DOHOL", "doğan holding": "DOHOL", "dogan holding": "DOHOL", "dohol": "DOHOL",
    "koç": "KCHOL", "kchol": "KCHOL",
    "sabancı": "SAHOL", "sahol": "SAHOL",
    "akfen": "AKFEN",
    # Havacılık & Turizm
    "pegasus": "PGSUS", "pgsus": "PGSUS",
    "tav": "TAVHL", "tavhl": "TAVHL",
    "thyao": "THYAO", "türk hava": "THYAO", "thy": "THYAO",
    "çelebi": "CLEBI", "celebi": "CLEBI",
    # Otomotiv & Beyaz Eşya
    "arçelik": "ARCLK", "arcelik": "ARCLK", "beko": "ARCLK", "arclk": "ARCLK",
    "ford otosan": "FROTO", "froto": "FROTO",
    "toaso": "TOASO", "tofaş": "TOASO",
    "togg": "TOGG",
    "vestel": "VESTL", "vestel elektronik": "VESTL", "vstl": "VESTL",
    # Enerji & Petrokimya
    "petkim": "PETKM", "petkm": "PETKM",
    "tüpraş": "TUPRS", "tupras": "TUPRS", "tuprs": "TUPRS",
    "zorlu": "ZOREN", "zoren": "ZOREN",
    "odaş": "ODAS",
    # Çelik & Madencilik
    "ereğli": "EREGL", "ereğli demir": "EREGL", "erdemir": "EREGL",
    "kardemir": "KRDMD", "krdmd": "KRDMD",
    "koza altın": "KOZAL", "kozal": "KOZAL",
    "koza anadolu": "KOZAA", "kozaa": "KOZAA",
    "park elektrik": "PRKME",
    # Savunma & Teknoloji
    "aselsan": "ASELS", "asels": "ASELS",
    "logo": "LOGO", "logo yazılım": "LOGO", "logo software": "LOGO",
    # Cam & Kimya
    "soda sanayii": "SODA", "soda sanayi": "SODA", "soda": "SODA",
    "şişecam": "SISE", "sise": "SISE",
    "trakya cam": "TRKCM", "trkcm": "TRKCM",
    # İnşaat & GYO
    "alarko": "ALARK", "alark": "ALARK",
    "emlak konut": "EKGYO", "ekgyo": "EKGYO",
    "enka": "ENKAI", "enkai": "ENKAI",
    "tekfen": "TKFEN", "tekfen holding": "TKFEN", "tkfen": "TKFEN",
    # Gıda & Perakende
    "anadolu efes": "AEFES", "aefes": "AEFES",
    "bim": "BIMAS", "bimas": "BIMAS",
    "coca cola": "CCOLA", "ccola": "CCOLA",
    "migros": "MGROS",
    "selçuk ecza": "SELEC", "selec": "SELEC",
    "sok market": "SOKM", "sokm": "SOKM",
    "ülker": "ULKER", "ulker": "ULKER",
    # Telekomünikasyon
    "turkcell": "TCELL", "tcell": "TCELL",
    "türk telekom": "TTKOM", "turk telekom": "TTKOM", "ttkom": "TTKOM",
    # Tarım & Sanayi
    "gübre fabrika": "GUBRF", "gubre": "GUBRF", "gubrf": "GUBRF",
    "türk traktör": "TTRAK", "turk traktor": "TTRAK", "ttrak": "TTRAK",
    # Sigorta
    "türkiye sigorta": "TURSG", "ray sigorta": "RAYSG",
}

# ---------------------------------------------------------------------------
# Sektör keyword → ticker listesi (tek kelime tetikleyiciler)
# ---------------------------------------------------------------------------
SEKTOR_MAP: Dict[str, List[str]] = {
    # Enerji & Petrol
    "petrol":          ["TUPRS", "AKENR"],
    "akaryakıt":       ["TUPRS"],
    "rafineri":        ["TUPRS"],
    "elektrik":        ["ZOREN", "AKENR"],
    # Savunma
    "savunma":         ["ASELS"],
    # Havacılık & Turizm
    "havacılık":       ["THYAO", "PGSUS"],
    "uçuş":            ["THYAO", "PGSUS"],
    "turizm":          ["TAVHL", "THYAO", "PGSUS"],
    # Metal & Madencilik
    "demir çelik":     ["EREGL", "KRDMD"],
    "madencilik":      ["KOZAL", "KOZAA", "KRDMD"],
    # Cam & Kimya
    "cam":             ["SISE", "TRKCM"],
    "kimya":           ["PETKM", "SODA", "GUBRF"],
    # Otomotiv
    "otomotiv":        ["FROTO", "TOGG", "TOASO"],
    # Gıda & Perakende
    "gıda":            ["ULKER", "AEFES", "CCOLA", "SOKM"],
    # İnşaat & GYO
    "inşaat":          ["EKGYO", "ENKAI"],
    # Telekomünikasyon
    "telekomünikasyon":["TTKOM", "TCELL"],
    # Tarım
    "tarım":           ["GUBRF", "TTRAK"],
    # Tekstil
    "tekstil":         ["ALARK"],
    # Beyaz Eşya & Tüketici Elektroniği
    "beyaz eşya":          ["ARCLK", "VESTL"],
    "home appliance":      ["ARCLK", "VESTL"],
    "washing machine":     ["ARCLK", "VESTL"],
    "dishwasher":          ["ARCLK", "VESTL"],
    "buzdolabı":           ["ARCLK", "VESTL"],
    "çamaşır makinesi":    ["ARCLK", "VESTL"],
    "televizyon":          ["VESTL", "ARCLK"],
    "television":          ["VESTL", "ARCLK"],
    "tv market":           ["VESTL", "ARCLK"],
    "consumer electronics":["VESTL", "ARCLK"],
    "tüketici elektroniği":["VESTL", "ARCLK"],
    # Tarım & Gübre
    "gübre":               ["GUBRF", "TTRAK"],
    "fertilizer":          ["GUBRF"],
    "tarım ilacı":         ["GUBRF"],
    "agricultural input":  ["GUBRF"],
    "traktör satışı":      ["GUBRF", "TTRAK"],
    # Sigorta
    "sigorta":             ["TURSG", "RAYSG"],
    "insurance turkey":    ["TURSG", "RAYSG"],
    "insurance premium":   ["TURSG", "RAYSG"],
    "sigorta prim":        ["TURSG", "RAYSG"],
}

# ---------------------------------------------------------------------------
# Global makro/sektör tetikleyicileri
# ---------------------------------------------------------------------------
GLOBAL_ETKI_MAP: Dict[str, List[str]] = {
    # Enerji
    "oil price":          ["TUPRS", "AKENR"],
    "brent crude":        ["TUPRS", "AKENR"],
    "opec":               ["TUPRS", "AKENR"],
    "natural gas":        ["AKENR", "ZOREN"],
    "energy crisis":      ["TUPRS", "AKENR"],
    # Altın/Maden
    "gold price":         ["KOZAL", "KOZAA"],
    "gold rally":         ["KOZAL", "KOZAA"],
    "silver price":       ["KOZAL"],
    "iron ore":           ["EREGL", "KRDMD"],
    "steel":              ["EREGL", "KRDMD"],
    # Savunma/Jeopolitik
    "military strike":    ["ASELS"],
    "armed conflict":     ["ASELS"],
    "nato defense":       ["ASELS"],
    "defense spending":   ["ASELS"],
    "ukraine war":        ["ASELS"],
    "iran":               ["TUPRS", "PETKM"],
    # Havacılık
    "jet fuel":           ["THYAO", "PGSUS"],
    "airport":            ["TAVHL"],
    "tourism":            ["THYAO", "TAVHL"],
    # Avrupa ekonomisi
    "europe recession":   ["FROTO", "ARCLK", "EREGL"],
    "eurozone":           ["FROTO", "ARCLK"],
    "europe economy":     ["FROTO", "ARCLK", "EREGL"],
    # Çin
    "china manufacturing":["EREGL", "KRDMD", "PETKM"],
    "china economy":      ["EREGL", "KRDMD"],
    "china pmi":          ["EREGL", "KRDMD"],
    # Otomotiv
    "automotive":         ["FROTO", "TOASO"],
    "electric vehicle":   ["FROTO", "TOASO"],
    # ABD borsası
    "s&p 500 crash":      ["THYAO", "GARAN", "EREGL"],
    "nasdaq crash":       ["THYAO", "GARAN"],
    "market selloff":     ["GARAN", "AKBNK", "THYAO"],
    "emerging market":    ["GARAN", "AKBNK"],
    # Altın makro
    "inflation hedge":    ["KOZAL", "altin"],
    "safe haven":         ["KOZAL", "altin", "gumus"],
    "dollar weakness":    ["KOZAL", "altin"],
    "geopolitical risk":  ["KOZAL", "altin", "ASELS"],
}

# ---------------------------------------------------------------------------
# Emtia / döviz eşlemeleri
# ---------------------------------------------------------------------------
MADEN_MAP: Dict[str, str] = {
    "altın": "altin", "gold": "altin", "xau": "altin",
    "gümüş": "gumus", "silver": "gumus",
    "bakır": "bakir", "copper": "bakir",
    "platin": "platin", "platinum": "platin",
}

DOVIZ_MAP: Dict[str, str] = {
    "dolar": "usd", "usd": "usd", "amerikan doları": "usd",
    "euro": "eur", "eur": "eur",
    "döviz": "usd",
}

# ---------------------------------------------------------------------------
# Bankacılık sektörü — finansal domain knowledge haritası
# ---------------------------------------------------------------------------
# "etkilemez_cikis" anahtarı özel: bu kelimeleri içeren haberler Türk
# bankacılık hisselerine eşleştirme yapılmadan döner.
BANKACILIK_HARITASI: Dict[str, Any] = {

    # === TÜM BANKALARI ETKİLEYEN OLAYLAR ===

    "tcmb_faiz_indirimi": {
        "keywords": [
            "faiz indirim", "faiz indirdi", "faiz düşürüldü",
            "rate cut", "tcmb indirim", "merkez bankası indirim",
            "interest rate cut", "monetary easing", "faiz gevşemesi",
            "politika faizi düşürüldü",
        ],
        "hisseler": ["GARAN", "AKBNK", "ISCTR", "YKBNK", "VAKBN", "HALKB"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Faiz indirimi bankaların net faiz marjını genişletir, kredi büyümesini artırır",
    },

    "tcmb_faiz_artisi": {
        "keywords": [
            "faiz artışı", "faiz artırdı", "faiz yükseltildi",
            "rate hike", "tcmb artış", "merkez bankası artış",
            "interest rate hike", "monetary tightening", "faiz sıkılaştırma",
            "politika faizi artırıldı", "rate increase turkey",
        ],
        "hisseler": ["GARAN", "AKBNK", "ISCTR", "YKBNK", "VAKBN", "HALKB"],
        "etki_yonu": "negatif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Faiz artışı bankaların fonlama maliyetini artırır, kredi talebini düşürür",
    },

    "enflasyon_artisi": {
        "keywords": [
            "enflasyon arttı", "enflasyon yüksek", "enflasyon beklentinin üzerinde",
            "inflation rise", "inflation surge", "cpi above", "cpi yüksek",
            "tüfe arttı", "yıllık enflasyon",
        ],
        "hisseler": ["GARAN", "AKBNK", "ISCTR", "YKBNK", "VAKBN", "HALKB"],
        "etki_yonu": "negatif",
        "etki_gucu": "orta",
        "etki_tipi": "sistemik",
        "aciklama": "Yüksek enflasyon faiz artışı beklentisi yaratır, banka marjlarını sıkıştırır",
    },

    "enflasyon_dustu": {
        "keywords": [
            "enflasyon düştü", "enflasyon geriledi", "dezenflasyon",
            "inflation fell", "disinflation", "inflation below expectations",
            "tüfe geriledi", "enflasyon beklentinin altında",
            "turkey inflation drops", "turkey inflation falls",
            "turkish cpi below", "inflation below expectations turkey",
            "disinflation turkey",
        ],
        "hisseler": ["GARAN", "AKBNK", "ISCTR", "YKBNK", "VAKBN", "HALKB"],
        "etki_yonu": "pozitif",
        "etki_gucu": "orta",
        "etki_tipi": "sistemik",
        "aciklama": "Düşen enflasyon faiz indirim beklentisi yaratır, bankacılık sektörüne olumlu",
    },

    "tl_deger_kaybi": {
        "keywords": [
            "dolar yükseldi", "euro yükseldi", "tl değer kaybı", "kur artışı",
            "lira depreciation", "turkish lira falls", "usd/try yükseliş",
            "döviz kurları yükseldi", "dolar rekor", "lira weakens",
            "record low lira", "turkish lira record", "lira hits low",
            "try record low", "lira falls record", "turkish currency falls",
            "lira hits", "try falls",
        ],
        "hisseler": ["GARAN", "AKBNK", "ISCTR", "YKBNK", "VAKBN", "HALKB"],
        "etki_yonu": "negatif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "TL değer kaybı bankaların dövizli kredi riskini artırır, sermaye yeterliliğini zorlar",
    },

    "turkiye_kredi_notu": {
        "keywords": [
            "türkiye kredi notu", "turkey credit rating", "moody's turkey",
            "fitch turkey", "s&p turkey", "rating upgrade turkey",
            "rating downgrade turkey", "türkiye not artışı", "türkiye not indirimi",
            "turkey sovereign", "cds turkey", "türkiye cds",
        ],
        "hisseler": ["GARAN", "AKBNK", "ISCTR", "YKBNK", "VAKBN", "HALKB"],
        "etki_yonu": "karma",
        "etki_gucu": "yüksek",
        "etki_tipi": "sistemik",
        "aciklama": "Ülke kredi notu değişimi tüm bankacılık sektörünü etkiler, yabancı yatırım akışını yönlendirir",
    },

    "bddk_duzenleme": {
        "keywords": [
            "bddk", "bankacilik duzenleme", "kredi büyüme sınırı",
            "banking regulation turkey", "credit growth cap",
            "bddk karar", "bankacılık düzenlemesi", "zorunlu karşılık",
        ],
        "hisseler": ["GARAN", "AKBNK", "ISCTR", "YKBNK", "VAKBN", "HALKB"],
        "etki_yonu": "negatif",
        "etki_gucu": "orta",
        "etki_tipi": "direkt",
        "aciklama": "BDDK kısıtlamaları bankaların kredi büyümesini ve gelir potansiyelini sınırlar",
    },

    # === SADECE O BANKAYA ÖZGÜ OLAYLAR ===

    "garanti_ozel": {
        "keywords": [
            "garanti bbva", "bbva garanti", "garanti bankası kâr", "garanti temettü",
        ],
        "hisseler": ["GARAN"],
        "etki_yonu": "karma",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Garanti'ye özgü gelişme",
    },

    "akbank_ozel": {
        "keywords": [
            "akbank kâr", "sabancı holding bank", "akbank temettü", "akbank siber",
        ],
        "hisseler": ["AKBNK"],
        "etki_yonu": "karma",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Akbank'a özgü gelişme",
    },

    "is_bankasi_ozel": {
        "keywords": [
            "iş bankası kâr", "iş bankası temettü", "is bankasi temettü",
            "chp iş bankası", "chp işbank",
        ],
        "hisseler": ["ISCTR"],
        "etki_yonu": "karma",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "İş Bankası'na özgü gelişme",
    },

    "yapi_kredi_ozel": {
        "keywords": [
            "yapı kredi kâr", "yapı kredi temettü", "unicredit turkey", "koç finansal",
        ],
        "hisseler": ["YKBNK"],
        "etki_yonu": "karma",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Yapı Kredi'ye özgü gelişme",
    },

    "kamu_bankalari": {
        "keywords": [
            "vakıfbank kâr", "vakıfbank temettü",
            "halkbank kâr", "halkbank temettü",
            "kamu bankası", "state bank turkey",
            "halkbank us court", "halkbank dava", "ofac turkey",
        ],
        "hisseler": ["VAKBN", "HALKB"],
        "etki_yonu": "karma",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Kamu bankalarına özgü gelişme",
    },

    # === TÜRK BANKALARINI ETKİLEMEYEN YABANCI BANKA HABERLERİ ===
    # Bu liste sözlük değil — özel kontrol yapılır.
    "etkilemez_cikis": [
        "chinese bank", "china bank collapse", "silicon valley bank",
        "svb collapse", "regional bank us", "european bank crisis",
        "deutsche bank", "credit suisse",
    ],
}

# ---------------------------------------------------------------------------
# Enerji sektörü — finansal domain knowledge haritası
# ---------------------------------------------------------------------------
# TUPRS ham petrol ALICISIDIR: petrol fiyatı artar → hammadde maliyeti artar
# ama rafine ürün fiyatları daha hızlı artar → net rafinery marjı genişler → POZİTİF
# PETKM nafta/LPG kullanır: ham petrol artışı maliyetleri artırır → NEGATİF
ENERJI_HARITASI: Dict[str, Any] = {

    "petrol_yukseldi": {
        "keywords": [
            "petrol fiyatı yükseldi", "ham petrol arttı", "brent arttı",
            "oil price rises", "crude oil up", "brent crude rises",
            "oil surges", "oil rally", "petrol rallisi",
            "crude oil higher", "wti rises", "oil price increase",
        ],
        "hisseler": ["TUPRS", "AKENR"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Petrol fiyatı artışı Tüpraş'ın rafinery marjını genişletir, stok değerleri artar",
    },

    "petrol_dustu": {
        "keywords": [
            "petrol fiyatı düştü", "ham petrol geriledi", "brent düştü",
            "oil price falls", "crude oil down", "brent drops",
            "oil selloff", "oil price decline", "petrol düşüşü",
            "crude oil lower", "wti falls", "oil price drop", "oil prices drop",
        ],
        "hisseler": ["TUPRS"],
        "etki_yonu": "negatif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Petrol fiyatı düşüşü Tüpraş'ın stok değer kayıplarına yol açar",
    },

    "ortadogu_gerilimi": {
        "keywords": [
            "orta doğu gerilim", "iran saldırı", "hürmüz boğazı",
            "middle east oil", "gulf oil", "middle east energy",
            "persian gulf conflict", "hormuz",
            "iran attack", "strait of hormuz",
            "israel iran", "saudi arabia attack",
            "ortadoğu kriz", "körfez gerilim", "gulf crisis",
            "iran sanctions", "iran nükleer", "yemen houthi",
            "red sea attack", "shipping disruption",
        ],
        "hisseler": ["TUPRS", "PETKM"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Ortadoğu gerilimi arz kesintisi riski yaratır, petrol fiyatları yükselir, TUPRS ve PETKM stok değerleri artar",
    },

    "opec_uretim_kesinti": {
        "keywords": [
            "opec üretim kesinti", "opec kota", "opec+ karar",
            "opec production cut", "opec cuts output", "opec+ decision",
            "saudi arabia cut", "opec meeting", "opec toplantı",
        ],
        "hisseler": ["TUPRS"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "OPEC üretim kesintisi petrol arzını düşürür, fiyatları yükseltir, TUPRS marjları iyileşir",
    },

    "opec_uretim_artisi": {
        "keywords": [
            "opec üretim artışı", "opec artırım",
            "opec production increase", "opec raises output",
            "saudi arabia increases", "opec supply boost",
        ],
        "hisseler": ["TUPRS"],
        "etki_yonu": "negatif",
        "etki_gucu": "orta",
        "etki_tipi": "direkt",
        "aciklama": "OPEC üretim artışı petrol fiyatlarını baskılar, TUPRS marjlarını daraltır",
    },

    "dogalgaz_yukseldi": {
        "keywords": [
            "doğalgaz fiyatı arttı", "natural gas rises",
            "natural gas price up", "gas price surge",
            "european gas prices", "ttf gas", "henry hub rises",
            "lng fiyatı arttı", "gaz fiyatı yükseldi",
        ],
        "hisseler": ["AKENR", "ZOREN"],
        "etki_yonu": "pozitif",
        "etki_gucu": "orta",
        "etki_tipi": "direkt",
        "aciklama": "Doğalgaz fiyat artışı gaz üretim ve dağıtım şirketlerinin gelirlerini artırır",
    },

    "petrokimya_hammadde": {
        "keywords": [
            "nafta fiyatı", "naphtha price", "lpg fiyatı",
            "petrochemical feedstock", "ethylene price",
            "petrokimya hammadde", "polimer fiyatı",
        ],
        "hisseler": ["PETKM"],
        "etki_yonu": "karma",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Nafta/LPG hammadde fiyatları Petkim'in maliyet yapısını doğrudan etkiler",
    },

    "turkiye_enerji_kesfi": {
        "keywords": [
            "karadeniz gaz", "türkiye doğalgaz keşfi",
            "turkey gas discovery", "black sea gas",
            "sakarya gaz sahası", "türkiye enerji keşfi",
            "turkey energy discovery", "turkey gas", "turkey oil discovery",
            "karadeniz keşif", "türkiye keşif",
            "black sea discovery", "gas discovery turkey", "energy discovery turkey",
            "natural gas in black sea",
            "turkey discovers gas", "black sea gas discovery",
            "turkey gas discovery", "gas discovery turkey",
            "turkey natural gas black sea",
            "karadeniz gaz keşfi", "türkiye gaz keşfi", "türkiye enerji keşfi",
        ],
        "hisseler": ["TUPRS", "PETKM", "AKENR", "ZOREN"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Türkiye'nin enerji keşifleri tüm enerji sektörünü olumlu etkiler",
    },

    "elektrik_fiyat": {
        "keywords": [
            "elektrik fiyatı arttı", "electricity price rises",
            "power price up", "energy tariff increase",
            "elektrik zammı", "enerji tarifeleri",
        ],
        "hisseler": ["AKENR", "ZOREN", "ODAS"],
        "etki_yonu": "pozitif",
        "etki_gucu": "orta",
        "etki_tipi": "direkt",
        "aciklama": "Elektrik fiyat artışı elektrik üreticilerinin gelirlerini artırır",
    },

    "rusya_enerji": {
        "keywords": [
            "russia gas", "russia pipeline", "russian pipeline", "russian oil supply",
            "russia energy cut", "gazprom", "nordstream",
            "russia energy", "russia oil", "russia ukraine energy",
            "rusya doğalgaz", "rusya petrol", "rusya enerji kesinti",
        ],
        "hisseler": ["TUPRS", "AKENR", "ZOREN"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Rusya enerji kesintisi global arzı kısıtlar, fiyatları yükseltir, enerji şirketleri değer kazanır",
    },
}

# ---------------------------------------------------------------------------
# Savunma sektörü — finansal domain knowledge haritası
# ---------------------------------------------------------------------------
# ASELS ihracat gelirlerinin büyük kısmı USD — dolar güçlenirse TL bazı gelir artar.
# Barış/ateşkes haberleri ASELS için negatif; savaş/çatışma haberleri pozitif.
SAVUNMA_HARITASI: Dict[str, Any] = {

    "savas_calisma_artisi": {
        "keywords": [
            "war escalates", "military conflict", "armed conflict",
            "ukraine war", "russia ukraine", "ukraine attack",
            "israel hamas", "israel hezbollah",
            "india pakistan conflict", "taiwan conflict", "taiwan strait",
            "military strike", "missile attack", "air strike",
            "savaş tırmanıyor", "askeri operasyon", "çatışma arttı",
            "bombing", "military offensive", "missile offensive", "nato russia",
            "north korea missile", "hypersonic missile test",
        ],
        "hisseler": ["ASELS", "RODRG"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Küresel çatışma artışı savunma harcamalarını hızlandırır, ASELS ve RODRG sipariş defteri büyür",
    },

    "baris_anlasma": {
        "keywords": [
            "ceasefire", "peace deal", "peace agreement",
            "diplomatic solution", "peace talks progress",
            "ukraine ceasefire", "ateşkes", "barış anlaşması",
            "israel ceasefire", "conflict resolution",
            "nato russia diplomacy", "tensions ease",
            "gerilim azaldı", "diplomatik çözüm",
        ],
        "hisseler": ["ASELS", "RODRG"],
        "etki_yonu": "negatif",
        "etki_gucu": "orta",
        "etki_tipi": "direkt",
        "aciklama": "Barış görüşmeleri jeopolitik riski azaltır, savunma harcama beklentilerini düşürür, ASELS baskı altına girer",
    },

    "nato_harcama_artisi": {
        "keywords": [
            "nato defense spending", "nato budget increase",
            "nato 5% gdp", "nato members increase spending",
            "european rearmament", "europe defense budget",
            "nato expansion", "nato enlargement",
            "savunma harcamaları artışı", "nato bütçe",
            "avrupa savunma", "defense spending gdp",
            "raise defense spending", "increase defense spending",
        ],
        "hisseler": ["ASELS", "RODRG"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "sistemik",
        "aciklama": "NATO ülkelerinin savunma harcamalarını artırması Aselsan ihracat fırsatlarını genişletir",
    },

    "turkiye_savunma_ihracat": {
        "keywords": [
            "aselsan ihracat", "aselsan export",
            "aselsan contract", "aselsan sözleşme",
            "türkiye savunma ihracat", "turkey defense export",
            "türk savunma sanayi", "turkey defense industry",
            "insansız hava aracı ihracat", "drone export turkey",
            "bayraktar export", "türk drone ihracat",
            "savunma sanayi sözleşme", "ssb contract",
            "çelik kubbe", "steel dome turkey",
            "aselsan backlog", "aselsan sipariş", "aselsan signs",
        ],
        "hisseler": ["ASELS", "RODRG"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Türkiye savunma ihracat sözleşmeleri Aselsan ve Roketsan gelir büyümesini destekler",
    },

    "dolar_savunma_etkisi": {
        "keywords": [
            "dollar strengthens", "dollar index rises", "dxy up",
            "dollar rally", "strong dollar", "usd rises",
            "dolar güçlendi", "dolar yükseldi", "dxy yükseliş",
            "dollar index", "dollar index hits",
        ],
        "hisseler": ["ASELS"],
        "etki_yonu": "pozitif",
        "etki_gucu": "orta",
        "etki_tipi": "direkt",
        "aciklama": "Aselsan ihracat gelirlerinin büyük kısmı USD cinsinden, dolar güçlenmesi TL bazında gelirleri artırır",
    },

    "turkiye_nato_iliskisi": {
        "keywords": [
            "turkey nato", "türkiye nato", "turkey f35",
            "turkey f-35", "turkey patriot", "türkiye f35",
            "turkey us defense", "türkiye abd savunma",
            "turkey nato membership", "nato turkey relations",
            "turkey arms embargo", "türkiye silah ambargosu",
        ],
        "hisseler": ["ASELS"],
        "etki_yonu": "karma",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Türkiye-NATO ilişkileri Aselsan ihracat kapılarını açar veya kapatır",
    },

    "global_savunma_harcama": {
        "keywords": [
            "global defense spending", "world defense budget",
            "military spending record", "arms race",
            "defense industry outlook", "defense stocks rally",
            "küresel savunma harcama", "silahlanma yarışı",
            "sipri defense", "defense budget increase",
        ],
        "hisseler": ["ASELS", "RODRG"],
        "etki_yonu": "pozitif",
        "etki_gucu": "orta",
        "etki_tipi": "sistemik",
        "aciklama": "Küresel savunma harcamalarındaki artış Aselsan ve Roketsan için büyük pazar fırsatı yaratır",
    },

    # Bu listedeki kelimeler varsa savunma eşleşmesi yapılmaz.
    "etkilemez_savunma": [
        "civilian police", "drug war", "crime",
        "civil unrest protest", "police brutality",
        "law enforcement budget",
        "wheat", "grain", "food prices",
        "agricultural", "crop",
        "software", "erp", "cloud software",
        "digital", "yazılım", "tech company revenue",
    ],
}

# ---------------------------------------------------------------------------
# Havacılık sektörü — finansal domain knowledge haritası
# ---------------------------------------------------------------------------
# Petrol artışı TUPRS için pozitif, THYAO/PGSUS için negatiftir (jet yakıt maliyeti).
# TAVHL yakıt maliyeti taşımaz; yolcu sayısı ve turizme bağlıdır.
# THY gelir/giderlerinin büyük kısmı döviz cinsinden, kur etkisi çift yönlüdür.
HAVACILIK_HARITASI: Dict[str, Any] = {

    "jet_yakiti_artti": {
        "keywords": [
            "jet fuel price rises", "jet fuel surge",
            "aviation fuel cost", "kerosene price up",
            "jet yakıtı fiyatı arttı", "jet yakıt maliyeti",
            "aviation fuel expensive", "fuel cost airline",
            "oil price airline", "fuel surcharge increase",
            "jet fuel prices surge", "jet fuel prices",
        ],
        "hisseler": ["THYAO", "PGSUS"],
        "etki_yonu": "negatif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Jet yakıtı THYAO ve Pegasus'un en büyük maliyet kalemi, fiyat artışı marjları doğrudan baskılar",
    },

    "jet_yakiti_dustu": {
        "keywords": [
            "jet fuel price falls", "jet fuel drops",
            "aviation fuel cheaper", "kerosene price down",
            "jet yakıtı düştü", "yakıt maliyeti geriledi",
            "fuel cost airline lower", "oil down airline",
            "fuel cost reduction aviation",
        ],
        "hisseler": ["THYAO", "PGSUS"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Jet yakıtı düşüşü THY ve Pegasus'un operasyonel kâr marjını genişletir",
    },

    "turizm_artisi": {
        "keywords": [
            "türkiye turizm rekoru", "turkey tourism record",
            "tourist arrivals turkey", "tourism revenue turkey",
            "yolcu trafiği arttı", "turkey passenger traffic increase",
            "summer travel boom", "travel demand surge",
            "airline passenger record", "turizm geliri arttı",
            "rezervasyon artışı", "booking surge",
            "turkish tourism", "antalya turizm",
            "iata passenger growth", "air travel recovery",
            "tourism record", "breaks tourism record",
        ],
        "hisseler": ["THYAO", "PGSUS", "TAVHL"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Turizm artışı yolcu sayısını ve bilet gelirlerini artırır, üç havacılık şirketini olumlu etkiler",
    },

    "turizm_dusus": {
        "keywords": [
            "turkey tourism decline", "tourist arrivals fall",
            "travel demand drop", "airline passenger decline",
            "yolcu sayısı düştü", "turizm geriledi",
            "travel restriction", "flight ban",
            "seyahat yasağı", "uçuş yasağı",
            "tourism warning turkey", "travel advisory turkey",
            "travel advisory",
        ],
        "hisseler": ["THYAO", "PGSUS", "TAVHL"],
        "etki_yonu": "negatif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Turizm düşüşü yolcu sayısını azaltır, havacılık sektörü genelinde negatif etki yaratır",
    },

    "hurmuz_kapanmasi": {
        "keywords": [
            "hormuz closure", "strait of hormuz closed",
            "hormuz blockade", "hormuz blocked",
            "hürmüz kapandı", "hürmüz boğazı kapatıldı",
            "persian gulf shipping halt",
            "middle east flight disruption",
            "gulf airspace closed",
        ],
        "hisseler": ["THYAO", "PGSUS"],
        "etki_yonu": "negatif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Hürmüz kapanması hem jet yakıt fiyatlarını artırır hem doğu rotalarını keser, çift negatif etki",
    },

    "havacilik_kaza_kriz": {
        "keywords": [
            "plane crash", "aviation accident",
            "airline crisis", "aircraft incident",
            "thy kaza", "thyao kaza",
            "pegasus kaza", "flight crash",
            "aviation safety concern",
        ],
        "hisseler": ["THYAO", "PGSUS"],
        "etki_yonu": "negatif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Havacılık kazaları ve güvenlik endişeleri yolcu talebini ve hisse değerini olumsuz etkiler",
    },

    "thy_buyume": {
        "keywords": [
            "türk hava yolları", "turkish airlines",
            "thy yolcu rekoru", "thy kargo",
            "turkish airlines record", "thy büyüme",
            "thyao sözleşme", "thy filo",
            "turkish airlines expansion",
            "thy uçuş hattı", "thyao kâr",
            "turkish cargo record",
        ],
        "hisseler": ["THYAO"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "THY'ye özgü büyüme ve operasyonel gelişmeler",
    },

    "pegasus_ozel": {
        "keywords": [
            "pegasus havayolları", "pegasus airlines",
            "pgsus kâr", "pegasus büyüme",
            "pegasus yolcu", "pegasus filo",
            "pegasus hava yolu", "pgsus sözleşme",
        ],
        "hisseler": ["PGSUS"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Pegasus'a özgü gelişme",
    },

    "tav_havalimani": {
        "keywords": [
            "tav havalimanı", "tav airports",
            "tavhl kâr", "istanbul havalimanı yolcu",
            "tav concession", "airport passenger record",
            "istanbul airport record",
            "havalimanı yolcu rekoru",
            "tav ihale", "tav sözleşme",
            "duty free revenue", "airport retail",
        ],
        "hisseler": ["TAVHL"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "TAV Havalimanları yolcu trafiğine bağlı gelir elde eder, rekorlar TAV için çok olumlu",
    },

    "petrol_dustu_havacilik": {
        "keywords": [
            "oil down airline", "oil drop airline",
            "airlines rally oil", "airlines rally", "airlines benefit",
            "fuel cost falls airline", "lower fuel costs airline",
            "oil prices drop airlines", "oil prices drop airline",
            "crude falls aviation", "crude down airline",
            "lower oil airline", "oil cheap airline",
            "petrol düştü havacılık", "yakıt ucuzladı",
        ],
        "hisseler": ["THYAO", "PGSUS"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Petrol düşüşü jet yakıt maliyetini azaltır, THY ve Pegasus marjları iyileşir",
    },

    "kuresel_resesyon_havacilik": {
        "keywords": [
            "global recession airline",
            "recession travel demand",
            "economic slowdown travel",
            "business travel decline",
            "corporate travel cut",
            "resesyon uçuş",
            "iata profit warning",
            "airline industry loss",
            "airline travel demand", "recession airline",
        ],
        "hisseler": ["THYAO", "PGSUS", "TAVHL"],
        "etki_yonu": "negatif",
        "etki_gucu": "orta",
        "etki_tipi": "sistemik",
        "aciklama": "Global resesyon iş seyahati ve turizm talebini düşürür, tüm havacılık sektörünü etkiler",
    },

    # Bu listedeki kelimeler varsa havacılık hisseleri eşleştirilmez.
    "etkilemez_havacilik": [
        "cargo ship", "sea freight", "shipping container",
        "maritime transport", "truck logistics",
        "rail transport", "highway",
    ],
}

# ---------------------------------------------------------------------------
# Demir-Çelik sektörü — finansal domain knowledge haritası
# ---------------------------------------------------------------------------
# Çin dünyanın en büyük çelik üreticisi; Çin yavaşlarsa global fiyatlar düşer.
# Demir cevheri çeliğin hammaddesi; ucuzlarsa maliyet avantajı sağlar.
# EREGL ihracat yapıyor, dolar güçlenince TL bazında gelirleri artar.
DEMIR_CELIK_HARITASI: Dict[str, Any] = {

    "celik_fiyati_artti": {
        "keywords": [
            "steel price rises", "steel prices up",
            "steel rally", "steel surge",
            "çelik fiyatı arttı", "çelik fiyatları yükseldi",
            "hot rolled coil price", "hrc price up",
            "steel demand increase", "çelik talebi arttı",
        ],
        "hisseler": ["EREGL", "KRDMD", "ISDMR"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Çelik fiyat artışı Erdemir ve Kardemir'in satış gelirlerini ve marjlarını artırır",
    },

    "celik_fiyati_dustu": {
        "keywords": [
            "steel price falls", "steel prices drop",
            "steel selloff", "steel oversupply",
            "çelik fiyatı düştü", "çelik fiyatları geriledi",
            "steel demand falls", "çelik talebi düştü",
            "steel market weak", "çelik piyasası zayıf",
        ],
        "hisseler": ["EREGL", "KRDMD", "ISDMR"],
        "etki_yonu": "negatif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Çelik fiyat düşüşü Erdemir ve Kardemir'in satış gelirlerini ve marjlarını baskılar",
    },

    "cin_celik_uretimi": {
        "keywords": [
            "china steel output", "chinese steel production",
            "china steel exports", "china steel dump",
            "çin çelik üretimi", "çin çelik ihracatı",
            "china overcapacity steel",
            "chinese mills output",
            "china steel flood market",
            "anti-dumping steel china",
        ],
        "hisseler": ["EREGL", "KRDMD"],
        "etki_yonu": "negatif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Çin'in aşırı çelik üretimi ve ihracatı global çelik fiyatlarını baskılar",
    },

    "cin_ekonomi_yavaslama": {
        "keywords": [
            "china economy slowdown", "china gdp miss",
            "china manufacturing pmi drop",
            "china construction decline",
            "china real estate crisis",
            "chinese economy weak",
            "china demand falls",
            "çin ekonomisi yavaşlıyor",
            "çin inşaat krizi",
            "china property sector crisis",
            "evergrande", "china developer",
        ],
        "hisseler": ["EREGL", "KRDMD"],
        "etki_yonu": "negatif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Çin ekonomik yavaşlaması global çelik talebini düşürür, fiyatları baskılar",
    },

    "cin_ekonomi_canlanma": {
        "keywords": [
            "china economy recovers", "china gdp beats",
            "china stimulus package", "china infrastructure",
            "china construction boom", "china pmi rises",
            "chinese economy strong",
            "china recovery", "china growth",
            "çin ekonomisi canlanıyor", "çin teşvik paketi",
            "china spending plan", "china steel demand",
        ],
        "hisseler": ["EREGL", "KRDMD"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Çin ekonomik canlanması global çelik talebini artırır, fiyatları destekler",
    },

    "demir_cevheri_fiyati": {
        "keywords": [
            "iron ore price", "iron ore falls", "iron ore rises",
            "demir cevheri fiyatı", "iron ore cheaper",
            "iron ore cost",
            "vale iron ore", "rio tinto iron ore",
            "bhp iron ore", "iron ore supply",
        ],
        "hisseler": ["EREGL", "KRDMD"],
        "etki_yonu": "karma",
        "etki_gucu": "orta",
        "etki_tipi": "direkt",
        "aciklama": "Demir cevheri fiyatı çelik üretim maliyetini etkiler, düşerse maliyet avantajı sağlar",
    },

    "avrupa_insaat_otomotiv": {
        "keywords": [
            "europe construction decline",
            "european auto production falls",
            "eu manufacturing weak",
            "europe recession industry",
            "avrupa inşaat düştü",
            "avrupa otomotiv üretim düştü",
            "eu steel demand falls",
            "europe industry slowdown",
        ],
        "hisseler": ["EREGL", "KRDMD"],
        "etki_yonu": "negatif",
        "etki_gucu": "orta",
        "etki_tipi": "direkt",
        "aciklama": "Avrupa inşaat ve otomotiv talebi düşüşü çelik ihracat gelirlerini azaltır",
    },

    "turkiye_insaat_buyume": {
        "keywords": [
            "türkiye inşaat büyüme", "turkey construction",
            "konut projeleri", "housing projects turkey",
            "turkey infrastructure", "altyapı yatırımı",
            "deprem konut üretimi", "earthquake housing",
            "kentsel dönüşüm", "urban transformation turkey",
            "turkey housing demand",
        ],
        "hisseler": ["EREGL", "KRDMD", "ISDMR"],
        "etki_yonu": "pozitif",
        "etki_gucu": "orta",
        "etki_tipi": "direkt",
        "aciklama": "Türkiye inşaat talebi artışı yurt içi çelik tüketimini artırır",
    },

    "celik_ithalat_gumruk": {
        "keywords": [
            "steel tariff", "steel import duty",
            "anti-dumping steel", "steel safeguard",
            "çelik ithalat vergisi", "çelik gümrük",
            "steel trade protection",
            "us steel tariff", "eu steel quota",
            "section 232 steel",
        ],
        "hisseler": ["EREGL", "KRDMD"],
        "etki_yonu": "pozitif",
        "etki_gucu": "orta",
        "etki_tipi": "direkt",
        "aciklama": "Çelik ithalat gümrükleri yerli üreticileri korur, rekabet avantajı sağlar",
    },

    "erdemir_ozel": {
        "keywords": [
            "ereğli demir çelik", "erdemir", "eregl",
            "erdemir kâr", "erdemir üretim",
            "erdemir ihracat", "erdemir sözleşme",
            "ereğli çelik", "erdemir temettü",
        ],
        "hisseler": ["EREGL"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Erdemir'e özgü gelişme",
    },

    "kardemir_ozel": {
        "keywords": [
            "kardemir", "krdmd", "karabük demir",
            "kardemir kâr", "kardemir üretim",
            "kardemir ihracat", "kardemir sözleşme",
        ],
        "hisseler": ["KRDMD"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Kardemir'e özgü gelişme",
    },

    # Bu listedeki kelimeler varsa demir-çelik eşleşmesi yapılmaz.
    "etkilemez_demir_celik": [
        "gold mining", "copper mining", "silver mining",
        "coal mining", "oil drilling",
        "stainless steel consumer", "steel kitchen",
        "jewelry",
        "white goods", "home appliance", "consumer electronics",
        "television", "washing machine",
    ],
}

# ---------------------------------------------------------------------------
# Madencilik sektörü — finansal domain knowledge haritası
# ---------------------------------------------------------------------------
MADENCILIK_HARITASI: Dict[str, Any] = {

    "altin_fiyati_artti": {
        "keywords": [
            "gold price rises", "gold rally", "gold surges",
            "gold hits record", "gold above", "xau rises",
            "altın fiyatı arttı", "altın rallisi", "altın rekor",
            "gold demand", "central bank gold buying",
            "gold safe haven", "gold inflation hedge",
        ],
        "hisseler": ["KOZAL", "KOZAA"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Altın fiyatı artışı Koza Altın'ın satış gelirlerini ve kâr marjını artırır",
    },

    "altin_fiyati_dustu": {
        "keywords": [
            "gold price falls", "gold drops", "gold selloff",
            "gold declines", "xau falls",
            "altın fiyatı düştü", "altın geriledi",
            "gold price lower", "gold weakness",
        ],
        "hisseler": ["KOZAL", "KOZAA"],
        "etki_yonu": "negatif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Altın fiyatı düşüşü Koza Altın gelirlerini ve kârlılığını olumsuz etkiler",
    },

    "dolar_altin_etkisi": {
        "keywords": [
            "dollar weakens gold", "weak dollar gold",
            "dollar index falls gold", "dxy falls",
            "dollar weakness gold rises",
            "dolar zayıfladı altın yükseldi",
        ],
        "hisseler": ["KOZAL", "KOZAA"],
        "etki_yonu": "pozitif",
        "etki_gucu": "orta",
        "etki_tipi": "direkt",
        "aciklama": "Dolar zayıflaması altın fiyatını destekler, Koza Altın hisselerine olumlu yansır",
    },

    "koza_ozel": {
        "keywords": [
            "koza altın", "kozal", "koza anadolu", "kozaa",
            "koza gold", "koza maden", "koza üretim",
            "koza kâr", "koza temettü", "koza rezerv",
        ],
        "hisseler": ["KOZAL", "KOZAA"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Koza şirketlerine özgü gelişme",
    },
}

# ---------------------------------------------------------------------------
# Perakende sektörü — finansal domain knowledge haritası
# ---------------------------------------------------------------------------
PERAKENDE_HARITASI: Dict[str, Any] = {

    "enflasyon_tuketim_etkisi": {
        "keywords": [
            "türkiye enflasyon tüketim", "turkey inflation consumption",
            "tüketici harcamaları", "consumer spending turkey",
            "perakende satışlar", "retail sales turkey",
            "household spending", "tüketim harcaması",
            "turkey retail inflation",
        ],
        "hisseler": ["BIMAS", "MGROS", "SOKM"],
        "etki_yonu": "pozitif",
        "etki_gucu": "orta",
        "etki_tipi": "direkt",
        "aciklama": "Yüksek enflasyon döneminde market zincirleri fiyat artışlarını yansıtarak nominal gelirlerini artırır",
    },

    "tuketici_guven_dustu": {
        "keywords": [
            "consumer confidence falls", "consumer confidence drops",
            "consumer confidence turkey", "consumer confidence turkey drops",
            "consumer confidence falls turkey", "consumer confidence 5-year",
            "consumer confidence low", "consumer sentiment falls",
            "tüketici güveni düştü", "tüketici güven düştü", "tüketici güven endeksi",
            "household confidence", "household confidence drop",
            "household spending falls turkey",
            "spending cuts", "turkey consumer weak", "turkey consumer spending weak",
        ],
        "hisseler": ["BIMAS", "MGROS", "SOKM"],
        "etki_yonu": "negatif",
        "etki_gucu": "orta",
        "etki_tipi": "direkt",
        "aciklama": "Tüketici güven düşüşü market zincirlerinin satış hacmini olumsuz etkiler",
    },

    "bim_ozel": {
        "keywords": [
            "bim mağaza", "bimas", "bim açılış",
            "bim kâr", "bim büyüme", "bim yurt dışı",
            "bim file", "bim indirim",
        ],
        "hisseler": ["BIMAS"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "BİM'e özgü gelişme",
    },

    "migros_ozel": {
        "keywords": [
            "migros", "mgros", "migros kâr",
            "migros büyüme", "migros mağaza",
            "migros e-ticaret", "migros online",
        ],
        "hisseler": ["MGROS"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Migros'a özgü gelişme",
    },

    "sok_ozel": {
        "keywords": [
            "şok market", "sokm", "şok mağaza",
            "sok kâr", "sok büyüme", "şok indirim",
        ],
        "hisseler": ["SOKM"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Şok Market'e özgü gelişme",
    },
}

# ---------------------------------------------------------------------------
# Otomotiv sektörü — finansal domain knowledge haritası
# ---------------------------------------------------------------------------
OTOMOTIV_HARITASI: Dict[str, Any] = {

    "avrupa_otomotiv_talebi": {
        "keywords": [
            "europe auto sales", "european car market",
            "eu auto demand", "europe vehicle sales",
            "avrupa otomotiv satışları", "avrupa araç talebi",
            "european new car registrations",
            "eu car sales record", "europe auto recovery",
            "european auto sales surge", "europe car sales increase",
            "eu vehicle sales rise", "european car market recovery",
            "europe auto demand grows",
        ],
        "hisseler": ["FROTO", "TOASO"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Avrupa otomotiv talebi Ford Otosan ve Tofaş ihracat gelirlerini doğrudan etkiler",
    },

    "avrupa_otomotiv_dusus": {
        "keywords": [
            "europe auto sales fall", "european car market weak",
            "eu auto demand drops", "europe vehicle sales decline",
            "avrupa otomotiv satışları düştü",
            "european auto slowdown",
            "car sales europe decline",
        ],
        "hisseler": ["FROTO", "TOASO"],
        "etki_yonu": "negatif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Avrupa otomotiv talep düşüşü ihracat gelirlerini azaltır",
    },

    "elektrikli_arac_gecis": {
        "keywords": [
            "electric vehicle transition", "ev adoption",
            "combustion engine ban", "ice ban europe",
            "2035 combustion ban", "ev mandate",
            "elektrikli araç geçiş", "içten yanmalı yasak",
            "europe ev regulation", "ford ev strategy",
            "togg ev",
        ],
        "hisseler": ["FROTO", "TOASO"],
        "etki_yonu": "karma",
        "etki_gucu": "orta",
        "etki_tipi": "sistemik",
        "aciklama": "EV geçişi geleneksel üreticiler için dönüşüm maliyeti yaratır, adaptasyon süreci kritik",
    },

    "cip_tedarik_sorunu": {
        "keywords": [
            "chip shortage automotive", "semiconductor auto",
            "auto production halt chip", "car production stop",
            "çip tedarik sorunu otomotiv", "yarı iletken eksikliği",
            "automotive semiconductor shortage",
        ],
        "hisseler": ["FROTO", "TOASO"],
        "etki_yonu": "negatif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Çip tedarik sorunu otomotiv üretimini durdurur, gelirler düşer",
    },

    "ford_ozel": {
        "keywords": [
            "ford otosan", "froto", "ford türkiye",
            "ford otosan kâr", "ford otosan üretim",
            "ford otosan ihracat", "ford transit",
            "ford otosan sözleşme", "ford otosan kapasite",
        ],
        "hisseler": ["FROTO"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Ford Otosan'a özgü gelişme",
    },

    "togg_tofas_ozel": {
        "keywords": [
            "tofaş", "toaso", "fiat türkiye",
            "tofaş kâr", "tofaş üretim", "tofaş ihracat",
            "tofaş kapasite", "stellantis turkey",
            "togg arabası", "togg üretim",
        ],
        "hisseler": ["TOASO"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Tofaş'a özgü gelişme",
    },
}

# ---------------------------------------------------------------------------
# Telekomünikasyon sektörü — finansal domain knowledge haritası
# ---------------------------------------------------------------------------
TELEKOM_HARITASI: Dict[str, Any] = {

    "5g_lisans_yatirim": {
        "keywords": [
            "5g turkey", "5g türkiye", "5g lisans",
            "5g yatırım", "5g rollout turkey",
            "turkcell 5g", "türk telekom 5g",
            "mobile network investment",
            "telecom infrastructure turkey",
        ],
        "hisseler": ["TCELL", "TTKOM"],
        "etki_yonu": "pozitif",
        "etki_gucu": "orta",
        "etki_tipi": "direkt",
        "aciklama": "5G yatırımları telekom şirketlerinin büyüme potansiyelini artırır",
    },

    "telekom_duzenleme": {
        "keywords": [
            "btk karar", "btk imposes", "btk tariff", "btk tarife",
            "telekomünikasyon düzenleme", "telecom regulation turkey",
            "turkcell tarife", "türk telekom tarife",
            "mobile tariff regulation", "mobile operator tariff turkey",
            "telecom tariff regulation", "btk mobile limit",
            "turkey mobile regulator", "internet fiyat düzenleme",
        ],
        "hisseler": ["TCELL", "TTKOM"],
        "etki_yonu": "negatif",
        "etki_gucu": "orta",
        "etki_tipi": "direkt",
        "aciklama": "BTK tarife kısıtlamaları telekom şirketlerinin fiyatlama gücünü sınırlar",
    },

    "turkcell_ozel": {
        "keywords": [
            "turkcell", "tcell", "turkcell kâr",
            "turkcell abone", "turkcell büyüme",
            "turkcell dijital", "turkcell fizy",
            "turkcell tv+", "turkcell temettü",
        ],
        "hisseler": ["TCELL"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Turkcell'e özgü gelişme",
    },

    "turk_telekom_ozel": {
        "keywords": [
            "türk telekom", "ttkom", "türk telekom kâr",
            "türk telekom fiber", "türk telekom büyüme",
            "türk telekom abone", "türk telekom temettü",
        ],
        "hisseler": ["TTKOM"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Türk Telekom'a özgü gelişme",
    },
}

# ---------------------------------------------------------------------------
# Holding sektörü — finansal domain knowledge haritası
# ---------------------------------------------------------------------------
HOLDING_HARITASI: Dict[str, Any] = {

    "koc_holding_ozel": {
        "keywords": [
            "koç holding", "kchol", "koç kâr",
            "koç büyüme", "koç temettü",
            "ford otosan koç", "arçelik koç",
            "tüpraş koç", "koç grup",
        ],
        "hisseler": ["KCHOL"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Koç Holding'e özgü gelişme",
    },

    "sabanci_holding_ozel": {
        "keywords": [
            "sabancı holding", "sahol", "sabancı kâr",
            "sabancı büyüme", "sabancı temettü",
            "akbank sabancı", "enerjisa sabancı",
            "sabancı grup", "sabancı yatırım",
        ],
        "hisseler": ["SAHOL"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Sabancı Holding'e özgü gelişme",
    },
}

# ---------------------------------------------------------------------------
# GYO & İnşaat sektörü — finansal domain knowledge haritası
# ---------------------------------------------------------------------------
GYO_INSAAT_HARITASI: Dict[str, Any] = {

    "konut_fiyat_artisi": {
        "keywords": [
            "konut fiyatları arttı", "ev fiyatları yükseldi",
            "turkey housing prices rise", "property prices turkey",
            "konut talebi arttı", "housing demand turkey",
            "mortgage turkey", "konut kredisi",
            "turkey real estate boom",
        ],
        "hisseler": ["EKGYO"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Konut fiyat artışı Emlak Konut'un proje gelirlerini artırır",
    },

    "insaat_proje_ihale": {
        "keywords": [
            "enka inşaat", "enkai", "enka proje",
            "enka ihale", "enka sözleşme",
            "enka kâr", "enka büyüme",
            "emlak konut", "ekgyo", "toki proje",
            "kentsel dönüşüm proje",
        ],
        "hisseler": ["EKGYO", "ENKAI"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "İnşaat şirketlerine özgü proje ve ihale gelişmeleri",
    },

    "faiz_konut_etkisi": {
        "keywords": [
            "konut kredisi faizi düştü", "mortgage rate falls turkey",
            "housing loan rate cut", "konut faizi indirim",
            "affordable housing turkey", "konut erişilebilirlik",
        ],
        "hisseler": ["EKGYO"],
        "etki_yonu": "pozitif",
        "etki_gucu": "orta",
        "etki_tipi": "direkt",
        "aciklama": "Konut kredisi faiz düşüşü konut talebini artırır, Emlak Konut satışlarını destekler",
    },
}

# ---------------------------------------------------------------------------
# Gıda & İçecek sektörü — finansal domain knowledge haritası
# ---------------------------------------------------------------------------
GIDA_HARITASI: Dict[str, Any] = {

    "hammadde_gida_artisi": {
        "keywords": [
            "wheat price rises", "wheat prices surge", "wheat supply shortage",
            "wheat exports", "wheat supply", "ukraine wheat", "black sea grain",
            "sugar price up",
            "buğday fiyatı arttı", "buğday fiyatı savaş", "şeker fiyatı arttı",
            "cocoa price rises", "kakao fiyatı",
            "corn price up", "mısır fiyatı",
            "grain prices up", "food commodity prices", "food prices rise war",
            "soybean prices", "palm oil price", "livestock feed costs",
            "gıda hammadde", "agricultural commodity",
        ],
        "hisseler": ["ULKER", "AEFES", "CCOLA"],
        "etki_yonu": "negatif",
        "etki_gucu": "orta",
        "etki_tipi": "direkt",
        "aciklama": "Hammadde fiyat artışı gıda şirketlerinin üretim maliyetlerini yükseltir",
    },

    "ulker_ozel": {
        "keywords": [
            "ülker", "ulker", "ülker kâr",
            "ülker büyüme", "ülker ihracat",
            "ülker çikolata", "ülker temettü",
            "pladis", "yıldız holding gıda",
        ],
        "hisseler": ["ULKER"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Ülker'e özgü gelişme",
    },

    "efes_ozel": {
        "keywords": [
            "anadolu efes", "aefes", "efes bira",
            "efes kâr", "efes büyüme",
            "efes rusya", "efes ukrayna",
            "ab inbev efes", "efes temettü",
        ],
        "hisseler": ["AEFES"],
        "etki_yonu": "karma",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Anadolu Efes'e özgü gelişme",
    },

    "ccola_ozel": {
        "keywords": [
            "coca cola içecek", "ccola", "cci",
            "coca cola türkiye", "ccola kâr",
            "ccola büyüme", "coca cola bottler turkey",
        ],
        "hisseler": ["CCOLA"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Coca Cola İçecek'e özgü gelişme",
    },
}

# ---------------------------------------------------------------------------
# Cam & Kimya sektörü — finansal domain knowledge haritası
# ---------------------------------------------------------------------------
CAM_KIMYA_HARITASI: Dict[str, Any] = {

    "cam_talep_artisi": {
        "keywords": [
            "şişecam", "sise", "sisecam",
            "şişecam kâr", "cam talebi",
            "flat glass demand", "glass price",
            "şişecam ihracat", "şişecam büyüme",
            "solar panel glass", "auto glass demand",
            "şişecam sözleşme", "şişecam temettü",
        ],
        "hisseler": ["SISE"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Şişecam'a özgü ve cam sektörü gelişmeleri",
    },

    "enerji_cam_etkisi": {
        "keywords": [
            "natural gas price cam", "energy cost glass",
            "doğalgaz cam maliyeti", "energy intensive glass",
        ],
        "hisseler": ["SISE"],
        "etki_yonu": "negatif",
        "etki_gucu": "orta",
        "etki_tipi": "direkt",
        "aciklama": "Enerji cam üretiminin en büyük maliyet kalemi, doğalgaz artışı marjları baskılar",
    },
}

# ---------------------------------------------------------------------------
# Beyaz Eşya & Tüketici Elektroniği — finansal domain knowledge haritası
# ---------------------------------------------------------------------------
BEYAZ_ESYA_ELEKTRONIK_HARITASI: Dict[str, Any] = {

    "avrupa_tuketici_talebi": {
        "keywords": [
            "europe consumer spending", "european retail sales",
            "eu consumer demand", "europe household spending",
            "european consumer confidence",
            "avrupa tüketici harcaması", "avrupa perakende",
            "europe disposable income",
            "consumer electronics demand europe",
            "home appliance demand europe",
        ],
        "hisseler": ["ARCLK", "VESTL"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Avrupa tüketici talebi Arçelik ve Vestel'in en büyük ihracat pazarını etkiler",
    },

    "avrupa_tuketici_dusus": {
        "keywords": [
            "europe consumer confidence falls",
            "european retail sales drop",
            "eu consumer spending weak",
            "europe household budget cuts",
            "avrupa tüketici güveni düştü",
            "europe economic recession consumer",
            "white goods demand falls europe",
            "consumer electronics weak europe",
            "european consumer spending drops",
            "europe consumer spending falls",
            "european spending decline",
            "europe q3 consumer",
        ],
        "hisseler": ["ARCLK", "VESTL"],
        "etki_yonu": "negatif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Avrupa tüketici talebi düşüşü beyaz eşya ve elektronik ihracatını olumsuz etkiler",
    },

    "euro_kur_etkisi": {
        "keywords": [
            "euro strengthens", "euro rises",
            "eur/try rises", "euro güçlendi",
            "euro dollar parity", "strong euro",
            "eurusd rises", "euro appreciation",
        ],
        "hisseler": ["ARCLK", "VESTL"],
        "etki_yonu": "pozitif",
        "etki_gucu": "orta",
        "etki_tipi": "direkt",
        "aciklama": "Euro güçlenmesi ihracat gelirlerinin TL karşılığını artırır",
    },

    "hammadde_metal_artisi": {
        "keywords": [
            "aluminum price up", "bakır fiyatı arttı",
            "metal prices surge", "raw material costs rise",
            "component prices rise electronics",
            "chip price increase",
        ],
        "hisseler": ["ARCLK", "VESTL"],
        "etki_yonu": "negatif",
        "etki_gucu": "orta",
        "etki_tipi": "direkt",
        "aciklama": "Hammadde ve bileşen fiyat artışı üretim maliyetlerini yükseltir",
    },

    "arcelik_ozel": {
        "keywords": [
            "arçelik", "arcelik", "beko",
            "arçelik kâr", "arçelik ihracat",
            "arçelik büyüme", "arçelik avrupa",
            "arclk", "arçelik temettü",
            "arçelik fabrika", "beko brand",
            "arçelik acquisitions", "arçelik satın alma",
            "grundig arçelik", "blomberg arçelik",
        ],
        "hisseler": ["ARCLK"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Arçelik'e özgü gelişme",
    },

    "vestel_ozel": {
        "keywords": [
            "vestel", "vestl", "vestel elektronik",
            "vestel kâr", "vestel tv", "vestel ihracat",
            "vestel büyüme", "vestel fabrika",
            "vestel temettü", "vestel ev aletleri",
            "vestel white goods", "vestel solar",
        ],
        "hisseler": ["VESTL"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Vestel'e özgü gelişme",
    },
}

# ---------------------------------------------------------------------------
# Tarım & Gübre sektörü — finansal domain knowledge haritası
# ---------------------------------------------------------------------------
TARIM_GUBRE_HARITASI: Dict[str, Any] = {

    "dogalgaz_gubre_etkisi": {
        "keywords": [
            "natural gas price gubre",
            "natural gas fertilizer cost",
            "ammonia price rises",
            "nitrogen fertilizer cost",
            "gübre hammadde maliyeti",
            "doğalgaz gübre üretim",
            "natural gas ammonia",
            "urea price rises",
            "fertilizer production cost",
        ],
        "hisseler": ["GUBRF"],
        "etki_yonu": "negatif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Doğalgaz gübre üretiminin ana hammaddesi, fiyat artışı Gübre Fabrikaları maliyetlerini yükseltir",
    },

    "tarim_sezonu_talep": {
        "keywords": [
            "tractor sales turkey",
            "farm equipment sales",
            "agricultural machinery demand",
            "agricultural season turkey",
            "farming season turkey",
            "tarım makinesi talebi",
            "türkiye traktör satış",
            "traktör satışı arttı",
        ],
        "hisseler": ["GUBRF", "TTRAK"],
        "etki_yonu": "pozitif",
        "etki_gucu": "orta",
        "etki_tipi": "direkt",
        "aciklama": "Tarım sezonu gübre ve tarım makinesi talebini artırır",
    },

    "traktor_satis": {
        "keywords": [
            "tractor sales turkey", "türkiye traktör satışları",
            "agricultural machinery demand",
            "farm equipment sales",
            "tarım makinesi talebi",
            "traktör satışı arttı",
            "turkish tractor", "turkey tractor",
            "tractor record turkey", "farming season turkey",
            "türkiye traktör satış",
        ],
        "hisseler": ["TTRAK"],
        "etki_yonu": "pozitif",
        "etki_gucu": "orta",
        "etki_tipi": "direkt",
        "aciklama": "Türkiye traktör satışları Türk Traktör gelirlerini doğrudan etkiler",
    },

    "gubrf_ozel": {
        "keywords": [
            "gübre fabrikaları", "gubrf",
            "gübre fabrika kâr", "gübre üretim",
            "türkiye gübre", "gubre fabrika",
        ],
        "hisseler": ["GUBRF"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Gübre Fabrikaları'na özgü gelişme",
    },

    "ttrak_ozel": {
        "keywords": [
            "türk traktör", "ttrak", "turk traktor",
            "türk traktör kâr", "türk traktör satış",
            "case new holland turkey",
            "türk traktör büyüme",
        ],
        "hisseler": ["TTRAK"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Türk Traktör'e özgü gelişme",
    },
}

# ---------------------------------------------------------------------------
# Kimya & Soda sektörü — finansal domain knowledge haritası
# ---------------------------------------------------------------------------
KIMYA_SODA_HARITASI: Dict[str, Any] = {

    "soda_kul_fiyati": {
        "keywords": [
            "soda ash price", "soda ash demand",
            "trona price", "sodium carbonate",
            "soda kül fiyatı", "soda ash supply",
            "soda ash glass industry",
            "soda ash market",
        ],
        "hisseler": ["SODA"],
        "etki_yonu": "karma",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Soda külü fiyatı Soda Sanayii'nin hem üretim hem satış gelirlerini etkiler",
    },

    "cam_talep_soda": {
        "keywords": [
            "glass industry demand",
            "flat glass production",
            "container glass demand",
            "cam sektörü talep",
            "glass manufacturing up",
            "solar glass demand",
            "soda ash glass", "glass industry soda",
            "soda ash demand glass", "glass boom soda",
            "soda ash demand rises", "soda ash glass industry boom",
            "glass industry boom soda", "global glass industry",
            "soda ash rises glass",
        ],
        "hisseler": ["SODA", "TRKCM", "SISE"],
        "etki_yonu": "pozitif",
        "etki_gucu": "orta",
        "etki_tipi": "direkt",
        "aciklama": "Cam endüstrisi talebi soda külü ve cam üreticilerini olumlu etkiler",
    },

    "trakya_cam_ozel": {
        "keywords": [
            "trakya cam", "trkcm", "trakya glass",
            "trakya cam kâr", "trakya cam üretim",
            "trakya cam ihracat", "trakya cam büyüme",
            "trakya cam temettü",
        ],
        "hisseler": ["TRKCM"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Trakya Cam'a özgü gelişme",
    },

    "soda_sanayii_ozel": {
        "keywords": [
            "soda sanayii", "soda sanayi",
            "soda sanayii kâr", "soda üretim",
            "soda sanayii büyüme", "soda sanayii temettü",
            "eti soda", "kazan soda",
        ],
        "hisseler": ["SODA"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Soda Sanayii'ne özgü gelişme",
    },
}

# ---------------------------------------------------------------------------
# Enerji Üretim sektörü — finansal domain knowledge haritası
# ---------------------------------------------------------------------------
ENERJI_URETIM_HARITASI: Dict[str, Any] = {

    "elektrik_uretim_fiyat": {
        "keywords": [
            "electricity price turkey", "elektrik fiyatı türkiye",
            "power generation turkey", "elektrik üretim",
            "energy price regulation turkey",
            "turkey electricity tariff",
            "renewable energy turkey",
            "yenilenebilir enerji türkiye",
            "wind energy turkey", "rüzgar enerjisi",
            "solar energy turkey", "güneş enerjisi türkiye",
            "hydropower turkey", "hidroelektrik türkiye",
        ],
        "hisseler": ["ZOREN", "ODAS", "AKENR", "ALARK"],
        "etki_yonu": "karma",
        "etki_gucu": "orta",
        "etki_tipi": "direkt",
        "aciklama": "Elektrik üretim fiyatları ve enerji politikaları elektrik üreticilerini etkiler",
    },

    "zorlu_ozel": {
        "keywords": [
            "zorlu enerji", "zoren", "zorlu holding",
            "zorlu kâr", "zorlu üretim",
            "zorlu temettü", "zorlu büyüme",
            "vestel zorlu", "zorlu group",
        ],
        "hisseler": ["ZOREN"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Zorlu Enerji'ye özgü gelişme",
    },

    "odas_ozel": {
        "keywords": [
            "odaş elektrik", "odas",
            "odaş kâr", "odaş üretim",
            "odaş enerji", "odaş büyüme",
        ],
        "hisseler": ["ODAS"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Odaş Elektrik'e özgü gelişme",
    },

    "alarko_ozel": {
        "keywords": [
            "alarko", "alark",
            "alarko holding", "alarko kâr",
            "alarko enerji", "alarko inşaat",
            "alarko büyüme", "alarko temettü",
        ],
        "hisseler": ["ALARK"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Alarko'ya özgü gelişme",
    },
}

# ---------------------------------------------------------------------------
# Madencilik & Enerji (Park Elektrik) — finansal domain knowledge haritası
# ---------------------------------------------------------------------------
MADENCILIK_ENERJI_HARITASI: Dict[str, Any] = {

    "bakir_fiyati_park": {
        "keywords": [
            "copper price rises", "copper price up",
            "copper price hits", "copper price record",
            "copper price surge", "copper 10-year high",
            "copper rally", "copper supply shortage",
            "lme copper", "lme copper rises",
            "bakır fiyatı arttı", "copper demand",
            "copper mining", "copper supply",
            "copper price 10-year", "copper price high",
            "copper hits high", "copper all time high",
            "copper price record high",
        ],
        "hisseler": ["PRKME"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Bakır fiyatı artışı Park Elektrik'in maden gelirlerini artırır",
    },

    "park_elektrik_ozel": {
        "keywords": [
            "park elektrik", "prkme",
            "park elektrik kâr", "park maden",
            "park elektrik büyüme", "park elektrik üretim",
            "park elektrik temettü",
        ],
        "hisseler": ["PRKME"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Park Elektrik'e özgü gelişme",
    },
}

# ---------------------------------------------------------------------------
# Yer Hizmetleri (Çelebi) — finansal domain knowledge haritası
# ---------------------------------------------------------------------------
YER_HIZMETLERI_HARITASI: Dict[str, Any] = {

    "havacilik_trafik_celebi": {
        "keywords": [
            "çelebi yer hizmetleri", "celebi ground",
            "clebi", "çelebi kâr",
            "çelebi büyüme", "çelebi havalimanı",
            "airport ground services",
            "ground handling turkey",
            "çelebi temettü",
        ],
        "hisseler": ["CLEBI"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Çelebi havacılık trafiğine bağlı gelir elde eder",
    },
}

# ---------------------------------------------------------------------------
# Medya, Yazılım & Diğer Holding — finansal domain knowledge haritası
# ---------------------------------------------------------------------------
MEDYA_DIGER_HARITASI: Dict[str, Any] = {

    "dohol_ozel": {
        "keywords": [
            "doğan holding", "dohol", "dogan holding",
            "doğan kâr", "doğan medya",
            "doğan enerji", "doğan büyüme",
            "doğan temettü", "d-smart", "doğan group",
        ],
        "hisseler": ["DOHOL"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Doğan Holding'e özgü gelişme",
    },

    "logo_yazilim_ozel": {
        "keywords": [
            "logo yazılım", "logo software",
            "logo kâr", "logo büyüme",
            "logo erp", "logo cloud",
            "logo temettü", "logo dijital",
            "türkiye yazılım", "erp turkey",
        ],
        "hisseler": ["LOGO"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Logo Yazılım'a özgü gelişme",
    },

    "dijital_donusum_yazilim": {
        "keywords": [
            "digital transformation turkey",
            "dijital dönüşüm türkiye",
            "cloud software demand",
            "erp market growth",
            "enterprise software turkey",
            "kurumsal yazılım büyüme",
        ],
        "hisseler": ["LOGO"],
        "etki_yonu": "pozitif",
        "etki_gucu": "orta",
        "etki_tipi": "direkt",
        "aciklama": "Dijital dönüşüm trendi Logo Yazılım'ın büyüme potansiyelini artırır",
    },

    "aghol_ozel": {
        "keywords": [
            "anadolu grubu", "aghol",
            "anadolu group", "aghol kâr",
            "anadolu efes holding", "anadolu otomotiv",
            "aghol büyüme", "aghol temettü",
        ],
        "hisseler": ["AGHOL"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Anadolu Grubu'na özgü gelişme",
    },

    "tkfen_ozel": {
        "keywords": [
            "tekfen holding", "tkfen", "tekfen",
            "tekfen kâr", "tekfen inşaat",
            "tekfen tarfin", "tekfen büyüme",
            "tekfen temettü", "tekfen enerji",
        ],
        "hisseler": ["TKFEN"],
        "etki_yonu": "pozitif",
        "etki_gucu": "yüksek",
        "etki_tipi": "direkt",
        "aciklama": "Tekfen Holding'e özgü gelişme",
    },
}

# ---------------------------------------------------------------------------
# Viral / beklenmedik olay haritası (Ronaldo/Coca-Cola tipi)
# ---------------------------------------------------------------------------
VIRAL_ETKI_HARITASI: Dict[str, Any] = {

    "unlu_sirket_olayi": {
        "keywords": [
            "coca cola ronaldo", "ronaldo coca cola",
            "elon musk twitter", "trump tariff",
            "celebrity endorsement", "viral product",
            "boycott", "boykot",
            "product recall", "ürün geri çağırma",
            "scandal company", "şirket skandalı",
            "ceo arrested", "ceo fraud",
            "accounting fraud", "muhasebe skandalı",
        ],
        "hisseler": [],
        "bist_geneli": True,
        "etki_tipi": "viral",
        "aciklama": "Viral/beklenmedik olay - ilgili şirketi direkt etkiler",
    },
}

# ---------------------------------------------------------------------------
# Genel BIST / etki yok filtreleri
# ---------------------------------------------------------------------------
_ETKI_YOK_KELIMELER = [
    "china local bank", "regional bank china",
    "sports", "entertainment", "celebrity",
    "weather", "climate summit",
]

_GENEL_BIST_KELIMELER = [
    "china bank", "chinese bank", "bank collapse",
    "crypto", "bitcoin", "blockchain",
    "us housing", "real estate crisis",
    "tech layoffs", "startup",
]

_ETKI_YOK_LOWER   = [k.lower() for k in _ETKI_YOK_KELIMELER]
_GENEL_BIST_LOWER = [k.lower() for k in _GENEL_BIST_KELIMELER]

# ---------------------------------------------------------------------------
# Ana eşleştirme fonksiyonu
# ---------------------------------------------------------------------------

def match(text: str) -> Dict:
    lower = text.lower().replace("-", " ")
    hisseler: Set[str] = set()
    madenler: Set[str] = set()
    dovizler: Set[str] = set()
    etki_detaylari: List[Dict] = []

    # 1. Etki yok → erken çıkış
    if any(k in lower for k in _ETKI_YOK_LOWER):
        return {
            "hisseler": [],
            "madenler": [],
            "dovizler": [],
            "etki_tipi": "yok",
            "bist_geneli": False,
            "etki_detaylari": [],
        }

    # 2. Genel BIST haberleri → hisse eşleşmesi yapma
    if any(k in lower for k in _GENEL_BIST_LOWER):
        for keyword, maden in MADEN_MAP.items():
            if keyword in lower:
                madenler.add(maden)
        for keyword, doviz in DOVIZ_MAP.items():
            if keyword in lower:
                dovizler.add(doviz)
        return {
            "hisseler": [],
            "madenler": sorted(madenler),
            "dovizler": sorted(dovizler),
            "etki_tipi": "genel",
            "bist_geneli": True,
            "etki_detaylari": [],
        }

    # 3. Bankacılık haritası taraması
    etkilemez = BANKACILIK_HARITASI["etkilemez_cikis"]
    if any(k in lower for k in etkilemez):
        return {
            "hisseler": [],
            "madenler": [],
            "dovizler": [],
            "etki_tipi": "yok",
            "bist_geneli": False,
            "etki_detaylari": [],
            "aciklama": "Yabancı bankacılık haberi — Türk bankalarını direkt etkilemez",
        }

    for trigger_adi, trigger_data in BANKACILIK_HARITASI.items():
        if trigger_adi == "etkilemez_cikis":
            continue
        for keyword in trigger_data["keywords"]:
            if keyword.lower() in lower:
                hisseler.update(trigger_data["hisseler"])
                etki_detaylari.append({
                    "trigger": trigger_adi,
                    "etki_yonu": trigger_data["etki_yonu"],
                    "etki_gucu": trigger_data["etki_gucu"],
                    "aciklama": trigger_data["aciklama"],
                })
                break

    # 3b. Enerji haritası taraması
    for trigger_adi, trigger_data in ENERJI_HARITASI.items():
        for keyword in trigger_data["keywords"]:
            if keyword.lower() in lower:
                hisseler.update(trigger_data["hisseler"])
                etki_detaylari.append({
                    "trigger": trigger_adi,
                    "etki_yonu": trigger_data["etki_yonu"],
                    "etki_gucu": trigger_data["etki_gucu"],
                    "aciklama": trigger_data["aciklama"],
                })
                break

    # 3c. Savunma haritası taraması
    _gida_engel = [
        "wheat", "grain", "corn", "crop", "harvest",
        "fertilizer", "agricultural", "food commodity",
        "agricultural price", "food price",
        "buğday", "tahıl", "gıda fiyatı", "hasat",
        "livestock", "soybean", "palm oil",
    ]
    savunma_engel = any(k in lower for k in _gida_engel)
    etkilemez_savunma = SAVUNMA_HARITASI["etkilemez_savunma"]
    if not savunma_engel and not any(k in lower for k in etkilemez_savunma):
        for trigger_adi, trigger_data in SAVUNMA_HARITASI.items():
            if trigger_adi == "etkilemez_savunma":
                continue
            for keyword in trigger_data["keywords"]:
                if keyword.lower() in lower:
                    hisseler.update(trigger_data["hisseler"])
                    etki_detaylari.append({
                        "trigger": trigger_adi,
                        "etki_yonu": trigger_data["etki_yonu"],
                        "etki_gucu": trigger_data["etki_gucu"],
                        "aciklama": trigger_data["aciklama"],
                    })
                    break

    # 3d. Havacılık haritası taraması
    etkilemez_havacilik = HAVACILIK_HARITASI["etkilemez_havacilik"]
    if not any(k in lower for k in etkilemez_havacilik):
        for trigger_adi, trigger_data in HAVACILIK_HARITASI.items():
            if trigger_adi == "etkilemez_havacilik":
                continue
            for keyword in trigger_data["keywords"]:
                if keyword.lower() in lower:
                    hisseler.update(trigger_data["hisseler"])
                    etki_detaylari.append({
                        "trigger": trigger_adi,
                        "etki_yonu": trigger_data["etki_yonu"],
                        "etki_gucu": trigger_data["etki_gucu"],
                        "aciklama": trigger_data["aciklama"],
                    })
                    break

    # 3e. Demir-Çelik haritası taraması
    etkilemez_demir_celik = DEMIR_CELIK_HARITASI["etkilemez_demir_celik"]
    if not any(k in lower for k in etkilemez_demir_celik):
        for trigger_adi, trigger_data in DEMIR_CELIK_HARITASI.items():
            if trigger_adi == "etkilemez_demir_celik":
                continue
            for keyword in trigger_data["keywords"]:
                if keyword.lower() in lower:
                    hisseler.update(trigger_data["hisseler"])
                    etki_detaylari.append({
                        "trigger": trigger_adi,
                        "etki_yonu": trigger_data["etki_yonu"],
                        "etki_gucu": trigger_data["etki_gucu"],
                        "aciklama": trigger_data["aciklama"],
                    })
                    break

    # 3f. Madencilik haritası taraması
    for trigger_adi, trigger_data in MADENCILIK_HARITASI.items():
        for keyword in trigger_data["keywords"]:
            if keyword.lower() in lower:
                hisseler.update(trigger_data["hisseler"])
                etki_detaylari.append({
                    "trigger": trigger_adi,
                    "etki_yonu": trigger_data["etki_yonu"],
                    "etki_gucu": trigger_data["etki_gucu"],
                    "aciklama": trigger_data["aciklama"],
                })
                break

    # 3g. Perakende haritası taraması
    for trigger_adi, trigger_data in PERAKENDE_HARITASI.items():
        for keyword in trigger_data["keywords"]:
            if keyword.lower() in lower:
                hisseler.update(trigger_data["hisseler"])
                etki_detaylari.append({
                    "trigger": trigger_adi,
                    "etki_yonu": trigger_data["etki_yonu"],
                    "etki_gucu": trigger_data["etki_gucu"],
                    "aciklama": trigger_data["aciklama"],
                })
                break

    # 3h. Otomotiv haritası taraması
    for trigger_adi, trigger_data in OTOMOTIV_HARITASI.items():
        for keyword in trigger_data["keywords"]:
            if keyword.lower() in lower:
                hisseler.update(trigger_data["hisseler"])
                etki_detaylari.append({
                    "trigger": trigger_adi,
                    "etki_yonu": trigger_data["etki_yonu"],
                    "etki_gucu": trigger_data["etki_gucu"],
                    "aciklama": trigger_data["aciklama"],
                })
                break

    # 3i. Telekom haritası taraması
    for trigger_adi, trigger_data in TELEKOM_HARITASI.items():
        for keyword in trigger_data["keywords"]:
            if keyword.lower() in lower:
                hisseler.update(trigger_data["hisseler"])
                etki_detaylari.append({
                    "trigger": trigger_adi,
                    "etki_yonu": trigger_data["etki_yonu"],
                    "etki_gucu": trigger_data["etki_gucu"],
                    "aciklama": trigger_data["aciklama"],
                })
                break

    # 3j. Holding haritası taraması
    for trigger_adi, trigger_data in HOLDING_HARITASI.items():
        for keyword in trigger_data["keywords"]:
            if keyword.lower() in lower:
                hisseler.update(trigger_data["hisseler"])
                etki_detaylari.append({
                    "trigger": trigger_adi,
                    "etki_yonu": trigger_data["etki_yonu"],
                    "etki_gucu": trigger_data["etki_gucu"],
                    "aciklama": trigger_data["aciklama"],
                })
                break

    # 3k. GYO & İnşaat haritası taraması
    for trigger_adi, trigger_data in GYO_INSAAT_HARITASI.items():
        for keyword in trigger_data["keywords"]:
            if keyword.lower() in lower:
                hisseler.update(trigger_data["hisseler"])
                etki_detaylari.append({
                    "trigger": trigger_adi,
                    "etki_yonu": trigger_data["etki_yonu"],
                    "etki_gucu": trigger_data["etki_gucu"],
                    "aciklama": trigger_data["aciklama"],
                })
                break

    # 3l. Gıda haritası taraması
    for trigger_adi, trigger_data in GIDA_HARITASI.items():
        for keyword in trigger_data["keywords"]:
            if keyword.lower() in lower:
                hisseler.update(trigger_data["hisseler"])
                etki_detaylari.append({
                    "trigger": trigger_adi,
                    "etki_yonu": trigger_data["etki_yonu"],
                    "etki_gucu": trigger_data["etki_gucu"],
                    "aciklama": trigger_data["aciklama"],
                })
                break

    # 3m. Cam & Kimya haritası taraması
    for trigger_adi, trigger_data in CAM_KIMYA_HARITASI.items():
        for keyword in trigger_data["keywords"]:
            if keyword.lower() in lower:
                hisseler.update(trigger_data["hisseler"])
                etki_detaylari.append({
                    "trigger": trigger_adi,
                    "etki_yonu": trigger_data["etki_yonu"],
                    "etki_gucu": trigger_data["etki_gucu"],
                    "aciklama": trigger_data["aciklama"],
                })
                break

    # 3n. Beyaz Eşya & Elektronik haritası taraması
    for trigger_adi, trigger_data in BEYAZ_ESYA_ELEKTRONIK_HARITASI.items():
        for keyword in trigger_data["keywords"]:
            if keyword.lower() in lower:
                hisseler.update(trigger_data["hisseler"])
                etki_detaylari.append({
                    "trigger": trigger_adi,
                    "etki_yonu": trigger_data["etki_yonu"],
                    "etki_gucu": trigger_data["etki_gucu"],
                    "aciklama": trigger_data["aciklama"],
                })
                break

    # 3o. Tarım & Gübre haritası taraması
    for trigger_adi, trigger_data in TARIM_GUBRE_HARITASI.items():
        for keyword in trigger_data["keywords"]:
            if keyword.lower() in lower:
                hisseler.update(trigger_data["hisseler"])
                etki_detaylari.append({
                    "trigger": trigger_adi,
                    "etki_yonu": trigger_data["etki_yonu"],
                    "etki_gucu": trigger_data["etki_gucu"],
                    "aciklama": trigger_data["aciklama"],
                })
                break

    # 3p. Kimya & Soda haritası taraması
    for trigger_adi, trigger_data in KIMYA_SODA_HARITASI.items():
        for keyword in trigger_data["keywords"]:
            if keyword.lower() in lower:
                hisseler.update(trigger_data["hisseler"])
                etki_detaylari.append({
                    "trigger": trigger_adi,
                    "etki_yonu": trigger_data["etki_yonu"],
                    "etki_gucu": trigger_data["etki_gucu"],
                    "aciklama": trigger_data["aciklama"],
                })
                break

    # 3r. Enerji Üretim haritası taraması
    for trigger_adi, trigger_data in ENERJI_URETIM_HARITASI.items():
        for keyword in trigger_data["keywords"]:
            if keyword.lower() in lower:
                hisseler.update(trigger_data["hisseler"])
                etki_detaylari.append({
                    "trigger": trigger_adi,
                    "etki_yonu": trigger_data["etki_yonu"],
                    "etki_gucu": trigger_data["etki_gucu"],
                    "aciklama": trigger_data["aciklama"],
                })
                break

    # 3s. Madencilik & Enerji (Park) haritası taraması
    for trigger_adi, trigger_data in MADENCILIK_ENERJI_HARITASI.items():
        for keyword in trigger_data["keywords"]:
            if keyword.lower() in lower:
                hisseler.update(trigger_data["hisseler"])
                etki_detaylari.append({
                    "trigger": trigger_adi,
                    "etki_yonu": trigger_data["etki_yonu"],
                    "etki_gucu": trigger_data["etki_gucu"],
                    "aciklama": trigger_data["aciklama"],
                })
                break

    # 3t. Yer Hizmetleri haritası taraması
    for trigger_adi, trigger_data in YER_HIZMETLERI_HARITASI.items():
        for keyword in trigger_data["keywords"]:
            if keyword.lower() in lower:
                hisseler.update(trigger_data["hisseler"])
                etki_detaylari.append({
                    "trigger": trigger_adi,
                    "etki_yonu": trigger_data["etki_yonu"],
                    "etki_gucu": trigger_data["etki_gucu"],
                    "aciklama": trigger_data["aciklama"],
                })
                break

    # 3u. Medya, Yazılım & Diğer haritası taraması
    for trigger_adi, trigger_data in MEDYA_DIGER_HARITASI.items():
        for keyword in trigger_data["keywords"]:
            if keyword.lower() in lower:
                hisseler.update(trigger_data["hisseler"])
                etki_detaylari.append({
                    "trigger": trigger_adi,
                    "etki_yonu": trigger_data["etki_yonu"],
                    "etki_gucu": trigger_data["etki_gucu"],
                    "aciklama": trigger_data["aciklama"],
                })
                break

    # 3v. Viral etki haritası taraması
    for trigger_adi, trigger_data in VIRAL_ETKI_HARITASI.items():
        for keyword in trigger_data["keywords"]:
            if keyword.lower() in lower:
                etki_detaylari.append({
                    "trigger": trigger_adi,
                    "etki_yonu": "karma",
                    "etki_gucu": "yüksek",
                    "aciklama": trigger_data["aciklama"],
                })
                break

    # 4. Şirket adı / ticker eşleşmesi (Aho-Corasick, DB tabanlı; basarisizsa HISSE_MAP fallback)
    automaton = _get_automaton()
    if automaton is not None:
        for _, (alias, ticker) in automaton.iter(lower):
            hisseler.add(ticker)
    else:
        for keyword, ticker in HISSE_MAP.items():
            if keyword in lower:
                hisseler.add(ticker)

    # 5. Sektör keyword eşleşmesi
    for keyword, tickers in SEKTOR_MAP.items():
        if keyword in lower:
            hisseler.update(tickers)

    # 6. Global makro/sektör eşleşmesi
    _savunma_hisseleri = {"ASELS", "RODRG"}
    for ifade, varliklar in GLOBAL_ETKI_MAP.items():
        if ifade in lower:
            # Gıda haberi varsa savunmaya özgü GLOBAL entry'leri atla
            if savunma_engel and set(v for v in varliklar if isinstance(v, str) and v.isupper()).issubset(_savunma_hisseleri):
                continue
            for v in varliklar:
                if v.isupper():
                    hisseler.add(v)
                else:
                    madenler.add(v)

    # 7. Maden eşleşmesi
    for keyword, maden in MADEN_MAP.items():
        if keyword in lower:
            madenler.add(maden)

    # 8. Döviz eşleşmesi
    for keyword, doviz in DOVIZ_MAP.items():
        if keyword in lower:
            dovizler.add(doviz)

    # 9. Etki tipini belirle
    if len(hisseler) > 4:
        etki_tipi = "sistemik"
    elif len(hisseler) > 0:
        etki_tipi = "direkt"
    else:
        etki_tipi = "genel"

    return {
        "hisseler": sorted(hisseler),
        "madenler": sorted(madenler),
        "dovizler": sorted(dovizler),
        "etki_tipi": etki_tipi,
        "bist_geneli": len(hisseler) == 0 and len(madenler) == 0,
        "etki_detaylari": etki_detaylari,
    }


# ---------------------------------------------------------------------------
# Alaka filtresi — sadece gercekten finansal etkisi olan haberleri tut
# ---------------------------------------------------------------------------

FINANSAL_BAGLAM_KELIMELERI = [
    "hisse", "hisseleri", "hissesi", "borsa", "bist", "yüzde", "%",
    "kâr", "kar açıkladı", "zarar", "yükseldi", "düştü", "geriledi",
    "tl", "dolar", "euro", "kur", "yatırım", "yatırımcı",
    "milyar", "milyon", "değer kaybetti", "değer kazandı",
    "satış", "gelir", "bilanço", "temettü", "ihracat", "ithalat",
    "rekor", "büyüme", "daralma", "endeks", "kapanış", "açılış",
    "fiyat", "piyasa değeri", "sözleşme", "ihale", "ortaklık",
]

MAKRO_KELIMELER = [
    "tcmb", "merkez bankası", "faiz kararı", "faiz oranı",
    "enflasyon", "tüfe", "üfe", "fed", "federal reserve",
    "cari açık", "işsizlik", "büyüme oranı", "gsyh", "gsmh",
    "kredi notu", "moody's", "fitch", "s&p", "döviz kuru",
    "hazine", "bütçe açığı", "dış ticaret", "ppk",
]

_FINANSAL_BAGLAM_LOWER = [k.lower() for k in FINANSAL_BAGLAM_KELIMELERI]
_MAKRO_LOWER = [k.lower() for k in MAKRO_KELIMELER]


def haberi_degerlendir(text: str) -> Dict[str, Any]:
    """
    Bir haberin sisteme kaydedilip kaydedilmeyecegine karar verir.

    Donus:
        {
            "tut": bool,
            "kategori": "hisse" | "genel" | "ret",
            "eslesme": <match() ciktisi>,
        }
    """
    lower = text.lower().replace("-", " ")
    eslesme = match(text)

    has_entity = bool(eslesme["hisseler"] or eslesme["madenler"] or eslesme["dovizler"])
    has_finansal_baglam = any(k in lower for k in _FINANSAL_BAGLAM_LOWER)
    has_makro = any(k in lower for k in _MAKRO_LOWER)

    # Sirket/varlik eslesmesi VAR ve finansal baglam VAR -> tut (hisse kategorisi)
    if has_entity and has_finansal_baglam:
        return {"tut": True, "kategori": "hisse", "eslesme": eslesme}

    # Makro/genel piyasa haberi -> tut (genel kategori)
    if has_makro:
        return {"tut": True, "kategori": "genel", "eslesme": eslesme}

    # Sirket eslesmesi var ama finansal baglam yoksa (ör. sirket ismi gecen
    # alakasiz bir haber) -> reddet
    return {"tut": False, "kategori": "ret", "eslesme": eslesme}
