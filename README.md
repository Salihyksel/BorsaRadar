# 🇹🇷 BorsaRadar — Turkish Financial Intelligence Platform

> Real-time BIST 100 stocks, precious metals, and AI-powered financial news analysis for Turkish investors.

![Python](https://img.shields.io/badge/Python-3.9-blue)
![React](https://img.shields.io/badge/React-18-61dafb)
![Flask](https://img.shields.io/badge/Flask-2.x-black)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange)
![NLP](https://img.shields.io/badge/NLP-BERT--Turkish-green)

---

## 🚀 What is BorsaRadar?

BorsaRadar is an open-source financial intelligence dashboard that aggregates real-time market data from multiple sources and uses Natural Language Processing to analyze financial news, automatically matching each news article to the relevant BIST 100 stocks it may impact.

Unlike generic financial dashboards, BorsaRadar understands the **domain-specific relationships** between global events and Turkish stocks — for example, knowing that an OPEC production cut affects TUPRS (Tüpraş), or that a Fed rate hike impacts Turkish banking stocks.

---

## ✨ Features

### 📊 Market Data
- **BIST 100** real-time stock prices and daily change percentages
- **Precious Metals** — Gold (XAU), Silver (XAG), Platinum (XPT), Palladium (XPD)
- **Currency Rates** — USD/TRY and EUR/TRY (via yfinance)
- Auto-refresh every 60 seconds during market hours

### 📰 Smart News Pipeline
- Aggregates from 5+ financial news sources:
  - BloombergHT (Turkish)
  - Dünya Gazetesi (Turkish)
  - Yahoo Finance (English)
  - MarketWatch (English)
  - Investing.com (English)
- Financial news filtering — removes sports, entertainment and irrelevant content
- Automatic duplicate detection via SHA-256 URL hashing

### 🧠 NLP & Sentiment Analysis
- **Turkish BERT** (`savasy/bert-base-turkish-sentiment-cased`) for sentiment classification
- **Hybrid approach**: financial keyword matching + BERT model
- **Domain-specific impact mapping**: 20 sectors, 60+ companies
  - Banking: GARAN, AKBNK, ISCTR, YKBNK, VAKBN, HALKB
  - Energy: TUPRS, PETKM, AKENR, ZOREN
  - Defense: ASELS, RODRG
  - Aviation: THYAO, PGSUS, TAVHL
  - Steel: EREGL, KRDMD
  - Mining: KOZAL, KOZAA
  - And 14 more sectors...

### 🎨 Modern Dashboard
- Aurora dark theme with animated starfield background
- Real-time stock list with sparkline mini-charts
- Interactive price charts (TradingView Lightweight Charts)
- News feed with sentiment indicators and direct article links
- Sector-based filtering and search

---

## 🏗️ Architecture

```
Data Sources          Python Pipeline         Storage        Frontend
─────────────         ───────────────         ───────        ────────
yfinance ──────────►  bist_collector    ──►              ◄── React 18
yfinance ──────────►  metals_collector  ──►  MySQL 8.0   ◄── Recharts
yfinance ──────────►  tcmb_collector    ──►              ◄── Lightweight
RSS Feeds ─────────►  news_collector    ──►  (borsaradar)     Charts
                                │
                                ▼
                         NLP Pipeline
                         ├── sentiment.py (BERT-Turkish)
                         └── entity_matcher.py (20 sectors)
                                │
                                ▼
                      Flask REST API  ──────────────────► React Dashboard
                        (port 5001)
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Data Collection | Python 3.9, yfinance, feedparser, requests |
| NLP | HuggingFace Transformers, BERT-Turkish |
| Scheduling | APScheduler (BlockingScheduler) |
| Backend API | Flask, Flask-CORS |
| Database | MySQL 8.0, PyMySQL |
| Frontend | React 18, React Router v6 |
| Charts | TradingView Lightweight Charts, Recharts |
| Styling | Custom CSS, Aurora dark theme |

---

## 📦 Installation

### Prerequisites
- Python 3.9+
- MySQL 8.0+
- Node.js 16+

### Backend Setup

```bash
git clone https://github.com/Salihyksel/BorsaRadar.git
cd BorsaRadar
pip3 install -r requirements.txt
cp .env.example .env
# Edit .env with your database credentials
mysql -u root -p < database/schema.sql
python3 main.py
python3 api.py
```

### Frontend Setup

```bash
cd frontend
npm install
npm start
```

Dashboard available at `http://localhost:3000`

---

## ⚙️ Configuration

```env
DB_HOST=localhost
DB_USER=root
DB_PASS=your_password
DB_NAME=borsaradar
GEMINI_API_KEY=optional
NEWS_API_KEY=optional
```

---

## 📡 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/hisseler` | All BIST stocks with latest prices |
| `GET /api/madenler` | Precious metals prices (USD + TRY) |
| `GET /api/kurlar` | USD/TRY and EUR/TRY exchange rates |
| `GET /api/haberler` | Latest financial news with sentiment |
| `GET /api/gecmis/<symbol>` | 30-day price history for any asset |

---

## 🧪 NLP System — 100% Test Accuracy

✅ TCMB rate cut → All 6 banking stocks  
✅ OPEC production cut → TUPRS, AKENR  
✅ NATO defense spending → ASELS, RODRG  
✅ Jet fuel surge → THYAO, PGSUS  
✅ China steel exports → EREGL, KRDMD  
✅ Gold rally → KOZAL, KOZAA  
✅ Chinese bank collapse → Empty (correctly ignored)  
✅ Wheat prices + Ukraine → ULKER, AEFES, CCOLA (not defense)  

---

## 🗺️ Roadmap

- [ ] US stocks (S&P 500, NASDAQ) support
- [ ] Price movement prediction scoring
- [ ] Email/SMS alerts for high-impact news
- [ ] Deploy to subdomain (borsa-radar.salihyksl.com)
- [ ] Historical sentiment vs price correlation charts

---

## 📄 License

MIT License

---

## 👨‍💻 Author

Developed by [@Salihyksel](https://github.com/Salihyksel)

*Portfolio project demonstrating financial data engineering, NLP, and full-stack development.*
