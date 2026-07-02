from datetime import datetime
from typing import Dict, List, Optional

import structlog
import yfinance as yf

logger = structlog.get_logger(__name__)

BIST_TICKERS: List[str] = [
    "THYAO", "GARAN", "EREGL", "TUPRS", "ASELS",
    "BIMAS", "AKBNK", "ISCTR", "KCHOL", "SISE",
    "PGSUS", "TCELL", "VESTL", "FROTO", "PETKM",
    "TAVHL", "TOASO", "ARCLK", "EKGYO", "SAHOL",
    "YKBNK", "HALKB", "VAKBN", "TTKOM", "TKFEN",
    "LOGO",  "MGROS", "CCOLA", "AGHOL", "ULKER",
]


def fetch_single_ticker(ticker: str) -> Optional[Dict]:
    try:
        t = yf.Ticker(f"{ticker}.IS")
        info = t.fast_info
        fiyat = info.last_price
        prev_close = info.previous_close
        if not fiyat or not prev_close:
            return None
        degisim = (fiyat - prev_close) / prev_close * 100
        return {
            "ticker": ticker,
            "fiyat": round(float(fiyat), 2),
            "degisim_yuzde": round(float(degisim), 4),
            "hacim": int(info.last_volume or 0),
            "guncelleme_zamani": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "veri_kaynagi": "yfinance",
        }
    except Exception as e:
        logger.warning("bist.fetch.hata", ticker=ticker, hata=str(e))
        return None


def fetch_bist_data() -> List[Dict]:
    sonuclar = []
    for ticker in BIST_TICKERS:
        result = fetch_single_ticker(ticker)
        if result:
            sonuclar.append(result)
    logger.info("bist.fetch_all.done", basarili=len(sonuclar), total=len(BIST_TICKERS))
    return sonuclar
