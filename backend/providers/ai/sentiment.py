from __future__ import annotations

"""
Review Sentiment Analysis Provider
====================================
Sentiment analysis for product reviews using keyword-based analysis
with optional VADER enhancement.
"""
import logging
import re
from collections import Counter
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

__all__ = [
    "HAS_VADER",
    "analyze_sentiment",
    "analyze_review",
    "extract_review_insights",
]

# ---------------------------------------------------------------------------
# VADER availability flag
# ---------------------------------------------------------------------------
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer  # type: ignore

    HAS_VADER = True
    _vader_analyzer = SentimentIntensityAnalyzer()
except ImportError:
    HAS_VADER = False
    _vader_analyzer = None

# ---------------------------------------------------------------------------
# Keyword-based sentiment lexicon
# ---------------------------------------------------------------------------
_POSITIVE_WORDS = {
    "good", "great", "excellent", "amazing", "awesome", "fantastic", "wonderful",
    "perfect", "love", "loved", "loving", "best", "beautiful", "nice", "happy",
    "pleased", "satisfied", "recommend", "recommended", "quality", "superb",
    "outstanding", "brilliant", "delightful", "enjoy", "enjoyed", "impressive",
    "comfortable", "durable", "reliable", "fast", "quick", "smooth", "easy",
    "affordable", "value", "stylish", "elegant", "cute", "fresh", "clean",
    "helpful", "friendly", "professional", "accurate", "effective", "efficient",
    "sturdy", "solid", "premium", "luxurious", "gorgeous", "charming",
    "flawless", "seamless", "intuitive", "versatile", "lightweight", "compact",
}

_NEGATIVE_WORDS = {
    "bad", "terrible", "awful", "horrible", "worst", "poor", "disappointing",
    "disappointed", "hate", "hated", "useless", "broken", "defective", "waste",
    "wasted", "cheap", "flimsy", "ugly", "uncomfortable", "difficult", "hard",
    "slow", "late", "delayed", "wrong", "missing", "damaged", "dirty", "rough",
    "noisy", "loud", "heavy", "bulky", "complicated", "confusing", "frustrating",
    "frustrated", "annoying", "annoyed", "painful", "unreliable", "unstable",
    "rude", "unprofessional", "inaccurate", "ineffective", "overpriced",
    "expensive", "refund", "return", "returned", "complaint", "complain",
    "problem", "problems", "issue", "issues", "fail", "failed", "failure",
    "error", "errors", "crash", "crashed", "dead", "died", "garbage", "trash",
}

# Intensifiers and negators
_INTENSIFIERS = {
    "very": 1.5, "extremely": 2.0, "really": 1.5, "absolutely": 2.0,
    "totally": 1.5, "completely": 1.5, "highly": 1.5, "incredibly": 2.0,
    "quite": 1.2, "super": 1.5, "so": 1.3, "too": 1.3, "utterly": 2.0,
}

_NEGATORS = {
    "not", "no", "never", "neither", "nor", "hardly", "barely", "scarcely",
    "doesn't", "don't", "didn't", "won't", "wouldn't", "couldn't", "shouldn't",
    "isn't", "aren't", "wasn't", "weren't", "hasn't", "haven't", "hadn't",
}

# Praise/complaint/suggestion indicators
_PRAISE_INDICATORS = {
    "love", "loved", "great", "excellent", "amazing", "perfect", "best",
    "beautiful", "recommend", "awesome", "fantastic", "wonderful", "superb",
}

_COMPLAINT_INDICATORS = {
    "broken", "defective", "damaged", "wrong", "missing", "late", "delayed",
    "terrible", "awful", "horrible", "worst", "waste", "useless", "refund",
    "return", "complaint", "problem", "issue", "fail", "error",
}

_SUGGESTION_INDICATORS = {
    "should", "could", "would", "wish", "hope", "suggest", "recommend",
    "improve", "better", "consider", "please", "add", "include", "need",
}


def _tokenize(text: str) -> List[str]:
    """Lowercase and split text into alphanumeric tokens."""
    return re.findall(r"[a-z0-9']+", text.lower())


