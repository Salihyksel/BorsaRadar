from __future__ import annotations

import structlog
from transformers import pipeline as hf_pipeline

logger = structlog.get_logger(__name__)

_LABEL_MAP: dict[str, str] = {
    "positive": "pozitif",
    "LABEL_1": "pozitif",
    "negative": "negatif",
    "LABEL_0": "negatif",
}

_MAX_CHARS = 512

POZITIF_KELIMELER = [
    "kar", "kâr", "artış", "yükseldi", "rekor", "büyüme",
    "kazanç", "başarı", "güçlü", "olumlu", "ihracat",
    "sözleşme", "yatırım", "temettü",
]

NEGATIF_KELIMELER = [
    "zarar", "düştü", "geriledi", "kayıp", "kriz", "risk",
    "endişe", "satış baskısı", "uyarı", "zayıf", "borç",
    "iflas", "para cezası", "soruşturma", "sert düşüş",
]


def _keyword_score(text: str) -> tuple[int, int]:
    """Metindeki pozitif ve negatif kelime sayılarını döndürür."""
    lower = text.lower()
    pos = sum(1 for k in POZITIF_KELIMELER if k in lower)
    neg = sum(1 for k in NEGATIF_KELIMELER if k in lower)
    return pos, neg


class SentimentAnalyzer:
    def __init__(self, model_name: str = "savasy/bert-base-turkish-sentiment-cased"):
        self.model_name = model_name
        self._pipeline = None

    def _load(self) -> None:
        if self._pipeline is None:
            logger.info("sentiment_model_loading", model=self.model_name)
            self._pipeline = hf_pipeline(
                "sentiment-analysis",
                model=self.model_name,
                truncation=True,
            )
            logger.info("sentiment_model_loaded", model=self.model_name)

    def _bert_analyze(self, text: str) -> dict:
        self._load()
        result = self._pipeline(text[:_MAX_CHARS])[0]
        label = result.get("label", "")
        skor = round(float(result.get("score", 0.5)), 4)
        sentiment = _LABEL_MAP.get(label, "notr")
        return {"sentiment": sentiment, "skor": skor}

    def analyze(self, text: str) -> dict:
        try:
            pos_count, neg_count = _keyword_score(text)

            if pos_count > neg_count:
                logger.debug("sentiment_keyword_decision", sentiment="pozitif",
                             pos=pos_count, neg=neg_count)
                return {"sentiment": "pozitif", "skor": 0.75}

            if neg_count > pos_count:
                logger.debug("sentiment_keyword_decision", sentiment="negatif",
                             pos=pos_count, neg=neg_count)
                return {"sentiment": "negatif", "skor": 0.75}

            # Eşit veya sıfır: BERT'e sor
            logger.debug("sentiment_bert_decision", pos=pos_count, neg=neg_count)
            return self._bert_analyze(text)

        except Exception:
            logger.exception("sentiment_analysis_failed")
            return {"sentiment": "notr", "skor": 0.5}

    def analyze_batch(self, texts: list[str]) -> list[dict]:
        return [self.analyze(t) for t in texts]


# Singleton
_analyzer = SentimentAnalyzer()


def analyze_sentiment(text: str) -> dict:
    return _analyzer.analyze(text)
