"""Overwrite all null-byte router files with real implementations."""
import os, sys

BACKEND = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"
sys.path.insert(0, BACKEND)
ROUTER_DIR = os.path.join(BACKEND, "routers")

def is_null(path):
    if not os.path.exists(path): return True
    with open(path, "rb") as f:
        data = f.read(20)
    return len(data) == 0 or all(b == 0 for b in data)

def write(name, content):
    path = os.path.join(ROUTER_DIR, f"{name}.py")
    if is_null(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  Written: {name}.py")
    else:
        print(f"  Skipped (has content): {name}.py")


write("cart", '''"""Cart router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import CartItem, Product, User
from db.schemas import CartItemCreate, CartOut, CartItemOut, ProductListOut
from utils.dependencies import get_current_user
from decimal import Decimal

router = APIRouter()

@router.get("")
def get_cart(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.query(CartItem).filter(CartItem.user_id == current_user.id).all()
    subtotal = sum((i.product.price * i.quantity) for i in items if i.product)
    return {"items": items, "subtotal": float(subtotal), "item_count": len(items)}

@router.post("/items")
def add_to_cart(payload: CartItemCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == payload.product_id, Product.is_active == True).first()
    if not product: raise HTTPException(404, "Product not found")
    existing = db.query(CartItem).filter(CartItem.user_id == current_user.id, CartItem.product_id == payload.product_id, CartItem.variant_id == payload.variant_id).first()
    if existing:
        existing.quantity += payload.quantity
    else:
        db.add(CartItem(user_id=current_user.id, **payload.model_dump()))
    db.commit()
    return {"message": "Added to cart"}

@router.put("/items/{item_id}")
def update_cart_item(item_id: int, quantity: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.user_id == current_user.id).first()
    if not item: raise HTTPException(404, "Item not found")
    if quantity <= 0:
        db.delete(item)
    else:
        item.quantity = quantity
    db.commit()
    return {"message": "Updated"}

@router.delete("/items/{item_id}")
def remove_from_cart(item_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.user_id == current_user.id).first()
    if not item: raise HTTPException(404, "Item not found")
    db.delete(item); db.commit()
    return {"message": "Removed"}

@router.delete("")
def clear_cart(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(CartItem).filter(CartItem.user_id == current_user.id).delete()
    db.commit()
    return {"message": "Cart cleared"}
''')

write("orders", '''"""Orders router."""
from __future__ import annotations
import math, random, string
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import Order, OrderItem, Product, CartItem, Coupon, User
from db.schemas import OrderCreate, OrderOut, OrderStatusUpdate
from utils.dependencies import get_current_user, require_admin
from utils.datetime_utils import utcnow
from decimal import Decimal

router = APIRouter()

def _gen_order_number():
    return "ORD-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

@router.get("")
def list_orders(page: int = Query(1, ge=1), size: int = Query(20), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(Order)
    if current_user.role == "customer":
        q = q.filter(Order.customer_id == current_user.id)
    total = q.count()
    items = q.order_by(Order.created_at.desc()).offset((page-1)*size).limit(size).all()
    return {"items": items, "total": total, "page": page, "pages": math.ceil(total/size) if total else 1}

@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    o = db.query(Order).filter(Order.id == order_id).first()
    if not o: raise HTTPException(404, "Order not found")
    if current_user.role == "customer" and o.customer_id != current_user.id:
        raise HTTPException(403, "Not your order")
    return o

@router.post("", response_model=OrderOut, status_code=201)
def create_order(payload: OrderCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    subtotal = Decimal("0")
    order_items = []
    for ci in payload.items:
        p = db.query(Product).filter(Product.id == ci.product_id, Product.is_active == True).first()
        if not p: raise HTTPException(400, f"Product {ci.product_id} not available")
        line = ci.quantity * p.price
        subtotal += line
        order_items.append(OrderItem(product_id=p.id, product_name=p.name, product_image=p.image_url, quantity=ci.quantity, unit_price=p.price, total_price=line))
    discount = Decimal("0")
    coupon_id = None
    if payload.coupon_code:
        coupon = db.query(Coupon).filter(Coupon.code == payload.coupon_code, Coupon.is_active == True).first()
        if coupon:
            if coupon.discount_type == "percentage":
                discount = subtotal * coupon.discount_value / 100
            else:
                discount = coupon.discount_value
            if coupon.maximum_discount:
                discount = min(discount, coupon.maximum_discount)
            coupon.usage_count += 1
            coupon_id = coupon.id
    total = subtotal - discount
    order = Order(
        order_number=_gen_order_number(),
        customer_id=current_user.id,
        status="pending",
        payment_method=payload.payment_method,
        shipping_address=payload.shipping_address,
        billing_address=payload.billing_address,
        subtotal=subtotal, discount_amount=discount, total=total,
        coupon_code=payload.coupon_code, coupon_id=coupon_id, notes=payload.notes,
    )
    db.add(order); db.flush()
    for item in order_items:
        item.order_id = order.id
        db.add(item)
    db.query(CartItem).filter(CartItem.user_id == current_user.id).delete()
    db.commit(); db.refresh(order)
    return order

@router.put("/{order_id}/status")
def update_order_status(order_id: int, payload: OrderStatusUpdate, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    o = db.query(Order).filter(Order.id == order_id).first()
    if not o: raise HTTPException(404, "Not found")
    o.status = payload.status
    db.commit()
    return {"message": "Status updated"}

@router.post("/{order_id}/cancel")
def cancel_order(order_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    o = db.query(Order).filter(Order.id == order_id).first()
    if not o: raise HTTPException(404, "Not found")
    if current_user.role == "customer" and o.customer_id != current_user.id:
        raise HTTPException(403, "Not your order")
    if o.status not in ("pending", "confirmed"):
        raise HTTPException(400, "Cannot cancel order in current status")
    o.status = "cancelled"; o.cancelled_at = utcnow()
    db.commit()
    return {"message": "Order cancelled"}
''')

write("payments", '''"""Payments router — Stripe integration."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import Order, Payment, User
from db.schemas import PaymentIntentCreate, PaymentIntentOut
from utils.dependencies import get_current_user
from utils.config import settings

router = APIRouter()

@router.post("/create-intent", response_model=PaymentIntentOut)
def create_payment_intent(payload: PaymentIntentCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == payload.order_id).first()
    if not order: raise HTTPException(404, "Order not found")
    if order.customer_id != current_user.id: raise HTTPException(403, "Not your order")
    try:
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        intent = stripe.PaymentIntent.create(
            amount=int(order.total * 100),
            currency=payload.currency.lower(),
            metadata={"order_id": order.id, "order_number": order.order_number},
        )
        order.payment_intent_id = intent.id
        order.payment_provider = "stripe"
        db.commit()
        return PaymentIntentOut(client_secret=intent.client_secret, payment_intent_id=intent.id, amount=intent.amount, currency=intent.currency)
    except Exception as e:
        raise HTTPException(500, f"Payment error: {e}")

@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    try:
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        event = stripe.Webhook.construct_event(payload, sig, settings.STRIPE_WEBHOOK_SECRET)
    except Exception:
        raise HTTPException(400, "Invalid webhook")
    if event["type"] == "payment_intent.succeeded":
        pi = event["data"]["object"]
        order = db.query(Order).filter(Order.payment_intent_id == pi["id"]).first()
        if order:
            order.payment_status = "paid"
            order.status = "confirmed"
            db.add(Payment(order_id=order.id, amount=order.total, provider="stripe", provider_reference=pi["id"], status="succeeded"))
            db.commit()
    return {"received": True}
''')

write("reviews", '''"""Reviews router."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import Review, User
from db.schemas import ReviewCreate, ReviewOut
from utils.dependencies import get_current_user

router = APIRouter()

@router.get("", response_model=list[ReviewOut])
def list_reviews(product_id: int = Query(...), db: Session = Depends(get_db)):
    return db.query(Review).filter(Review.product_id == product_id, Review.is_approved == True).all()

@router.post("", response_model=ReviewOut, status_code=201)
def create_review(payload: ReviewCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing = db.query(Review).filter(Review.product_id == payload.product_id, Review.user_id == current_user.id).first()
    if existing: raise HTTPException(400, "Already reviewed")
    review = Review(user_id=current_user.id, **payload.model_dump())
    db.add(review); db.commit(); db.refresh(review)
    return review

@router.delete("/{review_id}")
def delete_review(review_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review: raise HTTPException(404, "Not found")
    if review.user_id != current_user.id and current_user.role != "admin": raise HTTPException(403)
    db.delete(review); db.commit()
    return {"message": "Deleted"}
''')

write("wishlist", '''"""Wishlist router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import WishlistItem, Product, User
from utils.dependencies import get_current_user

router = APIRouter()

@router.get("")
def get_wishlist(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(WishlistItem).filter(WishlistItem.user_id == current_user.id).all()

@router.post("/{product_id}", status_code=201)
def add_to_wishlist(product_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not db.query(Product).filter(Product.id == product_id).first(): raise HTTPException(404)
    if db.query(WishlistItem).filter(WishlistItem.user_id == current_user.id, WishlistItem.product_id == product_id).first():
        return {"message": "Already in wishlist"}
    db.add(WishlistItem(user_id=current_user.id, product_id=product_id))
    db.commit()
    return {"message": "Added"}

@router.delete("/{product_id}")
def remove_from_wishlist(product_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(WishlistItem).filter(WishlistItem.user_id == current_user.id, WishlistItem.product_id == product_id).first()
    if not item: raise HTTPException(404)
    db.delete(item); db.commit()
    return {"message": "Removed"}
''')

write("addresses", '''"""Addresses router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import Address, User
from db.schemas import AddressCreate, AddressOut
from utils.dependencies import get_current_user

router = APIRouter()

@router.get("", response_model=list[AddressOut])
def list_addresses(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Address).filter(Address.user_id == current_user.id).all()

@router.post("", response_model=AddressOut, status_code=201)
def create_address(payload: AddressCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.is_default:
        db.query(Address).filter(Address.user_id == current_user.id).update({"is_default": False})
    addr = Address(user_id=current_user.id, **payload.model_dump())
    db.add(addr); db.commit(); db.refresh(addr)
    return addr

@router.put("/{address_id}", response_model=AddressOut)
def update_address(address_id: int, payload: AddressCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    a = db.query(Address).filter(Address.id == address_id, Address.user_id == current_user.id).first()
    if not a: raise HTTPException(404)
    for k, v in payload.model_dump().items(): setattr(a, k, v)
    db.commit(); db.refresh(a)
    return a

@router.delete("/{address_id}")
def delete_address(address_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    a = db.query(Address).filter(Address.id == address_id, Address.user_id == current_user.id).first()
    if not a: raise HTTPException(404)
    db.delete(a); db.commit()
    return {"message": "Deleted"}
''')

write("notifications", '''"""Notifications router."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import Notification, User
from db.schemas import NotificationOut
from utils.dependencies import get_current_user

router = APIRouter()

@router.get("", response_model=list[NotificationOut])
def list_notifications(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Notification).filter(Notification.user_id == current_user.id).order_by(Notification.created_at.desc()).limit(50).all()

@router.post("/{notification_id}/read")
def mark_read(notification_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    n = db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == current_user.id).first()
    if n: n.is_read = True; db.commit()
    return {"message": "Marked as read"}

@router.post("/read-all")
def mark_all_read(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(Notification).filter(Notification.user_id == current_user.id, Notification.is_read == False).update({"is_read": True})
    db.commit()
    return {"message": "All marked as read"}
''')

write("coupons", '''"""Coupons router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import Coupon, User
from db.schemas import CouponCreate, CouponOut, CouponValidateRequest, CouponValidateResponse
from utils.dependencies import get_current_user, require_admin
from utils.datetime_utils import utcnow
from decimal import Decimal

router = APIRouter()

@router.post("/validate", response_model=CouponValidateResponse)
def validate_coupon(payload: CouponValidateRequest, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    coupon = db.query(Coupon).filter(Coupon.code == payload.code, Coupon.is_active == True).first()
    if not coupon: return CouponValidateResponse(valid=False, discount_amount=Decimal("0"), message="Coupon not found")
    now = utcnow()
    if coupon.expires_at and coupon.expires_at < now: return CouponValidateResponse(valid=False, discount_amount=Decimal("0"), message="Coupon expired")
    if coupon.usage_limit and coupon.usage_count >= coupon.usage_limit: return CouponValidateResponse(valid=False, discount_amount=Decimal("0"), message="Usage limit reached")
    if payload.order_total < coupon.minimum_order: return CouponValidateResponse(valid=False, discount_amount=Decimal("0"), message=f"Minimum order {coupon.minimum_order}")
    discount = payload.order_total * coupon.discount_value / 100 if coupon.discount_type == "percentage" else coupon.discount_value
    if coupon.maximum_discount: discount = min(discount, coupon.maximum_discount)
    return CouponValidateResponse(valid=True, discount_amount=discount, coupon=coupon)

@router.get("", response_model=list[CouponOut])
def list_coupons(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(Coupon).all()

@router.post("", response_model=CouponOut, status_code=201)
def create_coupon(payload: CouponCreate, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    c = Coupon(**payload.model_dump())
    db.add(c); db.commit(); db.refresh(c)
    return c

@router.delete("/{coupon_id}")
def delete_coupon(coupon_id: int, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    c = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not c: raise HTTPException(404)
    db.delete(c); db.commit()
    return {"message": "Deleted"}
''')

write("banners", '''"""Banners router."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from db.database import get_db
from db.models import Banner, User
from db.schemas import BannerCreate, BannerOut
from utils.dependencies import require_admin

router = APIRouter()

@router.get("", response_model=list[BannerOut])
def list_banners(position: Optional[str] = Query(None), db: Session = Depends(get_db)):
    q = db.query(Banner).filter(Banner.is_active == True)
    if position: q = q.filter(Banner.position == position)
    return q.order_by(Banner.sort_order).all()

@router.post("", response_model=BannerOut, status_code=201)
def create_banner(payload: BannerCreate, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    b = Banner(**payload.model_dump())
    db.add(b); db.commit(); db.refresh(b)
    return b

@router.put("/{banner_id}", response_model=BannerOut)
def update_banner(banner_id: int, payload: BannerCreate, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    b = db.query(Banner).filter(Banner.id == banner_id).first()
    if not b: raise HTTPException(404)
    for k, v in payload.model_dump().items(): setattr(b, k, v)
    db.commit(); db.refresh(b)
    return b

@router.delete("/{banner_id}")
def delete_banner(banner_id: int, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    b = db.query(Banner).filter(Banner.id == banner_id).first()
    if not b: raise HTTPException(404)
    db.delete(b); db.commit()
    return {"message": "Deleted"}
''')

write("tickets", '''"""Support tickets router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import SupportTicket, TicketMessage, User
from db.schemas import TicketCreate, TicketMessageCreate, TicketOut
from utils.dependencies import get_current_user, require_staff

router = APIRouter()

@router.get("", response_model=list[TicketOut])
def list_tickets(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(SupportTicket)
    if current_user.role == "customer": q = q.filter(SupportTicket.user_id == current_user.id)
    return q.order_by(SupportTicket.created_at.desc()).all()

@router.post("", response_model=TicketOut, status_code=201)
def create_ticket(payload: TicketCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ticket = SupportTicket(user_id=current_user.id, **payload.model_dump())
    db.add(ticket); db.commit(); db.refresh(ticket)
    return ticket

@router.post("/{ticket_id}/messages", status_code=201)
def add_message(ticket_id: int, payload: TicketMessageCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket: raise HTTPException(404)
    msg = TicketMessage(ticket_id=ticket_id, sender_id=current_user.id, **payload.model_dump())
    db.add(msg); db.commit(); db.refresh(msg)
    return msg
''')

write("returns", '''"""Returns router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import ReturnRequest, Order, User
from db.schemas import ReturnRequestCreate, ReturnRequestOut
from utils.dependencies import get_current_user, require_admin

router = APIRouter()

@router.get("", response_model=list[ReturnRequestOut])
def list_returns(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(ReturnRequest)
    if current_user.role == "customer": q = q.filter(ReturnRequest.customer_id == current_user.id)
    return q.order_by(ReturnRequest.created_at.desc()).all()

@router.post("", response_model=ReturnRequestOut, status_code=201)
def create_return(payload: ReturnRequestCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == payload.order_id, Order.customer_id == current_user.id).first()
    if not order: raise HTTPException(403, "Order not found or not yours")
    if order.status not in ("delivered",): raise HTTPException(400, "Order not eligible for return")
    req = ReturnRequest(customer_id=current_user.id, **payload.model_dump())
    db.add(req); db.commit(); db.refresh(req)
    return req

@router.put("/{return_id}/status")
def update_return_status(return_id: int, status: str, notes: str = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    r = db.query(ReturnRequest).filter(ReturnRequest.id == return_id).first()
    if not r: raise HTTPException(404)
    r.status = status
    if notes: r.resolution_notes = notes
    db.commit()
    return {"message": "Updated"}
''')

write("search", '''"""Search router."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session
from typing import Optional
from db.database import get_db
from db.models import Product

router = APIRouter()

@router.get("")
def search(q: str = Query(..., min_length=1), limit: int = 20, db: Session = Depends(get_db)):
    products = db.query(Product).filter(
        Product.is_active == True,
        or_(Product.name.ilike(f"%{q}%"), Product.description.ilike(f"%{q}%"), Product.category.ilike(f"%{q}%"))
    ).limit(limit).all()
    return products
''')

write("chatbot", '''"""Chatbot router — AI product assistant."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import Product, User
from utils.dependencies import get_current_user
from typing import Optional

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

@router.post("")
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    products = db.query(Product).filter(Product.is_active == True, Product.name.ilike(f"%{payload.message}%")).limit(5).all()
    if products:
        suggestions = [{"id": p.id, "name": p.name, "price": float(p.price), "image": p.image_url} for p in products]
        return {"response": f"I found {len(products)} matching products!", "products": suggestions}
    return {"response": "I could not find specific products, but feel free to browse our catalog!", "products": []}
''')

write("logistics_partner", '''"""Logistics partner profile router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import LogisticsPartnerProfile, User
from db.schemas import LogisticsPartnerProfileCreate, LogisticsPartnerProfileOut
from utils.dependencies import get_current_user, require_logistics

router = APIRouter()

@router.get("/profile", response_model=LogisticsPartnerProfileOut)
def get_profile(current_user: User = Depends(require_logistics), db: Session = Depends(get_db)):
    p = db.query(LogisticsPartnerProfile).filter(LogisticsPartnerProfile.user_id == current_user.id).first()
    if not p: raise HTTPException(404)
    return p

@router.post("/profile", response_model=LogisticsPartnerProfileOut, status_code=201)
def create_profile(payload: LogisticsPartnerProfileCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if db.query(LogisticsPartnerProfile).filter(LogisticsPartnerProfile.user_id == current_user.id).first():
        raise HTTPException(400, "Profile already exists")
    p = LogisticsPartnerProfile(user_id=current_user.id, **payload.model_dump())
    db.add(p); db.commit(); db.refresh(p)
    current_user.role = "logistics_partner"; db.commit()
    return p
''')

print("All done.")
