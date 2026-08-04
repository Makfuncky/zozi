import re
from difflib import SequenceMatcher, get_close_matches
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func, or_, text, case
from sqlalchemy.orm import Session

from data.models import Product

# Hard limits to prevent OOM under heavy traffic.
_MAX_PAGE_SIZE = 100
_MAX_FUZZY_PRODUCTS = 5000


class AdvancedSearchEngine:
    def __init__(self, db: Session):
        self.db = db
        self._is_postgres = self.db.bind.dialect.name == "postgresql"

    def parse_query(self, query: str) -> Dict[str, Any]:
        parsed: Dict[str, Any] = {
            "q": query,
            "terms": [],
            "min_price": None,
            "max_price": None,
            "category": None,
            "brand": None,
            "brands": None,
            "size": None,
            "color": None,
            "min_rating": None,
            "max_rating": None,
            "sort": None,
            "has_video": False,
        }

        q_lower = query.lower()

        price_patterns = [
            (r"\bunder\s+\$?(\d+(?:\.\d+)?)", "max_price"),
            (r"\bbelow\s+\$?(\d+(?:\.\d+)?)", "max_price"),
            (r"\bless\s+than\s+\$?(\d+(?:\.\d+)?)", "max_price"),
            (r"\babove\s+\$?(\d+(?:\.\d+)?)", "min_price"),
            (r"\bover\s+\$?(\d+(?:\.\d+)?)", "min_price"),
            (r"\bbetween\s+\$?(\d+(?:\.\d+)?)\s+and\s+\$?(\d+(?:\.\d+)?)", "range_price"),
        ]

        for pattern, field in price_patterns:
            match = re.search(pattern, q_lower)
            if match:
                if field == "range_price":
                    parsed["min_price"] = float(match.group(1))
                    parsed["max_price"] = float(match.group(2))
                elif field == "max_price":
                    parsed["max_price"] = float(match.group(1))
                elif field == "min_price":
                    parsed["min_price"] = float(match.group(1))
                query = re.sub(pattern, "", query, flags=re.IGNORECASE)
                break

        rating_match = re.search(r"(\d)\+\s*star", q_lower)
        if rating_match:
            parsed["min_rating"] = int(rating_match.group(1))
            query = re.sub(r"(\d)\+\s*star", "", query, flags=re.IGNORECASE)

        brands = ["nike", "adidas", "apple", "samsung", "sony", "lg", "hp", "dell", "canon", "nikon"]
        found_brands = [b.capitalize() for b in brands if b in q_lower]
        if found_brands:
            parsed["brands"] = found_brands
            for b in brands:
                query = re.sub(rf"\b{b}\b", "", query, flags=re.IGNORECASE)

        if "video" in q_lower or "with video" in q_lower:
            parsed["has_video"] = True
            query = re.sub(r"\bvideo\b", "", query, flags=re.IGNORECASE)

        if "in stock" in q_lower or "available" in q_lower:
            query = re.sub(r"\b(in\s+stock|available)\b", "", query, flags=re.IGNORECASE)

        if re.search(r"\bnew(est)?\b", q_lower):
            parsed["sort"] = "newest"
            query = re.sub(r"\bnew(est)?\b", "", query, flags=re.IGNORECASE)
        elif re.search(r"\b(top|rated|reviewed)\b", q_lower):
            parsed["sort"] = "rating"
            query = re.sub(r"\b(top|rated|reviewed)\b", "", query, flags=re.IGNORECASE)
        elif re.search(r"\b(cheap\w*|low(\s*price)?)\b", q_lower):
            parsed["sort"] = "price_asc"
            query = re.sub(r"\b(cheapest|cheap|low\s*price)\b", "", query, flags=re.IGNORECASE)
        elif re.search(r"\bexpensive\b", q_lower):
            parsed["sort"] = "price_desc"
            query = re.sub(r"\b(expens|high\s*end)\b", "", query, flags=re.IGNORECASE)

        stop_words = {"a", "an", "and", "for", "the", "is", "are", "to", "of", "in", "on", "with", "by", "at", "from", "it", "this", "that", "these", "those"}
        terms = [t for t in re.findall(r"[a-z]{2,}", query.lower()) if t not in stop_words]
        parsed["terms"] = list(dict.fromkeys(terms))
        parsed["q"] = " ".join(parsed["terms"])

        return parsed

    def expand_query(self, query: str) -> List[str]:
        synonyms = {
            "shoe": ["footwear", "sneaker", "boot"],
            "dress": ["gown", "outfit", "gown"],
            "phone": ["smartphone", "mobile", "cell"],
            "laptop": ["computer", "notebook", "pc"],
            "watch": ["timepiece", "wristwatch"],
            "headphone": ["headset", "earphone", "earbuds"],
            "camera": ["photography", "digital camera"],
            "book": ["novel", "publication", "textbook"],
            "toy": ["game", "plaything", "childhood"],
        }

        expanded = [query]
        words = query.lower().split()

        for word in words:
            if word in synonyms:
                for syn in synonyms[word]:
                    expanded.append(query.lower().replace(word, syn))

        return list(set(expanded))

    def _apply_text_search(self, db_query, search_term: str):
        if not search_term:
            return db_query

        like_pattern = f"%{search_term}%"

        if self._is_postgres:
            tsquery = func.plainto_tsquery("english", search_term)
            tsvector = func.to_tsvector("english", Product.name + " " + func.coalesce(Product.description, ""))
            db_query = db_query.filter(
                or_(
                    tsvector.op("@@")(tsquery),
                    Product.name.ilike(like_pattern),
                    Product.description.ilike(like_pattern),
                    Product.category.ilike(like_pattern),
                    Product.brand.ilike(like_pattern),
                    Product.tags.ilike(like_pattern),
                )
            )
        else:
            db_query = db_query.filter(
                or_(
                    Product.name.ilike(like_pattern),
                    Product.description.ilike(like_pattern),
                    Product.category.ilike(like_pattern),
                    Product.brand.ilike(like_pattern),
                    Product.tags.ilike(like_pattern),
                )
            )
        return db_query

    def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "relevance",
    ) -> Dict[str, Any]:
        limit = min(limit, _MAX_PAGE_SIZE)
        offset = max(offset, 0)

        parsed = self.parse_query(query)
        all_filters = {**(filters or {}), **parsed}

        db_query = self.db.query(Product).filter(
            Product.is_deleted == False,
            Product.is_active == True,
            Product.is_approved == True,
            Product.stock > 0,
        )

        if all_filters.get("min_price") is not None:
            db_query = db_query.filter(Product.price >= float(all_filters["min_price"]))
        if all_filters.get("max_price") is not None:
            db_query = db_query.filter(Product.price <= float(all_filters["max_price"]))
        if all_filters.get("min_rating") is not None:
            db_query = db_query.filter(Product.rating >= float(all_filters["min_rating"]))
        if all_filters.get("max_rating") is not None:
            db_query = db_query.filter(Product.rating <= float(all_filters["max_rating"]))
        if all_filters.get("brands"):
            brands = all_filters["brands"]
            if isinstance(brands, str):
                brands = [b.strip() for b in brands.split(",") if b.strip()]
            if brands:
                db_query = db_query.filter(Product.brand.in_(brands))
        if all_filters.get("category"):
            db_query = db_query.filter(Product.category.ilike(f"%{all_filters['category']}%"))
        if all_filters.get("has_video"):
            db_query = db_query.filter(Product.video_count > 0)

        db_query = self._apply_text_search(db_query, all_filters.get("q"))

        total = db_query.count()

        if sort_by == "price_asc":
            db_query = db_query.order_by(Product.price.asc())
        elif sort_by == "price_desc":
            db_query = db_query.order_by(Product.price.desc())
        elif sort_by == "rating":
            db_query = db_query.order_by(Product.rating.desc(), Product.sales_count.desc())
        elif sort_by == "newest":
            db_query = db_query.order_by(Product.created_at.desc())
        else:
            db_query = db_query.order_by(Product.sales_count.desc(), Product.rating.desc())

        products = db_query.offset(offset).limit(limit).all()

        return {
            "products": [self._serialize_product(p) for p in products],
            "total": total,
            "limit": limit,
            "offset": offset,
            "parsed_query": parsed,
        }

    def _serialize_product(self, product: Product) -> Dict[str, Any]:
        return {
            "id": product.id,
            "name": product.name,
            "price": float(product.price) if product.price else 0,
            "rating": float(product.rating) if product.rating else 0,
            "brand": product.brand,
            "category": product.category,
            "image_url": product.image_url,
            "stock": product.stock,
            "video_count": product.video_count or 0,
        }

    def get_autocomplete_suggestions(self, query: str, limit: int = 10) -> List[str]:
        if not query or len(query) < 2:
            return []

        terms = [t.strip() for t in query.split() if t.strip()]
        if not terms:
            return []

        last_term = terms[-1].lower()
        prefix = f"%{last_term}%"

        suggestions = []

        name_matches = (
            self.db.query(Product.name)
            .filter(Product.name.ilike(prefix), Product.is_active == True, Product.is_deleted == False)
            .limit(limit * 2)
            .all()
        )
        suggestions.extend([m[0] for m in name_matches])

        brand_matches = (
            self.db.query(Product.brand)
            .filter(Product.brand.ilike(prefix), Product.brand.isnot(None))
            .limit(limit * 2)
            .all()
        )
        suggestions.extend([b[0] for b in brand_matches if b[0]])

        if last_term and len(suggestions) > 0:
            fuzzy_matches = get_close_matches(
                last_term,
                [s.lower() for s in suggestions if s],
                n=limit,
                cutoff=0.6
            )
            suggestions = [s for s in suggestions if s.lower() in fuzzy_matches or s.lower().startswith(last_term.lower())]
        elif not last_term:
            suggestions = []

        return list(dict.fromkeys(suggestions))[:limit]

    def _build_word_graph(self) -> Dict[str, List[str]]:
        word_graph: Dict[str, List[str]] = {}

        products = self.db.query(Product.name, Product.description, Product.brand).filter(
            Product.is_active == True,
            Product.is_deleted == False
        ).limit(1000).all()

        for product in products:
            text = f"{(product[0] or '')} {(product[1] or '')} {(product[2] or '')}".lower()
            words = re.findall(r'\b[a-z]{2,}\b', text)
            for i, word in enumerate(words):
                if word not in word_graph:
                    word_graph[word] = []
                for other_word in words[i+1:i+4]:
                    if other_word != word and other_word not in word_graph.get(word, []):
                        word_graph[word].append(other_word)

        return word_graph

    def get_word_predictions(self, query: str, limit: int = 5) -> List[str]:
        if not query or len(query) < 2:
            return []

        words = query.lower().split()
        last_word = words[-1] if words else ""

        if not last_word:
            return []

        suggestions = []

        if len(last_word) >= 2:
            prefix_matches = self._prefix_suggestions(last_word, limit * 3)
            suggestions.extend(prefix_matches)

        word_graph = self._build_word_graph()
        for word in words[:-1]:
            if word in word_graph:
                for related in word_graph[word][:limit]:
                    if related not in suggestions and related != last_word:
                        suggestions.append(related)

        if len(words) >= 2:
            prev_word = words[-2]
            product_names = self._get_product_names()
            for prod_name in product_names[:200]:
                prod_words = prod_name.split()
                for i, pw in enumerate(prod_words[:-1]):
                    if pw == prev_word and i + 1 < len(prod_words):
                        next_word = prod_words[i + 1]
                        if next_word not in suggestions and next_word.startswith(last_word[:2]):
                            suggestions.append(next_word)

        if not suggestions:
            product_names = self._get_product_names()
            for prod_name in product_names[:100]:
                prod_words = prod_name.lower().split()
                for pw in prod_words:
                    if pw.startswith(last_word) and pw not in suggestions:
                        suggestions.append(pw)
                        if len(suggestions) >= limit:
                            break

        suggestions = list(dict.fromkeys(suggestions))[:limit]
        return suggestions

    def _get_product_names(self) -> List[str]:
        products = self.db.query(Product.name).filter(
            Product.is_active == True,
            Product.is_deleted == False
        ).limit(1000).all()
        return [p[0] for p in products if p[0]]

    def _prefix_suggestions(self, prefix: str, limit: int) -> List[str]:
        suggestions = []
        products = self.db.query(Product.name).filter(
            Product.is_active == True,
            Product.is_deleted == False
        ).limit(1000).all()

        for (name,) in products:
            if name:
                words = re.findall(r'\b[a-z]+', name.lower())
                for word in words:
                    if word.startswith(prefix) and word not in suggestions:
                        suggestions.append(word)
                        if len(suggestions) >= limit:
                            return suggestions
        return suggestions

    def fuzzy_search(self, query: str, limit: int = 20, cutoff: float = 0.6) -> Dict[str, Any]:
        limit = min(limit, _MAX_PAGE_SIZE)
        parsed = self.parse_query(query)

        db_query = self.db.query(Product).filter(
            Product.is_deleted == False,
            Product.is_active == True,
            Product.is_approved == True,
            Product.stock > 0,
        )

        if parsed.get("min_price") is not None:
            db_query = db_query.filter(Product.price >= float(parsed["min_price"]))
        if parsed.get("max_price") is not None:
            db_query = db_query.filter(Product.price <= float(parsed["max_price"]))
        if parsed.get("min_rating") is not None:
            db_query = db_query.filter(Product.rating >= float(parsed["min_rating"]))

        # Use DB-level search first to narrow results, then fuzzy-score in-memory
        search_term = parsed.get("q")
        if search_term:
            db_query = self._apply_text_search(db_query, search_term)

        all_products = db_query.limit(_MAX_FUZZY_PRODUCTS).all()
        total = len(all_products)

        query_words = query.lower().split()
        scored_products = []

        for product in all_products:
            product_text = f"{(product.name or '')} {(product.brand or '')} {(product.category or '')}".lower()
            product_words = product_text.split()

            max_word_similarity = 0.0
            matched_words = 0

            for qw in query_words:
                word_scores = [SequenceMatcher(None, qw, pw).ratio() for pw in product_words]
                if word_scores:
                    best_score = max(word_scores)
                    max_word_similarity = max(max_word_similarity, best_score)
                    if best_score >= cutoff:
                        matched_words += 1

            overall_similarity = max_word_similarity

            if len(query_words) > 0:
                word_coverage = matched_words / len(query_words)
                overall_similarity = 0.7 * overall_similarity + 0.3 * word_coverage

            if overall_similarity >= cutoff - 0.1:
                scored_products.append((overall_similarity, product))

        scored_products.sort(key=lambda x: (-x[0], -(x[1].rating or 0), -(x[1].sales_count or 0)))

        top_products = scored_products[:limit]

        return {
            "products": [self._serialize_product(p) for s, p in top_products],
            "total": total,
            "limit": limit,
            "offset": 0,
            "parsed_query": parsed,
            "fuzzy_applied": cutoff < 1.0,
            "similarity_scores": [round(s, 2) for s, p in top_products],
        }
