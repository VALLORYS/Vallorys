"""Property-related schemas."""

from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field


class PropertyType(str, Enum):
    """Type of property."""
    MAISON = "maison"
    APPARTEMENT = "appartement"
    TERRAIN = "terrain"
    IMMEUBLE = "immeuble"


class DPERating(str, Enum):
    """DPE energy rating."""
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"
    UNKNOWN = "unknown"


class ConditionLevel(str, Enum):
    """General condition level."""
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    POOR = "poor"
    TO_RENOVATE = "to_renovate"


class RoofCondition(str, Enum):
    """Roof condition."""
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    POOR = "poor"
    TO_REPLACE = "to_replace"


class WindowsType(str, Enum):
    """Windows type."""
    DOUBLE_GLAZING_RECENT = "double_glazing_recent"
    DOUBLE_GLAZING_OLD = "double_glazing_old"
    SINGLE_GLAZING = "single_glazing"


class SystemCondition(str, Enum):
    """Condition of technical systems."""
    RECENT = "recent"
    UP_TO_CODE = "up_to_code"
    FUNCTIONAL = "functional"
    TO_RENOVATE = "to_renovate"
    TO_REPLACE = "to_replace"


class ViewQuality(str, Enum):
    """View quality."""
    EXCEPTIONAL = "exceptional"
    PLEASANT = "pleasant"
    ORDINARY = "ordinary"
    OBSTRUCTED = "obstructed"


class NoiseLevel(str, Enum):
    """Noise level."""
    VERY_QUIET = "very_quiet"
    QUIET = "quiet"
    MODERATE = "moderate"
    NOISY = "noisy"


class PropertyAddress(BaseModel):
    """Property address."""
    street: str | None = None
    city: str
    citycode: Annotated[str, Field(pattern=r"^[0-9]{5}$")]
    postal_code: str | None = None
    lat: float | None = None
    lng: float | None = None


class PropertyCondition(BaseModel):
    """Property condition details."""
    global_: ConditionLevel | None = Field(default=None, alias="global")
    roof: RoofCondition | None = None
    windows: WindowsType | None = None
    heating: SystemCondition | None = None
    electrical: SystemCondition | None = None
    plumbing: SystemCondition | None = None

    class Config:
        populate_by_name = True


class PropertyRenovation(BaseModel):
    """Property renovation details."""
    last_major_renovation_year: int | None = None
    estimated_work_budget: float | None = None
    work_description: str | None = None


class PropertyAmenities(BaseModel):
    """Property amenities."""
    garage: bool = False
    parking_spots: int = 0
    cellar: bool = False
    pool: bool = False
    terrace: bool = False
    balcony: bool = False
    garden: bool = False
    elevator: bool = False
    fireplace: bool = False


class PropertyEnvironment(BaseModel):
    """Property environment characteristics."""
    view: ViewQuality | None = None
    noise_level: NoiseLevel | None = None
    nearby_shops: bool = False
    nearby_transport: bool = False
    nearby_schools: bool = False


class PropertyProfile(BaseModel):
    """Complete property profile."""
    id: str | None = None
    address: PropertyAddress
    type: PropertyType
    surface_living: Annotated[float, Field(gt=0, description="Living area in m²")]
    surface_land: float | None = Field(default=None, description="Land area in m²")
    rooms: Annotated[int, Field(ge=1)] = 1
    bedrooms: int | None = None
    bathrooms: int | None = None
    floor: int | None = None
    floors_total: int | None = None
    construction_year: int | None = None
    dpe_rating: DPERating = DPERating.UNKNOWN
    ges_rating: DPERating = DPERating.UNKNOWN
    condition: PropertyCondition | None = None
    renovation: PropertyRenovation | None = None
    amenities: PropertyAmenities | None = None
    environment: PropertyEnvironment | None = None

    def get_effective_amenities(self) -> PropertyAmenities:
        """Get amenities with defaults."""
        return self.amenities or PropertyAmenities()

    def get_effective_condition(self) -> PropertyCondition:
        """Get condition with defaults."""
        return self.condition or PropertyCondition()

    def get_effective_environment(self) -> PropertyEnvironment:
        """Get environment with defaults."""
        return self.environment or PropertyEnvironment()
