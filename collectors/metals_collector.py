from datetime import datetime
from typing import Dict, List

import structlog
import yfinance as yf

logger = structlog.get_logger(__name__)

MADEN_SEMBOLLER: Dict[str, str] = {
    "XAU": "GC=F",   # Altın
    "XAG": "SI=F",   # Gümüş
    "XPT": "PL=F",   # Platin
    "XPD": "PA=F",   # Paladyum
}


def fetch_metals_data() -> List[dict]:
    from collectors.tcmb_collector import fetch_tcmb_data

    try:
        kurlar = fetch_tcmb_data()
        usd_try = kurlar.get("USD", 46.5) or 46.5
    except Exception as exc:
        logger.warning("metals.kur_alinamadi", hata=str(exc))
        usd_try = 46.5

    sonuclar = []
    for kod, sembol in MADEN_SEMBOLLER.items():
        try:
            info = yf.Ticker(sembol).fast_info
            fiyat_usd = float(info.last_price or 0)
            prev_close = float(info.previous_close or 0)

            if fiyat_usd == 0:
                logger.warning("metals.fiyat_sifir", kod=kod)
                continue

            degisim = 0.0
            if prev_close:
                degisim = round((fiyat_usd - prev_close) / prev_close * 100, 2)

            sonuclar.append({
                "maden_kodu":        kod,
                "fiyat_usd":         round(fiyat_usd, 4),
                "fiyat_try":         round(fiyat_usd * usd_try, 4),
                "degisim_yuzde":     degisim,
                "guncelleme_zamani": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            })
            logger.info("metals.fetch.ok", kod=kod, fiyat=fiyat_usd, degisim=degisim)
        except Exception as exc:
            logger.error("metals.fetch.hata", kod=kod, hata=str(exc))

    return sonuclar
