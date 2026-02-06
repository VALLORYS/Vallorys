"""Objection handling schemas."""

from enum import Enum

from pydantic import BaseModel, Field


class ObjectionCategory(str, Enum):
    """Categories of seller objections."""
    PRICE_TOO_LOW = "price_too_low"
    NEIGHBOR_SOLD_HIGHER = "neighbor_sold_higher"
    OTHER_AGENCY_ESTIMATE = "other_agency_estimate"
    WANT_TO_TEST_MARKET = "want_to_test_market"
    NOT_URGENT = "not_urgent"
    NEED_TIME_TO_THINK = "need_time_to_think"
    COMMISSION_TOO_HIGH = "commission_too_high"
    DONT_TRUST_ESTIMATES = "dont_trust_estimates"
    OTHER = "other"


class SuggestedTone(str, Enum):
    """Suggested tone for response."""
    EMPATHETIC = "empathetic"
    FACTUAL = "factual"
    CHALLENGING = "challenging"
    REASSURING = "reassuring"


class ConversationMessage(BaseModel):
    """A message in the conversation history."""
    role: str = Field(pattern="^(agent|seller)$")
    text: str


class ObjectionRequest(BaseModel):
    """Request for objection response."""
    objection_text: str = Field(max_length=500)
    objection_category: ObjectionCategory | None = None
    valuation_id: str | None = None
    conversation_history: list[ConversationMessage] = Field(
        default=[],
        max_length=10,
    )
    # Embedded context (optional, for faster processing)
    valuation_summary: dict | None = None
    seller_context: dict | None = None


class ObjectionResponse(BaseModel):
    """Response to an objection."""
    objection_id: str
    quick_response: str = Field(description="10-second response")
    detailed_response: str = Field(description="45-second response")
    follow_up_question: str = Field(description="Question to regain control")
    proof_point: str = Field(description="Proof from valuation report")
    suggested_tone: SuggestedTone
    additional_tips: list[str] = []
    detected_category: ObjectionCategory | None = None


class ObjectionOutcome(str, Enum):
    """Outcome after handling objection."""
    OBJECTION_RESOLVED = "objection_resolved"
    OBJECTION_PERSISTS = "objection_persists"
    NEW_OBJECTION = "new_objection"
    MEETING_ENDED = "meeting_ended"


class ResponseUsed(str, Enum):
    """Which response was used."""
    QUICK = "quick"
    DETAILED = "detailed"
    CUSTOM = "custom"
    NONE = "none"


class AgentFeedback(str, Enum):
    """Agent feedback on response quality."""
    HELPFUL = "helpful"
    NOT_HELPFUL = "not_helpful"
    PARTIALLY_HELPFUL = "partially_helpful"


class ObjectionLogRequest(BaseModel):
    """Request to log objection outcome."""
    objection_id: str
    response_used: ResponseUsed
    outcome: ObjectionOutcome
    agent_feedback: AgentFeedback | None = None


class ProactiveSuggestion(BaseModel):
    """A proactive suggestion for the agent."""
    trigger: str
    message: str
    priority: str = Field(pattern="^(high|medium|low)$")


class ProactiveSuggestRequest(BaseModel):
    """Request for proactive suggestions."""
    current_phase: str = Field(
        pattern="^(discovery|presentation|objection_handling|closing)$"
    )
    valuation_id: str | None = None
    seller_context: dict | None = None


class ProactiveSuggestResponse(BaseModel):
    """Response with proactive suggestions."""
    suggestions: list[ProactiveSuggestion]
