import pymysql
import structlog

import config
from collectors.tcmb_collector import fetch_tcmb_data
from collectors.metals_collector import fetch_metals_data
from collectors.bist_collector import fetch_bist_data
from collectors.news_collector import fetch_news_data
from nlp.sentiment import analyze_sentiment
from nlp.entity_matcher import match, haberi_degerlendir

logger = structlog.get_logger(__name__)


def get_conn() -> pymysql.connections.Connection:
    return pymysql.connect(
        host=config.DB_HOST,
        user=config.DB_USER,
        password=config.DB_PASS,
        database=config.DB_NAME,
        charset="utf8mb4",
    )


# ── Adımlar ────────────────────────────────────────────────────────────────────

def adim_tcmb() -> bool:
    try:
        kur = fetch_tcmb_data()
        logger.info("adim.tcmb.ok", usd=kur.get("USD"), eur=kur.get("EUR"))
        return True
    except Exception as exc:
        logger.error("adim.tcmb.hata", hata=str(exc))
        return False


def adim_madenler(conn: pymysql.connections.Connection) -> int:
    try:
        madenler = fetch_metals_data()
        if not madenler:
            logger.warning("adim.madenler.veri_yok")
            return 0

        cursor = conn.cursor()
        for maden in madenler:
            cursor.execute(
                """
                INSERT INTO maden_fiyatlari
                    (maden_kodu, fiyat_usd, fiyat_try, degisim_yuzde, guncelleme_zamani)
                VALUES (%s, %s, %s, %s, NOW())
                """,
                (
                    maden["maden_kodu"],
                    maden["fiyat_usd"],
                    maden["fiyat_try"],
                    maden.get("degisim_yuzde", 0.0),
                ),
            )
        conn.commit()
        logger.info("adim.madenler.ok", sayi=len(madenler))
        return len(madenler)

    except Exception as exc:
        conn.rollback()
        logger.error("adim.madenler.hata", hata=str(exc))
        return 0


def adim_bist(conn: pymysql.connections.Connection) -> int:
    try:
        hisseler = fetch_bist_data()
        if not hisseler:
            logger.warning("adim.bist.veri_yok")
            return 0

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
        logger.info("adim.bist.ok", sayi=len(hisseler))
        return len(hisseler)

    except Exception as exc:
        conn.rollback()
        logger.error("adim.bist.hata", hata=str(exc))
        return 0


def _varlik_kaydet(cursor, haber_id: int, varliklar: dict) -> None:
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


def adim_haberler(conn: pymysql.connections.Connection) -> int:
    try:
        haberler = fetch_news_data()
        if not haberler:
            logger.warning("adim.haberler.veri_yok")
            return 0

        cursor = conn.cursor()
        kaydedilen = 0
        atlanan_alakasiz = 0
        for i, haber in enumerate(haberler):
            try:
                baslik = haber["baslik"]

                degerlendirme = haberi_degerlendir(baslik)
                if not degerlendirme["tut"]:
                    atlanan_alakasiz += 1
                    continue

                nlp_sonuc = analyze_sentiment(baslik)
                varliklar = degerlendirme["eslesme"]

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

                if cursor.rowcount:  # INSERT IGNORE → 0 ise duplicate
                    haber_id = cursor.lastrowid
                    _varlik_kaydet(cursor, haber_id, varliklar)
                    kaydedilen += 1

                if (i + 1) % 10 == 0:
                    logger.info(
                        "adim.haberler.ilerleme",
                        islenen=i + 1,
                        toplam=len(haberler),
                        kaydedilen=kaydedilen,
                    )

            except Exception as exc:
                logger.warning("adim.haberler.haber_atlandi", hata=str(exc),
                               baslik=haber.get("baslik", "")[:80])
                continue

        conn.commit()
        logger.info("adim.haberler.ok", cekilen=len(haberler), kaydedilen=kaydedilen, atlanan_alakasiz=atlanan_alakasiz)
        return kaydedilen

    except Exception as exc:
        conn.rollback()
        logger.error("adim.haberler.hata", hata=str(exc))
        return 0


# ── Ana akış ───────────────────────────────────────────────────────────────────

def main() -> None:
    logger.info("borsaradar.basladi")

    # 1. TCMB kuru
    tcmb_ok = adim_tcmb()
    if not tcmb_ok:
        logger.warning("tcmb.basarisiz.devam_ediliyor")

    # DB bağlantısını bir kez aç, tüm adımlarda paylaş
    try:
        conn = get_conn()
    except Exception as exc:
        logger.error("db.baglanti.hata", hata=str(exc))
        print("HATA: Veritabanına bağlanılamadı.")
        return

    try:
        maden_sayisi = adim_madenler(conn)
        hisse_sayisi = adim_bist(conn)
        haber_sayisi = adim_haberler(conn)
    finally:
        conn.close()

    logger.info(
        "borsaradar.bitti",
        tcmb=("ok" if tcmb_ok else "hata"),
        maden_kaydedilen=maden_sayisi,
        hisse_kaydedilen=hisse_sayisi,
        haber_kaydedilen=haber_sayisi,
    )
    print(
        f"\n=== BorsaRadar Özet ===\n"
        f"  TCMB kuru   : {'ok' if tcmb_ok else 'HATA'}\n"
        f"  Maden       : {maden_sayisi} kayıt\n"
        f"  Hisse       : {hisse_sayisi} kayıt\n"
        f"  Haber       : {haber_sayisi} kayıt\n"
    )


if __name__ == "__main__":
    main()
