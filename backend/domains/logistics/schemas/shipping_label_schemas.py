"""Pydantic request/response DTOs for the shipping label service."""
from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class ShipmentLabelDestination(BaseModel):
    """Validated destination address for a shipping label request."""

    country: str = Field(..., min_length=2, max_length=2)
    city: str = Field(..., min_length=1)


class ShipmentLabelData(BaseModel):
    """Validated shipment payload for a shipping label request."""

    origin_country: str = Field(..., min_length=2, max_length=2)
    origin_city: str = Field(..., min_length=1)
    weight_kg: float = Field(..., gt=0)
    tracking_number: str = Field(..., min_length=1)
    length_cm: float = Field(default=30.0, gt=0)
    width_cm: float = Field(default=20.0, gt=0)
    height_cm: float = Field(default=10.0, gt=0)

    @model_validator(mode="after")
    def _check_positive_dimensions(self) -> ShipmentLabelData:
        if self.length_cm <= 0 or self.width_cm <= 0 or self.height_cm <= 0:
            raise ValueError("Package dimensions must be positive numbers")
        return self


def validate_shipment_data(data: dict) -> dict:
    """Validate raw shipment_data dict and return a normalized dict.

    Raises ``pydantic.ValidationError`` when the input is invalid so callers
    (and FastAPI routers) get a 422 response instead of silent misbehavior.
    """
    model = ShipmentLabelData(**data)
    return model.model_dump()


def validate_destination(data: dict) -> dict:
    """Validate raw destination dict and return a normalized dict.

    Raises ``pydantic.ValidationError`` when the input is invalid.
    """
    model = ShipmentLabelDestination(**data)
    return model.model_dump()
