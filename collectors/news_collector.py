import functools
import hashlib
import time
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Dict, List, Optional

import feedparser
import requests
import structlog

import config

logger = structlog.get_logger(__name__)

_RSS_TIMEOUT = 15   # saniye
_API_TIMEOUT = 10   # saniye

_RSS_KAYNAKLAR: List[Dict] = [
    {"ad": "BloombergHT",      "url": "https://www.bloomberght.com/rss"},
    {"ad": "Dunya Finans",     "url": "https://www.dunya.com/finans/rss",
                                "fallback_url": "https://www.dunya.com/rss"},
    {"ad": "BİST",             "url": "https://www.borsaistanbul.com/rss/news"},
    {"ad": "Hurriyet Ekonomi", "url": "https://www.hurriyet.com.tr/rss/ekonomi"},
    {"ad": "Sabah Ekonomi",    "url": "https://www.sabah.com.tr/rss/ekonomi.xml"},
    {"ad": "Yahoo Finance",    "url": "https://finance.yahoo.com/rss/topstories"},
    {"ad": "Investing.com",    "url": "https://www.investing.com/rss/news_25.rss"},
    {"ad": "MarketWatch",      "url": "https://feeds.marketwatch.com/marketwatch/topstories/"},
]

_NEWSAPI_URL   = "https://newsapi.org/v2/everything"
_NEWSAPI_QUERY = "borsa istanbul OR BIST OR türk lirası OR enflasyon"

_RSS_HEADERS = {
    "User-Agent": "BorsaRadar/1.0 (finansal veri toplayici)",
    "Accept":     "application/rss+xml, application/xml, text/xml",
}

FINANSAL_ANAHTAR_KELIMELER = [
    # Merkez bankaları
    "fed", "federal reserve", "fed reserve", "ecb", "boj", "bank of england",
    "tcmb", "merkez bankası", "central bank", "interest rate",
    "faiz", "rate hike", "rate cut",
    # Emtia ve enerji
    "oil", "crude", "brent", "opec", "natural gas", "petrol", "gold", "silver",
    "copper", "wheat", "corn", "platinum", "commodity", "energy",
    "altın", "altın fiyatı", "gümüş", "bakır", "enerji", "ham petrol", "doğalgaz",
    # Türkiye ekonomisi
    "turkey", "turkish", "lira", "bist", "borsa istanbul", "istanbul",
    "inflation", "enflasyon", "erdogan", "tcmb",
    "hisse senedi", "endeks", "döviz", "dolar", "euro", "sterlin",
    "ihracat", "ithalat", "cari açık", "büyüme", "gsyh",
    # Global ekonomi
    "gdp", "gdp growth", "recession", "resesyon", "powell", "lagarde",
    "china", "china economy", "europe economy", "manufacturing", "pmi",
    "inflation data", "cpi", "ppi",
    "ukraine", "russia", "middle east", "iran",
    "geopolitical", "war", "conflict", "sanctions", "tariff", "trade war",
    # Şirket finansalları
    "earnings", "quarterly results", "revenue",
    # Piyasalar
    "stock market", "s&p", "nasdaq", "dow jones", "dow",
    "emerging market", "emerging markets", "dollar", "euro",
    "bonds", "yield", "treasury",
]

ALAKASIZ_KELIMELER = [
    # Spor
    "futbol", "maç sonucu", "gol", "şampiyon", "lig", "transfer",
    "ronaldo", "messi", "neymar", "barcelona", "real madrid",
    "galatasaray maç", "fenerbahçe maç", "beşiktaş maç", "trabzonspor",
    "football", "soccer", "nba", "nfl", "tennis", "golf",
    "world cup", "dünya kupası maçı", "olimpiyat", "olympic",
    "eastbourne", "wimbledon", "roland garros",
    # Gündem/Siyaset (finansal etkisi olmayanlar)
    "deprem listesi", "son depremler nerede oldu", "belediye başkanı",
    "kurultay", "istifa", "kaza yaptı", "hayatını kaybetti",
    "başsağlığı", "mühimmat deposu", "patlama haberi",
    "film festivali", "kamp programı",
    # Eğlence/Kültür
    "dizi", "film", "müzik", "konsert", "sanat",
    "celebrity", "entertainment", "gossip",
    # Kişisel finans (TR'ye etki etmeyenler)
    "mortgage", "refinance", "heloc", "home equity",
    "student loan", "savings account", "apy", "credit card",
    "insurance", "real estate listing", "housing market",
    "recipe", "sports",
    "crypto wallet", "nft", "meme coin",
]

