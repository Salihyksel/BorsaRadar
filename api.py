import os
from flask import Flask, jsonify
from flask_cors import CORS
import pymysql
import pymysql.cursors
import yfinance as yf
from datetime import datetime, timedelta

import config

app = Flask(__name__)
CORS(app)


def get_db():
    return pymysql.connect(
        host=config.DB_HOST,
        user=config.DB_USER,
        password=config.DB_PASS,
        database=config.DB_NAME,
        port=int(os.environ.get("DB_PORT", 3306)),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )


_kur_cache = {"data": None, "ts": None}
_KUR_CACHE_TTL = 60

@app.route("/api/kurlar")
def kurlar():
    try:
        now = datetime.now()
        if _kur_cache["data"] and _kur_cache["ts"] and (now - _kur_cache["ts"]).total_seconds() < _KUR_CACHE_TTL:
            return jsonify(_kur_cache["data"])

        from collectors.tcmb_collector import fetch_tcmb_data
        k = fetch_tcmb_data()
        result = {
            "USD_TRY":     k["USD"],
            "EUR_TRY":     k["EUR"],
            "usd_degisim": k["USD_degisim"],
            "eur_degisim": k["EUR_degisim"],
            "guncelleme":  now.isoformat(),
        }
        _kur_cache["data"] = result
        _kur_cache["ts"] = now
        return jsonify(result)
    except Exception as e:
        if _kur_cache["data"]:
            return jsonify(_kur_cache["data"])
        return jsonify({"error": str(e)}), 500


@app.route("/api/madenler")
def madenler():
    try:
        conn = get_db()
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT m1.maden_kodu, m1.fiyat_usd, m1.fiyat_try,
                           m1.degisim_yuzde, m1.guncelleme_zamani
                    FROM maden_fiyatlari m1
                    INNER JOIN (
                        SELECT maden_kodu, MAX(id) AS max_id
                        FROM maden_fiyatlari
                        GROUP BY maden_kodu
                    ) m2 ON m1.id = m2.max_id
                """)
                rows = cur.fetchall()
        result = {}
        for row in rows:
            guncelleme = row["guncelleme_zamani"]
            result[row["maden_kodu"]] = {
                "fiyat_usd":     float(row["fiyat_usd"]) if row["fiyat_usd"] is not None else None,
                "fiyat_try":     float(row["fiyat_try"]) if row["fiyat_try"] is not None else None,
                "degisim_yuzde": float(row["degisim_yuzde"] or 0),
                "guncelleme":    guncelleme.isoformat() if guncelleme else None,
            }
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/hisseler")
def hisseler():
    try:
        conn = get_db()
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT h1.ticker, h1.fiyat, h1.degisim_yuzde,
                           h1.hacim, h1.guncelleme_zamani AS guncelleme
                    FROM hisse_fiyatlari h1
                    INNER JOIN (
                        SELECT ticker, MAX(id) AS max_id
                        FROM hisse_fiyatlari
                        GROUP BY ticker
                    ) h2 ON h1.id = h2.max_id
                    ORDER BY h1.ticker ASC
                """)
                rows = cur.fetchall()
        result = []
        for row in rows:
            guncelleme = row["guncelleme"]
            result.append({
                "ticker": row["ticker"],
                "fiyat": float(row["fiyat"]) if row["fiyat"] is not None else None,
                "degisim_yuzde": float(row["degisim_yuzde"]) if row["degisim_yuzde"] is not None else None,
                "hacim": row["hacim"],
                "guncelleme": guncelleme.isoformat() if guncelleme else None,
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/haberler")
def haberler():
    try:
        conn = get_db()
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        h.id,
                        h.baslik,
                        h.url,
                        h.kaynak,
                        h.yayin_zamani,
                        h.sentiment,
                        h.etki_skoru,
                        GROUP_CONCAT(
                            e.varlik_kodu
                            ORDER BY e.varlik_kodu
                            SEPARATOR ','
                        ) AS varliklar
                    FROM haberler h
                    LEFT JOIN haber_varlik_eslesme e ON h.id = e.haber_id
                    GROUP BY h.id
                    ORDER BY h.yayin_zamani DESC
                    LIMIT 100
                """)
                rows = cur.fetchall()
        simdi = datetime.now()
        bugun_baslangic = simdi.replace(hour=0, minute=0, second=0, microsecond=0)
        dun_baslangic = bugun_baslangic - timedelta(days=1)
        hafta_baslangic = bugun_baslangic - timedelta(days=7)

        result = []
        for row in rows:
            yayin = row["yayin_zamani"]
            if isinstance(yayin, str):
                yayin = datetime.fromisoformat(yayin)
            varliklar = row["varliklar"].split(",") if row["varliklar"] else []

            if yayin and yayin >= bugun_baslangic:
                gun_grubu = "bugün"
            elif yayin and yayin >= dun_baslangic:
                gun_grubu = "dün"
            elif yayin and yayin >= hafta_baslangic:
                gun_grubu = "bu_hafta"
            else:
                gun_grubu = "eski"

            result.append({
                "id": row["id"],
                "baslik": row["baslik"],
                "url": row["url"],
                "kaynak": row["kaynak"],
                "sentiment": row["sentiment"],
                "etki_skoru": row["etki_skoru"],
                "yayin_zamani": yayin.isoformat() if yayin else None,
                "gun_grubu": gun_grubu,
                "varliklar": varliklar,
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/gecmis/<sembol>")
def gecmis(sembol):
    try:
        MADEN_MAP = {
            "XAU": "GC=F",  "XAG": "SI=F",
            "XPT": "PL=F",  "XPD": "PA=F",
            "USD": "USDTRY=X", "EUR": "EURTRY=X",
        }
        yf_sembol = MADEN_MAP.get(sembol, f"{sembol}.IS")

        hist = yf.Ticker(yf_sembol).history(period="1mo", interval="1d")
        if hist.empty:
            return jsonify([])

        result = []
        for tarih, row in hist.iterrows():
            result.append({
                "tarih":   tarih.strftime("%Y-%m-%d"),
                "kapanis": round(float(row["Close"]), 2),
                "acilis":  round(float(row["Open"]),  2),
                "yuksek":  round(float(row["High"]),  2),
                "dusuk":   round(float(row["Low"]),   2),
                "hacim":   int(row["Volume"]),
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/hisse/<ticker>")
def hisse_gecmis(ticker):
    try:
        conn = get_db()
        baslangic = datetime.utcnow() - timedelta(days=90)
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT fiyat, degisim_yuzde, hacim, guncelleme_zamani
                    FROM hisse_fiyatlari
                    WHERE ticker = %s AND guncelleme_zamani >= %s
                    ORDER BY guncelleme_zamani ASC
                """, (ticker.upper(), baslangic))
                rows = cur.fetchall()
        if not rows:
            return jsonify({"error": f"{ticker.upper()} için veri bulunamadı"}), 404
        gecmis = []
        for row in rows:
            guncelleme = row["guncelleme_zamani"]
            gecmis.append({
                "fiyat": float(row["fiyat"]) if row["fiyat"] is not None else None,
                "degisim_yuzde": float(row["degisim_yuzde"]) if row["degisim_yuzde"] is not None else None,
                "hacim": row["hacim"],
                "guncelleme": guncelleme.isoformat() if guncelleme else None,
            })
        return jsonify({"ticker": ticker.upper(), "gecmis": gecmis})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5001)), debug=False)
