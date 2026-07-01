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

import json
import time as _time
import hashlib

_CACHE_DIR = "/tmp/borsaradar_cache"
os.makedirs(_CACHE_DIR, exist_ok=True)

def _cache_path(key):
    h = hashlib.md5(key.encode()).hexdigest()
    return os.path.join(_CACHE_DIR, f"{h}.json")

def cached(key, ttl_seconds, compute_fn):
    path = _cache_path(key)
    try:
        if os.path.exists(path):
            mtime = os.path.getmtime(path)
            if _time.time() - mtime < ttl_seconds:
                with open(path, "r") as f:
                    return json.load(f)
    except Exception:
        pass

    result = compute_fn()

    try:
        tmp_path = path + f".tmp{os.getpid()}"
        with open(tmp_path, "w") as f:
            json.dump(result, f)
        os.replace(tmp_path, path)
    except Exception:
        pass

    return result



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
    def _compute():
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
        return result
    try:
        return jsonify(cached("madenler", 30, _compute))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/hisseler")
def hisseler():
    def _compute():
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
        return result
    try:
        return jsonify(cached("hisseler", 30, _compute))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/haberler")
def haberler():
    def _compute():
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
        return result
    try:
        return jsonify(cached("haberler", 60, _compute))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/gecmis/<sembol>")
def gecmis(sembol):
    from flask import request
    period_key = request.args.get("period", "3A")

    def _compute():
        MADEN_MAP = {
            "XAU": "GC=F",  "XAG": "SI=F",
            "XPT": "PL=F",  "XPD": "PA=F",
            "USD": "USDTRY=X", "EUR": "EURTRY=X",
        }
        yf_sembol = MADEN_MAP.get(sembol, f"{sembol}.IS")

        period_map = {
            "1H": ("5d", "15m"),
            "1A": ("1mo", "1d"),
            "3A": ("3mo", "1d"),
            "6A": ("6mo", "1d"),
            "1Y": ("1y", "1d"),
            "3Y": ("3y", "1wk"),
        }
        period, interval = period_map.get(period_key, ("3mo", "1d"))

        hist = yf.Ticker(yf_sembol).history(period=period, interval=interval)
        if hist.empty:
            return []

        result = []
        tarih_format = "%Y-%m-%d %H:%M" if interval in ("15m", "1h") else "%Y-%m-%d"
        for tarih, row in hist.iterrows():
            result.append({
                "tarih":   tarih.strftime(tarih_format),
                "kapanis": round(float(row["Close"]), 2),
                "acilis":  round(float(row["Open"]),  2),
                "yuksek":  round(float(row["High"]),  2),
                "dusuk":   round(float(row["Low"]),   2),
                "hacim":   int(row["Volume"]),
            })
        return result

    try:
        cache_key = f"gecmis:{sembol}:{period_key}"
        return jsonify(cached(cache_key, 300, _compute))
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