# Ünlü + şirket kombinasyonu haberleri (Ronaldo/Coca-Cola tipi viral olaylar)
# Bu çiftlerden her ikisi de başlıkta geçiyorsa haber finansal sayılır
_VIRAL_UNLU_SIRKET_CIFTI = [
    ("ronaldo", "coca cola"), ("ronaldo", "pepsi"),
    ("messi", "pepsi"), ("messi", "adidas"),
    ("elon musk", "tesla"), ("elon musk", "twitter"),
    ("warren buffett", "berkshire"),
    ("trump", "tariff"), ("trump", "tarife"),
    ("boycott", "coca cola"), ("boykot", "coca cola"),
    ("boycott", "pepsi"), ("boykot", "pepsi"),
    ("scandal", "volkswagen"), ("scandal", "enron"),
    ("fraud", "accounting"), ("muhasebe", "skandal"),
    ("ceo arrested", "fraud"), ("ceo tutukland", "şirket"),
]

_FINANSAL_LOWER = [k.lower() for k in FINANSAL_ANAHTAR_KELIMELER]
_ALAKASIZ_LOWER = [k.lower() for k in ALAKASIZ_KELIMELER]


def _finansal_mi(baslik: str) -> bool:
    """
    1. Viral ünlü+şirket kombinasyonu varsa direkt True döner.
    2. Alakasız kelime içeriyorsa False döner.
    3. Finansal anahtar kelime içeriyorsa True döner.
    """
    baslik_lower = baslik.lower()

    # Viral etki kontrolü: ünlü + şirket çifti geçiyorsa finansal say
    for unlu, sirket in _VIRAL_UNLU_SIRKET_CIFTI:
        if unlu in baslik_lower and sirket in baslik_lower:
            return True

    if any(k in baslik_lower for k in _ALAKASIZ_LOWER):
        return False
    return any(k in baslik_lower for k in _FINANSAL_LOWER)


# ── Retry decorator ────────────────────────────────────────────────────────────

def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0, backoff: float = 2.0):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = base_delay
            last_exc: Exception = RuntimeError("retry çağrılmadı")
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    last_exc = exc
                    if attempt < max_retries:
                        logger.warning(
                            "retry.bekliyor",
                            fonksiyon=func.__name__,
                            deneme=attempt,
                            sonraki_bekleme=delay,
                            hata=str(exc),
                        )
                        time.sleep(delay)
                        delay *= backoff
            raise last_exc
        return wrapper
    return decorator


# ── Yardımcılar ────────────────────────────────────────────────────────────────

def _sha256(metin: str) -> str:
    return hashlib.sha256(metin.encode("utf-8")).hexdigest()


def _haber_hash(url: Optional[str], baslik: str, yayin_zamani: Optional[str]) -> str:
    kaynak = url.strip() if url and url.strip() else f"{baslik}|{yayin_zamani}"
    return _sha256(kaynak)


def _parse_zaman(entry) -> Optional[str]:
    try:
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            return datetime(*entry.published_parsed[:6]).isoformat(timespec="seconds")
        if hasattr(entry, "updated_parsed") and entry.updated_parsed:
            return datetime(*entry.updated_parsed[:6]).isoformat(timespec="seconds")
        if hasattr(entry, "published") and entry.published:
            return parsedate_to_datetime(entry.published).isoformat(timespec="seconds")
    except Exception:
        pass
    return None


def _newsapi_zaman(published_at: Optional[str]) -> Optional[str]:
    if not published_at:
        return None
    try:
        return datetime.fromisoformat(published_at.replace("Z", "+00:00")).isoformat(
            timespec="seconds"
        )
    except ValueError:
        return None


# ── RSS çekici ─────────────────────────────────────────────────────────────────

