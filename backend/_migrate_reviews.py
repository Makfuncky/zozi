from __future__ import annotations
import io

p = "controllers/commerce/reviews_controller.py"
raw = open(p, "rb").read()
text = raw.decode("utf-8")
if text.startswith("\ufeff"):
    text = text[1:]
crlf = b"\r\n" in raw
text = text.replace("\r\n", "\n")

def put(s):
    return s.replace("\n", "\r\n") if crlf else s

# 1) imports
text = text.replace(
    "from data.db_schemas import ReviewCreate\n",
    "from data.db_schemas import ReviewCreate, ReviewOut\n",
    1,
)
text = text.replace(
    "from sqlalchemy.orm import Session\n\nfrom services.commerce.reviews_service import (\n",
    "from sqlalchemy.orm import Session\n\n"
    "from routers.generated.auto_router import delete, get, post, put\n\n"
    "from services.commerce.reviews_service import (\n",
    1,
)

# 2) decorate get_product_reviews  (add limit default 50 to preserve router default)
old_gpr = (
    "def get_product_reviews(\n"
    "    product_id: int, limit: int, cursor: Optional[int], db: Session\n"
    ") -> List[dict]:\n"
)
new_gpr = (
    '@get("/api/v1/products/{product_id}", deps=["db"], query=["limit", "cursor"], '
    "response_model=List[ReviewOut], tags=[\"reviews\"])\n"
    "def get_product_reviews(\n"
    "    product_id: int, limit: int = 50, cursor: Optional[int] = None, db: Session\n"
    ") -> List[dict]:\n"
)
assert old_gpr in text, "get_product_reviews anchor not found"
text = text.replace(old_gpr, new_gpr, 1)

# add list_reviews right after get_product_reviews body (before get_review)
list_reviews = (
    "\n"
    '@get("/api/v1", deps=["db"], query=["product_id", "limit", "cursor"], '
    "response_model=List[ReviewOut], tags=[\"reviews\"])\n"
    "def list_reviews(\n"
    "    product_id: int, limit: int = 50, cursor: Optional[int] = None, db: Session\n"
    ") -> List[dict]:\n"
    "    return get_product_reviews(product_id, limit=limit, cursor=cursor, db=db)\n"
)
anchor_review = (
    "def get_review(review_id: int, db: Session) -> dict:\n"
)
assert anchor_review in text, "get_review anchor not found"
text = text.replace(anchor_review, list_reviews + anchor_review, 1)

# 3) decorate get_review
text = text.replace(
    "def get_review(review_id: int, db: Session) -> dict:\n",
    '@get("/api/v1/{review_id}", deps=["db"], response_model=ReviewOut, tags=["reviews"])\n'
    "def get_review(review_id: int, db: Session) -> dict:\n",
    1,
)

# 4) decorate create_review
text = text.replace(
    "def create_review(product_id: int, review: ReviewCreate, current_user, db: Session) -> dict:\n",
    '@post("/api/v1/products/{product_id}", deps=["db", "user"], body=ReviewCreate, '
    "response_model=ReviewOut, status_code=201, tags=[\"reviews\"])\n"
    "def create_review(product_id: int, review: ReviewCreate, current_user, db: Session) -> dict:\n",
    1,
)

# 5) decorate update_review
text = text.replace(
    "def update_review(review_id: int, review: ReviewCreate, current_user, db: Session) -> dict:\n",
    '@put("/api/v1/{review_id}", deps=["db", "user"], body=ReviewCreate, '
    "response_model=ReviewOut, tags=[\"reviews\"])\n"
    "def update_review(review_id: int, review: ReviewCreate, current_user, db: Session) -> dict:\n",
    1,
)

# 6) decorate delete_review
text = text.replace(
    "def delete_review(review_id: int, current_user, db: Session) -> dict:\n",
    '@delete("/api/v1/{review_id}", deps=["db", "user"], response_model=ReviewOut, tags=["reviews"])\n'
    "def delete_review(review_id: int, current_user, db: Session) -> dict:\n",
    1,
)

out = put(text)
open(p, "wb").write(out.encode("utf-8"))
print("updated", p)