def _keyword_sentiment(tokens: List[str]) -> Dict[str, float]:
    """Compute sentiment score from keyword matching.

    Returns dict with score (-1 to 1), positive_count, negative_count.
    """
    score = 0.0
    pos_count = 0
    neg_count = 0
    i = 0
    while i < len(tokens):
        token = tokens[i]
        multiplier = 1.0

        # Check for preceding intensifier
        if i > 0 and tokens[i - 1] in _INTENSIFIERS:
            multiplier = _INTENSIFIERS[tokens[i - 1]]

        # Check for negation (look back up to 3 tokens)
        negated = False
        for j in range(max(0, i - 3), i):
            if tokens[j] in _NEGATORS:
                negated = True
                break

        if token in _POSITIVE_WORDS:
            if negated:
                score -= 1.0 * multiplier
                neg_count += 1
            else:
                score += 1.0 * multiplier
                pos_count += 1
        elif token in _NEGATIVE_WORDS:
            if negated:
                score += 1.0 * multiplier
                pos_count += 1
            else:
                score -= 1.0 * multiplier
                neg_count += 1
        i += 1

    # Normalize to [-1, 1]
    total = pos_count + neg_count
    if total > 0:
        normalized = score / total
        normalized = max(-1.0, min(1.0, normalized))
    else:
        normalized = 0.0

    return {
        "score": round(normalized, 4),
        "positive_count": pos_count,
        "negative_count": neg_count,
    }


def analyze_sentiment(text: str) -> Dict[str, Any]:
    """Analyze sentiment of a text string.

    Uses VADER if available, otherwise falls back to keyword-based analysis.

    Args:
        text: The text to analyze.

    Returns:
        Dict with score (-1 to 1), label (positive/negative/neutral),
        confidence, and method used.
    """
    if not text or not text.strip():
        return {
            "score": 0.0,
            "label": "neutral",
            "confidence": 0.0,
            "method": "none",
        }

    # Try VADER first
    if HAS_VADER and _vader_analyzer is not None:
        try:
            vader_scores = _vader_analyzer.polarity_scores(text)
            compound = vader_scores["compound"]
            if compound >= 0.05:
                label = "positive"
            elif compound <= -0.05:
                label = "negative"
            else:
                label = "neutral"

            # Confidence based on absolute compound and pos/neg spread
            confidence = round(abs(compound), 4)
            return {
                "score": round(compound, 4),
                "label": label,
                "confidence": confidence,
                "method": "vader",
                "details": {
                    "pos": vader_scores["pos"],
                    "neg": vader_scores["neg"],
                    "neu": vader_scores["neu"],
                },
            }
        except Exception as exc:
            logger.warning("VADER analysis failed, falling back: %s", exc)

    # Keyword-based fallback
    tokens = _tokenize(text)
    kw_result = _keyword_sentiment(tokens)
    score = kw_result["score"]

    if score > 0.1:
        label = "positive"
    elif score < -0.1:
        label = "negative"
    else:
        label = "neutral"

    total = kw_result["positive_count"] + kw_result["negative_count"]
    confidence = round(min(abs(score), 1.0), 4) if total > 0 else 0.0

    return {
        "score": score,
        "label": label,
        "confidence": confidence,
        "method": "keyword",
        "details": {
            "positive_count": kw_result["positive_count"],
            "negative_count": kw_result["negative_count"],
        },
    }