@retry_with_backoff(max_retries=3, base_delay=2.0, backoff=2.0)
def _fetch_rss(kaynak_adi: str, url: str) -> List[dict]:
    response = requests.get(url, headers=_RSS_HEADERS, timeout=_RSS_TIMEOUT)
    response.raise_for_status()

    feed = feedparser.parse(response.content)

    if feed.bozo and not feed.entries:
        raise ValueError(f"RSS parse hatası [{kaynak_adi}]: {feed.get('bozo_exception')}")

    haberler: List[dict] = []
    for entry in feed.entries:
        baslik      = (entry.get("title") or "").strip()
        haber_url   = (entry.get("link")  or "").strip() or None
        yayin_zaman = _parse_zaman(entry)

        if not baslik:
            continue

        if not _finansal_mi(baslik):
            continue

        haberler.append({
            "baslik":       baslik,
            "url":          haber_url,
            "kaynak":       kaynak_adi,
            "yayin_zamani": yayin_zaman,
            "url_hash":     _haber_hash(haber_url, baslik, yayin_zaman),
        })

    return haberler


# ── NewsAPI çekici ─────────────────────────────────────────────────────────────

@retry_with_backoff(max_retries=3, base_delay=2.0, backoff=2.0)
def _fetch_newsapi(api_key: str) -> List[dict]:
    params = {
        "q":        _NEWSAPI_QUERY,
        "language": "tr",
        "pageSize": 20,
        "apiKey":   api_key,
    }
    response = requests.get(_NEWSAPI_URL, params=params, timeout=_API_TIMEOUT)
    response.raise_for_status()

    veri = response.json()
    if veri.get("status") != "ok":
        raise ValueError(f"NewsAPI hata yanıtı: {veri.get('message')}")

    haberler: List[dict] = []
    for article in veri.get("articles", []):
        baslik      = (article.get("title") or "").strip()
        haber_url   = (article.get("url")   or "").strip() or None
        yayin_zaman = _newsapi_zaman(article.get("publishedAt"))

        if not baslik or baslik == "[Removed]":
            continue

        haberler.append({
            "baslik":       baslik,
            "url":          haber_url,
            "kaynak":       article.get("source", {}).get("name") or "NewsAPI",
            "yayin_zamani": yayin_zaman,
            "url_hash":     _haber_hash(haber_url, baslik, yayin_zaman),
        })

    return haberler


# ── Public API ─────────────────────────────────────────────────────────────────

def fetch_news_data() -> List[dict]:
    """
    Tüm kaynaklardan haberleri toplar, liste olarak döner.
    Kaydetme işlemi çağıran tarafa (main.py) bırakılmıştır.
    Kullanım: from collectors.news_collector import fetch_news_data
    """
    haberler: List[dict] = []

    for kaynak in _RSS_KAYNAKLAR:
        try:
            sonuclar = _fetch_rss(kaynak["ad"], kaynak["url"])
            haberler.extend(sonuclar)
            logger.info("news.kaynak.ok", kaynak=kaynak["ad"], sayi=len(sonuclar))
        except Exception as exc:
            fallback = kaynak.get("fallback_url")
            if fallback:
                try:
                    sonuclar = _fetch_rss(kaynak["ad"], fallback)
                    haberler.extend(sonuclar)
                    logger.info("news.kaynak.fallback.ok", kaynak=kaynak["ad"], sayi=len(sonuclar))
                    continue
                except Exception as exc2:
                    logger.error("news.kaynak.fallback.hata", kaynak=kaynak["ad"], hata=str(exc2))
            logger.error("news.kaynak.hata", kaynak=kaynak["ad"], hata=str(exc))

    api_key: str = config.NEWS_API_KEY or ""
    if api_key:
        try:
            sonuclar = _fetch_newsapi(api_key)
            haberler.extend(sonuclar)
            logger.info("news.kaynak.ok", kaynak="NewsAPI", sayi=len(sonuclar))
        except Exception as exc:
            logger.error("news.kaynak.hata", kaynak="NewsAPI", hata=str(exc))
    else:
        logger.debug("news.newsapi.atla", sebep="NEWS_API_KEY tanımlı değil")

    logger.info("news.fetch_all.bitti", toplam=len(haberler))
    return haberler
