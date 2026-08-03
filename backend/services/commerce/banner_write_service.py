"""Banner write service — DB write operations for banners."""
from datetime import datetime, timezone
from typing import cast

from sqlalchemy.orm import Session

from data.models import Banner


def create_banner(db: Session, **banner_data) -> Banner:
    banner = Banner(**banner_data)
    db.add(banner)
    db.commit()
    db.refresh(banner)
    return banner


def update_banner(db: Session, banner: Banner, updates: dict) -> Banner:
    for key, value in updates.items():
        setattr(banner, key, value)
    db.commit()
    db.refresh(banner)
    return banner


def delete_banner(db: Session, banner: Banner) -> None:
    db.delete(banner)
    db.commit()


def update_banner_image(db: Session, banner: Banner, image_url: str, filename: str) -> Banner:
    setattr(banner, "image_url", image_url)
    setattr(banner, "updated_at", datetime.now(timezone.utc).replace(tzinfo=None))
    db.commit()
    db.refresh(banner)
    return banner


def reorder_banners(db: Session, banner_ids: list[int]) -> None:
    for index, bid in enumerate(banner_ids):
        db.query(Banner).filter(Banner.id == bid).update({"sort_order": index})
    db.commit()


def bulk_add_banners(db: Session, banners_data: list[dict]) -> None:
    for d in banners_data:
        db.add(Banner(**d))
    db.commit()


def add_banner_if_missing(db: Session, banner_data: dict) -> None:
    existing_titles = {
        title for (title,) in db.query(Banner.title).filter(
            Banner.title == banner_data.get("title")
        ).all()
    }
    if banner_data.get("title") not in existing_titles:
        db.add(Banner(**banner_data))
        db.commit()