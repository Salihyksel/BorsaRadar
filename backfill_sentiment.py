import sys
sys.path.insert(0, '.')
import pymysql
import config
from nlp.sentiment import analyze_sentiment

conn = pymysql.connect(
    host=config.DB_HOST, user=config.DB_USER, password=config.DB_PASS,
    database=config.DB_NAME, port=config.DB_PORT, charset="utf8mb4",
    cursorclass=pymysql.cursors.DictCursor,
)

cursor = conn.cursor()
cursor.execute("SELECT id, baslik FROM haberler")
rows = cursor.fetchall()

guncellenen = 0
for row in rows:
    sonuc = analyze_sentiment(row["baslik"])
    cursor.execute(
        "UPDATE haberler SET sentiment = %s, sentiment_skoru = %s WHERE id = %s",
        (sonuc["sentiment"], sonuc["skor"], row["id"])
    )
    guncellenen += 1

conn.commit()
print(f"Güncellenen haber sayısı: {guncellenen}")

cursor.close()
conn.close()
