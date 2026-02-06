"""Field pack schemas for argumentaire, scripts, checklists."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from vallorys.schemas.seller import SellerProfile
from vallorys.schemas.valuation import ValuationResult


class Tone(str, Enum):
    """Tone for generated content."""
    PROFESSIONAL = "professional"
    REASSURING = "reassuring"
    DIRECT = "direct"
    EMPATHETIC = "empathetic"


class TemplateType(str, Enum):
    """Type of template to generate."""
    EMAIL_PRE_RDV = "email_pre_rdv"
    EMAIL_POST_RDV = "email_post_rdv"
    SMS_REMINDER = "sms_reminder"
    OBJECTION_RESPONSE = "objection_response"
    FOLLOW_UP = "follow_up"


# Argumentaire schemas

class ArgumentPoint(BaseModel):
    """A single argument point."""
    point: str
    argument: str
    proof: str | None = None


class Argumentaire(BaseModel):
    """Complete argumentaire for seller meeting."""
    opening: str
    key_points: list[ArgumentPoint]
    closing: str
    tone: Tone = Tone.PROFESSIONAL


# RDV Script schemas

class ScriptPhase(BaseModel):
    """A phase in the RDV script."""
    phase: str
    duration_minutes: int
    timing: str
    objectives: list[str]
    script: str
    questions: list[str] = []
    key_moments: list[str] = []
    common_objections: list[str] = []
    closing_options: list[str] = []
    tips: list[str] = []
    checklist: list[str] = []


class RdvScript(BaseModel):
    """Complete RDV script."""
    total_duration_minutes: int
    phases: list[ScriptPhase]


# Checklist schemas

class ChecklistItem(BaseModel):
    """A single checklist item."""
    item: str
    required: bool = False
    note: str | None = None
    checked: bool = False


class ChecklistCategory(BaseModel):
    """A category of checklist items."""
    category: str
    items: list[ChecklistItem]


class Checklist(BaseModel):
    """Complete pre-mandat checklist."""
    categories: list[ChecklistCategory]


# Template schemas

class Template(BaseModel):
    """A generated template."""
    template_type: TemplateType
    subject: str | None = None
    body: str
    variables: list[str] = []


class ObjectionTemplate(BaseModel):
    """Template for objection response."""
    objection: str
    response_quick: str
    response_detailed: str
    follow_up_question: str | None = None


# Request/Response schemas

class GenerateOptions(BaseModel):
    """Options for what to generate."""
    argumentaire: bool = True
    script_rdv: bool = True
    checklist: bool = True
    templates: list[TemplateType] = []


class FieldPackRequest(BaseModel):
    """Request for field pack generation."""
    valuation_id: str
    seller: SellerProfile | None = None
    generate: GenerateOptions = Field(default_factory=GenerateOptions)
    options: dict = Field(default_factory=dict)

    def get_tone(self) -> Tone:
        """Get requested tone with default."""
        tone_str = self.options.get("tone", "professional")
        return Tone(tone_str)

    def get_rdv_duration(self) -> int:
        """Get RDV duration with default."""
        return self.options.get("rdv_duration_minutes", 60)


class FieldPackResponse(BaseModel):
    """Response for field pack generation."""
    fieldpack_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    valuation_id: str
    argumentaire: Argumentaire | None = None
    script_rdv: RdvScript | None = None
    checklist: Checklist | None = None
    templates: dict[str, Template | ObjectionTemplate] = {}
