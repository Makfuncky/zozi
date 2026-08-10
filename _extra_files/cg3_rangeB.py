def compute_credibility_score(supplier_id: int, db: Session) -> int:
    """
    Compute a 0-100 credibility score based on:
      - Order fulfilment rate        (max 35 pts)
      - Average product review score (max 25 pts)
      - Document verification status (max 20 pts)
      - Account age in days          (max 10 pts)
      - Number of approved products  (max 10 pts)
    """
    from models import SupplierProfile as SP, Product, Order, OrderItem, Review

    # 1. Fulfilment rate
    total_orders = (
        db.query(func.count(func.distinct(Order.id)))
        .join(OrderItem)
        .join(Product)
        .filter(Product.supplier_id == supplier_id)
        .scalar()
    ) or 0
    fulfilled_orders = (
        db.query(func.count(func.distinct(Order.id)))
        .join(OrderItem)
        .join(Product)
        .filter(
            Product.supplier_id == supplier_id,
            Order.status.in_(["completed", "delivered", "shipped"]),
        )
        .scalar()
    ) or 0
    fulfilment_rate = (fulfilled_orders / total_orders) if total_orders > 0 else 0
    pts_fulfilment = round(fulfilment_rate * 35)

    # 2. Average review
    avg_review = (
        db.query(func.avg(Review.rating))
        .join(Product, Review.product_id == Product.id)
        .filter(Product.supplier_id == supplier_id)
        .scalar()
    ) or 0
    pts_review = round((float(avg_review) / 5.0) * 25)

    # 3. Document verification
    profile = db.query(SP).filter(SP.user_id == supplier_id).first()
    docs = {}
    if profile and profile.verified_documents:
        try:
            docs = json.loads(profile.verified_documents)
        except Exception:
            docs = {}
    pts_docs = 0
    if profile and profile.verification_status in ("approved", "verified"):
        pts_docs = 20
    elif docs:
        pts_docs = min(15, len(docs) * 5)

    # 4. Account age
    user = db.query(User).filter(User.id == supplier_id).first()
    age_days = 0
    if user and user.created_at:
        age_days = max(0, (utcnow() - user.created_at).days)
    pts_age = min(10, age_days // 30)  # 1pt per month, max 10

    # 5. Approved products
    approved_count = (
        db.query(func.count(Product.id))
        .filter(
            Product.supplier_id == supplier_id,
            Product.is_approved == True,  # noqa: E712
            Product.is_deleted == False,  # noqa: E712
        )
        .scalar()
    ) or 0
    pts_products = min(10, approved_count)

    return int(pts_fulfilment + pts_review + pts_docs + pts_age + pts_products)


