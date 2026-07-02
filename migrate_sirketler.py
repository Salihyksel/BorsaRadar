import sys
sys.path.insert(0, '.')
from collections import defaultdict
import pymysql
import config
from nlp.entity_matcher import HISSE_MAP

# Ticker -> [alias1, alias2, ...] grupla
ticker_aliases = defaultdict(list)
for alias, ticker in HISSE_MAP.items():
    ticker_aliases[ticker].append(alias)

# Ticker -> "resmi ad" (en uzun alias'ı ad olarak kullan, genelde en açıklayıcı)
def get_resmi_ad(ticker, aliases):
    return max(aliases, key=len).title()

conn = pymysql.connect(
    host=config.DB_HOST,
    user=config.DB_USER,
    password=config.DB_PASS,
    database=config.DB_NAME,
    port=config.DB_PORT,
    charset="utf8mb4",
)

cursor = conn.cursor()
eklenen_sirket = 0
eklenen_alias = 0

for ticker, aliases in ticker_aliases.items():
    ad = get_resmi_ad(ticker, aliases)
    cursor.execute(
        "INSERT IGNORE INTO sirketler (ticker, ad, piyasa) VALUES (%s, %s, 'BIST')",
        (ticker, ad)
    )
    if cursor.rowcount:
        eklenen_sirket += 1

    cursor.execute("SELECT id FROM sirketler WHERE ticker = %s", (ticker,))
    sirket_id = cursor.fetchone()[0]

    for alias in set(aliases):
        cursor.execute(
            "INSERT IGNORE INTO sirket_aliaslar (sirket_id, alias) VALUES (%s, %s)",
            (sirket_id, alias.lower())
        )
        if cursor.rowcount:
            eklenen_alias += 1

conn.commit()
print(f"Eklenen şirket: {eklenen_sirket}")
print(f"Eklenen alias: {eklenen_alias}")
print(f"Toplam ticker: {len(ticker_aliases)}")

cursor.close()
conn.close()
