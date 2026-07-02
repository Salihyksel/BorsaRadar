import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from typing import Dict

import pymysql
import structlog
from apscheduler.schedulers.blocking import BlockingScheduler

import config
from collectors.bist_collector import fetch_bist_data
from collectors.metals_collector import fetch_metals_data
from collectors.news_collector import fetch_news_data
from collectors.tcmb_collector import fetch_tcmb_data
from nlp.entity_matcher import match
from nlp.sentiment import analyze_sentiment

logger = structlog.get_logger(__name__)


def _get_conn() -> pymysql.connections.Connection:
    return pymysql.connect(
        host=config.DB_HOST,
        user=config.DB_USER,
        password=config.DB_PASS,
        database=config.DB_NAME,
        port=config.DB_PORT,
        charset="utf8mb4",
    )


def _is_weekday_trading_hours() -> bool:
    now = datetime.now()
    return now.weekday() < 5 and 10 <= now.hour < 18


# ── Jobs ───────────────────────────────────────────────────────────────────────

def hisse_job() -> None:
    if not _is_weekday_trading_hours():
        return

    log = logger.bind(job="hisse_job")
    log.info("job.basladi")
    try:
        hisseler = fetch_bist_data()
        if not hisseler:
            log.warning("job.veri_yok")
            return

        conn = _get_conn()
        try:
            cursor = conn.cursor()
            for hisse in hisseler:
                cursor.execute(
                    """
                    INSERT INTO hisse_fiyatlari
                        (ticker, fiyat, degisim_yuzde, hacim, guncelleme_zamani, veri_kaynagi)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        hisse["ticker"],
                        hisse["fiyat"],
                        hisse["degisim_yuzde"],
                        hisse["hacim"],
                        hisse["guncelleme_zamani"],
                        hisse["veri_kaynagi"],
                    ),
                )
            conn.commit()
            log.info("job.bitti", kaydedilen=len(hisseler))
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    except Exception as exc:
        log.error("job.hata", hata=str(exc))


def maden_job() -> None:
    log = logger.bind(job="maden_job")
    log.info("job.basladi")
    try:
        madenler = fetch_metals_data()
        if not madenler:
            log.warning("job.veri_yok")
            return

        conn = _get_conn()
        try:
            cursor = conn.cursor()
            for maden in madenler:
                cursor.execute(
                    """
                    INSERT INTO maden_fiyatlari
                        (maden_kodu, fiyat_usd, fiyat_try, degisim_yuzde, guncelleme_zamani)
                    VALUES (%s, %s, %s, %s, NOW())
                    """,
                    (maden["maden_kodu"], maden["fiyat_usd"], maden["fiyat_try"], maden.get("degisim_yuzde", 0)),
                )
            conn.commit()
            log.info("job.bitti", kaydedilen=len(madenler))
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    except Exception as exc:
        log.error("job.hata", hata=str(exc))


def _varlik_kaydet(cursor, haber_id: int, varliklar: Dict) -> None:
    for ticker in varliklar.get("hisseler", []):
        cursor.execute(
            """
            INSERT IGNORE INTO haber_varlik_eslesme
                (haber_id, varlik_turu, varlik_kodu, eslestirme_yontemi)
            VALUES (%s, 'hisse', %s, 'keyword')
            """,
            (haber_id, ticker),
        )
    for kod in varliklar.get("madenler", []):
        cursor.execute(
            """
            INSERT IGNORE INTO haber_varlik_eslesme
                (haber_id, varlik_turu, varlik_kodu, eslestirme_yontemi)
            VALUES (%s, 'maden', %s, 'keyword')
            """,
            (haber_id, kod),
        )
    for kod in varliklar.get("dovizler", []):
        cursor.execute(
            """
            INSERT IGNORE INTO haber_varlik_eslesme
                (haber_id, varlik_turu, varlik_kodu, eslestirme_yontemi)
            VALUES (%s, 'doviz', %s, 'keyword')
            """,
            (haber_id, kod),
        )


def haber_job() -> None:
    log = logger.bind(job="haber_job")
    log.info("job.basladi")
    try:
        haberler = fetch_news_data()
        if not haberler:
            log.warning("job.veri_yok")
            return

        conn = _get_conn()
        try:
            cursor = conn.cursor()
            kaydedilen = 0
            for haber in haberler:
                try:
                    baslik = haber["baslik"]
                    nlp_sonuc = analyze_sentiment(baslik)
                    varliklar = match(baslik)

                    cursor.execute(
                        """
                        INSERT IGNORE INTO haberler
                            (baslik, url, kaynak, yayin_zamani, url_hash,
                             sentiment, sentiment_skoru)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            baslik,
                            haber.get("url"),
                            haber.get("kaynak"),
                            haber.get("yayin_zamani"),
                            haber.get("url_hash"),
                            nlp_sonuc["sentiment"],
                            nlp_sonuc["skor"],
                        ),
                    )
                    if cursor.rowcount:
                        haber_id = cursor.lastrowid
                        _varlik_kaydet(cursor, haber_id, varliklar)
                        kaydedilen += 1

                except Exception as exc:
                    log.warning(
                        "job.haber_atlandi",
                        hata=str(exc),
                        baslik=haber.get("baslik", "")[:80],
                    )
                    continue

            conn.commit()
            log.info("job.bitti", cekilen=len(haberler), kaydedilen=kaydedilen)
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    except Exception as exc:
        log.error("job.hata", hata=str(exc))


def tcmb_job() -> None:
    log = logger.bind(job="tcmb_job")
    log.info("job.basladi")
    try:
        kur = fetch_tcmb_data()
        log.info("job.bitti", usd=kur.get("USD"), eur=kur.get("EUR"))
    except Exception as exc:
        log.error("job.hata", hata=str(exc))


# ── Scheduler kurulumu ─────────────────────────────────────────────────────────

def main() -> None:
    scheduler = BlockingScheduler(timezone="Europe/Istanbul")

    scheduler.add_job(hisse_job, "interval", minutes=1, id="hisse_job")
    scheduler.add_job(maden_job, "interval", minutes=5, id="maden_job")
    scheduler.add_job(haber_job, "interval", minutes=5, id="haber_job")
    scheduler.add_job(
        tcmb_job, "cron",
        hour=9, minute=5,
        day_of_week="mon-fri",
        id="tcmb_job",
    )

    print("BorsaRadar Scheduler başladı")
    print("Durdurmak için Ctrl+C")

    print("İlk çalıştırma başlıyor...")
    tcmb_job()
    maden_job()
    hisse_job()
    haber_job()
    print("İlk çalıştırma tamamlandı, scheduler devam ediyor...")

    try:
        scheduler.start()
    except KeyboardInterrupt:
        scheduler.shutdown()
        print("Scheduler durduruldu")


if __name__ == "__main__":
    main()