def analyze_review(review_text: str, rating: int = 0) -> Dict[str, Any]:
    """Analyze a product review combining text sentiment and rating.

    Args:
        review_text: The review text.
        rating: Numeric rating (1-5 or 1-10 scale).

    Returns:
        Dict with combined sentiment, text sentiment, rating sentiment,
        and agreement flag.
    """
    text_result = analyze_sentiment(review_text)

    # Normalize rating to [-1, 1]
    rating_score = 0.0
    if rating > 0:
        if rating <= 5:
            # 1-5 scale
            rating_score = (rating - 3) / 2.0
        elif rating <= 10:
            # 1-10 scale
            rating_score = (rating - 5.5) / 4.5
        rating_score = max(-1.0, min(1.0, rating_score))

    # Combined score: weighted average
    if rating > 0:
        combined = 0.6 * text_result["score"] + 0.4 * rating_score
    else:
        combined = text_result["score"]

    combined = round(max(-1.0, min(1.0, combined)), 4)

    if combined > 0.1:
        combined_label = "positive"
    elif combined < -0.1:
        combined_label = "negative"
    else:
        combined_label = "neutral"

    # Check agreement between text and rating
    agreement = True
    if rating > 0:
        text_pos = text_result["score"] > 0.1
        text_neg = text_result["score"] < -0.1
        rating_pos = rating_score > 0.1
        rating_neg = rating_score < -0.1
        if (text_pos and rating_neg) or (text_neg and rating_pos):
            agreement = False

    return {
        "combined_score": combined,
        "combined_label": combined_label,
        "text_sentiment": text_result,
        "rating_score": round(rating_score, 4),
        "rating_provided": rating > 0,
        "agreement": agreement,
    }


def extract_review_insights(reviews: List[str]) -> Dict[str, Any]:
    """Extract aggregate insights from a list of reviews.

    Identifies common praises, complaints, suggestions, and sentiment distribution.

    Args:
        reviews: List of review text strings.

    Returns:
        Dict with top_keywords, sentiment_distribution, common_praises,
        common_complaints, suggestions, and total_reviews.
    """
    if not reviews:
        return {
            "total_reviews": 0,
            "top_keywords": [],
            "sentiment_distribution": {"positive": 0, "neutral": 0, "negative": 0},
            "common_praises": [],
            "common_complaints": [],
            "suggestions": [],
        }

    all_tokens: List[str] = []
    sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
    praise_counter: Counter = Counter()
    complaint_counter: Counter = Counter()
    suggestion_counter: Counter = Counter()

    for review in reviews:
        tokens = _tokenize(review)
        all_tokens.extend(tokens)

        # Sentiment
        result = analyze_sentiment(review)
        sentiment_counts[result["label"]] += 1

        # Praise/complaint/suggestion extraction
        token_set = set(tokens)
        for token in token_set:
            if token in _PRAISE_INDICATORS:
                praise_counter[token] += 1
            if token in _COMPLAINT_INDICATORS:
                complaint_counter[token] += 1
            if token in _SUGGESTION_INDICATORS:
                suggestion_counter[token] += 1

    # Top keywords (excluding stop words)
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "shall", "can", "need", "dare", "ought",
        "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
        "as", "into", "through", "during", "before", "after", "above", "below",
        "between", "out", "off", "over", "under", "again", "further", "then",
        "once", "here", "there", "when", "where", "why", "how", "all", "both",
        "each", "few", "more", "most", "other", "some", "such", "no", "nor",
        "not", "only", "own", "same", "so", "than", "too", "very", "just",
        "because", "but", "and", "or", "if", "while", "about", "up", "it",
        "its", "i", "me", "my", "we", "our", "you", "your", "he", "she",
        "they", "them", "his", "her", "this", "that", "these", "those",
    }
    filtered_tokens = [t for t in all_tokens if t not in stop_words and len(t) > 2]
    keyword_counter = Counter(filtered_tokens)

    total = len(reviews)
    sentiment_distribution = {
        "positive": round(sentiment_counts["positive"] / total, 4),
        "neutral": round(sentiment_counts["neutral"] / total, 4),
        "negative": round(sentiment_counts["negative"] / total, 4),
    }

    return {
        "total_reviews": total,
        "top_keywords": [
            {"keyword": kw, "count": cnt}
            for kw, cnt in keyword_counter.most_common(15)
        ],
        "sentiment_distribution": sentiment_distribution,
        "common_praises": [
            {"keyword": kw, "count": cnt}
            for kw, cnt in praise_counter.most_common(10)
        ],
        "common_complaints": [
            {"keyword": kw, "count": cnt}
            for kw, cnt in complaint_counter.most_common(10)
        ],
        "suggestions": [
            {"keyword": kw, "count": cnt}
            for kw, cnt in suggestion_counter.most_common(10)
        ],
    }
