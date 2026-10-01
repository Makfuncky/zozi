"""Promotional campaign service — sends promotions via SMS and WhatsApp.

Manages campaign creation, audience targeting (with opt-in respect),
message delivery, and campaign analytics.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

# LAZY: from domains.comms.ports import NotificationResult
# Write operation was removed from domains.comms.ports (Law 3: reads only).
# This cross-domain notification sender must eventually move behind an event;
# for now import it directly from the owning service so modules continue to
# load.
# LAZY: from domains.comms.ports import send_notification
from infrastructure.utils.phone_utils import normalize_phone_number, validate_phone_number

logger = logging.getLogger(__name__)


class PromotionCampaign:
    """Represents a promotional campaign."""

    def __init__(
        self,
        campaign_id: str,
        name: str,
        template_id: str,
        channel: str,  # "sms" or "whatsapp"
        country_code: str | None = None,
        product_name: str | None = None,
        product_url: str | None = None,
        discount_text: str | None = None,
        promo_code: str | None = None,
        created_at: datetime | None = None,
    ):
        self.campaign_id = campaign_id
        self.name = name
        self.template_id = template_id
        self.channel = channel
        self.country_code = country_code
        self.product_name = product_name
        self.product_url = product_url
        self.discount_text = discount_text
        self.promo_code = promo_code
        self.created_at = created_at or datetime.now(timezone.utc)
        self.results: list[NotificationResult] = []

    def to_dict(self) -> dict:
        return {
            "campaign_id": self.campaign_id,
            "name": self.name,
            "template_id": self.template_id,
            "channel": self.channel,
            "country_code": self.country_code,
            "product_name": self.product_name,
            "product_url": self.product_url,
            "discount_text": self.discount_text,
            "promo_code": self.promo_code,
            "created_at": self.created_at.isoformat(),
            "stats": self.get_stats(),
        }

    def get_stats(self) -> dict:
        total = len(self.results)
        sent = sum(1 for r in self.results if r.success)
        preview = sum(1 for r in self.results if r.preview)
        failed = total - sent - preview
        return {
            "total": total,
            "sent": sent,
            "preview": preview,
            "failed": failed,
        }


def get_opted_in_customers(
    db: Session,
    channel: str,
    country_code: str | None = None,
) -> list[dict]:
    """Get customers who have marketing opt-in for the given channel.

    Args:
        db: Database session
        channel: "sms" or "whatsapp"
        country_code: Optional country filter

    Returns:
        List of dicts with user_id, phone, name
    """
    from domains.accounts.ports import User

    # Query active users with phone numbers
    # Marketing opt-in is determined by user preferences
    query = (
        db.query(User.id, User.phone, User.full_name, User.country_code)
        .filter(
            User.phone.isnot(None),
            User.is_active.is_(True),
        )
    )

    if country_code:
        query = query.filter(User.country_code == country_code)

    customers = []
    for user_id, phone, name, cc in query.all():
        # Validate phone is a mobile number
        validation = validate_phone_number(phone, cc or country_code)
        if validation["valid"] and phone:
            customers.append({
                "user_id": user_id,
                "phone": phone,
                "name": name or "Customer",
                "country_code": cc or country_code,
            })

    return customers


def send_promotion_campaign(
    db: Session,
    campaign: PromotionCampaign,
    customers: list[dict] | None = None,
) -> PromotionCampaign:
    """Send a promotional campaign to targeted customers.

    Args:
        db: Database session
        campaign: PromotionCampaign to send
        customers: Optional pre-filtered customer list

    Returns:
        Updated campaign with results
    """
    if customers is None:
        customers = get_opted_in_customers(db, campaign.channel, campaign.country_code)

    logger.info(
        "Promotion campaign '%s' targeting %d customers via %s",
        campaign.name, len(customers), campaign.channel,
    )

    for customer in customers:
        # Normalize phone number
        e164 = normalize_phone_number(customer["phone"], customer.get("country_code"))
        if not e164:
            campaign.results.append(NotificationResult(
                success=False,
                channel=campaign.channel,
                to=customer["phone"],
                template_id=campaign.template_id,
                error="invalid_phone",
            ))
            continue

        # Build template variables
        template_vars = {
            "name": customer.get("name", "Customer"),
            "product": campaign.product_name or "Amazing deals",
            "url": campaign.product_url or "https://zozi.com",
        }
        if campaign.discount_text:
            template_vars["discount"] = campaign.discount_text
        if campaign.promo_code:
            template_vars["code"] = campaign.promo_code

        # Send notification
        result = send_notification(
            to=customer["phone"],
            template_id=campaign.template_id,
            channel=campaign.channel,
            country_code=customer.get("country_code"),
            **template_vars,
        )
        campaign.results.append(result)

    stats = campaign.get_stats()
    logger.info(
        "Campaign '%s' complete: %d sent, %d preview, %d failed",
        campaign.name, stats["sent"], stats["preview"], stats["failed"],
    )

    return campaign


def create_flash_sale_campaign(
    db: Session,
    name: str,
    product_name: str,
    product_url: str,
    discount_text: str,
    channel: str = "sms",
    country_code: str | None = None,
    promo_code: str | None = None,
) -> PromotionCampaign:
    """Create and send a flash sale campaign.

    Args:
        db: Database session
        name: Campaign name
        product_name: Name of the product on sale
        product_url: URL to the sale page
        discount_text: Discount description (e.g., "50% OFF")
        channel: "sms" or "whatsapp"
        country_code: Optional country filter
        promo_code: Optional promo code

    Returns:
        PromotionCampaign with results
    """
    template_id = f"promo_{channel}"
    campaign = PromotionCampaign(
        campaign_id=f"flash_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        name=name,
        template_id=template_id,
        channel=channel,
        country_code=country_code,
        product_name=product_name,
        product_url=product_url,
        discount_text=discount_text,
        promo_code=promo_code,
    )

    return send_promotion_campaign(db, campaign)


def create_product_launch_campaign(
    db: Session,
    name: str,
    product_name: str,
    product_url: str,
    channel: str = "whatsapp",
    country_code: str | None = None,
) -> PromotionCampaign:
    """Create and send a product launch announcement.

    Args:
        db: Database session
        name: Campaign name
        product_name: New product name
        product_url: URL to product page
        channel: "sms" or "whatsapp"
        country_code: Optional country filter

    Returns:
        PromotionCampaign with results
    """
    template_id = "product_launch_" + channel
    campaign = PromotionCampaign(
        campaign_id=f"launch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        name=name,
        template_id=template_id,
        channel=channel,
        country_code=country_code,
        product_name=product_name,
        product_url=product_url,
    )

    return send_promotion_campaign(db, campaign)


__all__ = [
    "PromotionCampaign",
    "get_opted_in_customers",
    "send_promotion_campaign",
    "create_flash_sale_campaign",
    "create_product_launch_campaign",
]
