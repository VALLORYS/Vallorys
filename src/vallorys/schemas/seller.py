"""Seller-related schemas."""

from __future__ import annotations

from datetime import date as date_type
from enum import Enum

from pydantic import BaseModel


class SellerType(str, Enum):
    """Type of seller."""
    OWNER_OCCUPIER = "owner_occupier"
    INVESTOR = "investor"
    HEIR = "heir"
    DIVORCING = "divorcing"
    RELOCATING = "relocating"
    OTHER = "other"


class UrgencyLevel(str, Enum):
    """Urgency level."""
    URGENT = "urgent"
    MODERATE = "moderate"
    NO_RUSH = "no_rush"
    UNKNOWN = "unknown"


class PersonalityType(str, Enum):
    """Personality type for communication adaptation."""
    ANALYTICAL = "analytical"
    EXPRESSIVE = "expressive"
    DRIVER = "driver"
    AMIABLE = "amiable"
    UNKNOWN = "unknown"


class PreviousEstimate(BaseModel):
    """Previous estimate from another source."""
    source: str
    amount: float
    date: date_type | None = None


class SellerProfile(BaseModel):
    """Seller profile for personalization."""
    id: str | None = None
    type: SellerType = SellerType.OTHER
    urgency: UrgencyLevel = UrgencyLevel.UNKNOWN
    motivation: str | None = None
    price_expectation: float | None = None
    previous_estimates: list[PreviousEstimate] = []
    objections_history: list[str] = []
    personality_hints: PersonalityType = PersonalityType.UNKNOWN

    def has_competing_estimates(self) -> bool:
        """Check if seller has estimates from other sources."""
        return len(self.previous_estimates) > 0

    def get_highest_previous_estimate(self) -> float | None:
        """Get highest previous estimate amount."""
        if not self.previous_estimates:
            return None
        return max(e.amount for e in self.previous_estimates)
