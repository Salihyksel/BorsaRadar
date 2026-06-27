from datetime import datetime
from typing import Dict

import structlog
import yfinance as yf

import config

logger = structlog.get_logger(__name__)


def fetch_tcmb_data() -> Dict[str, float]:
    """
    yfinance ile anlık USD/TRY ve EUR/TRY kurlarını çeker.
    Dönen dict: {'USD': ..., 'EUR': ..., 'USD_degisim': ..., 'EUR_degisim': ...}
    """
    try:
        usd_info = yf.Ticker("USDTRY=X").fast_info
        eur_info = yf.Ticker("EURTRY=X").fast_info

        usd_fiyat = float(usd_info.last_price or 0)
        eur_fiyat = float(eur_info.last_price or 0)
        usd_prev  = float(usd_info.previous_close or 0)
        eur_prev  = float(eur_info.previous_close or 0)

        usd_degisim = 0.0
        eur_degisim = 0.0
        if usd_prev:
            usd_degisim = round((usd_fiyat - usd_prev) / usd_prev * 100, 2)
        if eur_prev:
            eur_degisim = round((eur_fiyat - eur_prev) / eur_prev * 100, 2)

        config.TCMB_USD_TRY = usd_fiyat
        config.TCMB_EUR_TRY = eur_fiyat

        logger.info(
            "tcmb.fetch.ok",
            usd_try=usd_fiyat,
            eur_try=eur_fiyat,
            zaman=datetime.now().isoformat(timespec="seconds"),
        )
        return {
            "USD":         round(usd_fiyat, 4),
            "EUR":         round(eur_fiyat, 4),
            "USD_degisim": usd_degisim,
            "EUR_degisim": eur_degisim,
        }
    except Exception as exc:
        logger.error("tcmb.fetch.basarisiz", hata=str(exc))
        # Fallback: son config değerleri veya sabit
        usd = config.TCMB_USD_TRY or 46.5
        eur = config.TCMB_EUR_TRY or 53.0
        return {"USD": usd, "EUR": eur, "USD_degisim": 0.0, "EUR_degisim": 0.0}
