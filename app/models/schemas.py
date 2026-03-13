"""Pydantic models for request/response schemas."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class SimpleAIRequest(BaseModel):
        prompt: str

class SimpleAIResponse(BaseModel):
        response: str


class ChatMessage(BaseModel):
    """Chat message model."""

    role: str = Field(..., description="Message role: 'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Chat completion request model."""

    model: str = Field(default="openai/gpt-3.5-turbo", description="AI model to use")
    messages: List[ChatMessage] = Field(..., description="List of chat messages")
    max_tokens: Optional[int] = Field(
        default=4000, ge=1, le=4096, description="Maximum tokens to generate"
    )
    temperature: Optional[float] = Field(
        default=0.7, ge=0.0, le=2.0, description="Sampling temperature"
    )
    stream: Optional[bool] = Field(
        default=False, description="Enable streaming response"
    )

class Usage(BaseModel):
    """Token usage information."""

    prompt_tokens: int = Field(..., description="Number of tokens in the prompt")
    completion_tokens: int = Field(..., description="Number of tokens in the completion")
    total_tokens: int = Field(..., description="Total number of tokens used")

class ChatResponse(BaseModel):
    """Chat completion response model."""

    id: str = Field(..., description="Response ID")
    object: str = Field(default="chat.completion", description="Object type")
    created: int = Field(..., description="Creation timestamp")
    model: str = Field(..., description="Model used")
    choices: List[Dict[str, Any]] = Field(..., description="Response choices")
    usage: Optional[Usage] = Field(
        default=None, description="Token usage information"
    )


class ModelInfo(BaseModel):
    """AI model information."""

    id: str = Field(..., description="Model ID")
    name: Optional[str] = Field(default=None, description="Model display name")
    description: Optional[str] = Field(default=None, description="Model description")
    pricing: Optional[Dict[str, Any]] = Field(
        default=None, description="Pricing information"
    )


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Response timestamp")
    version: str = Field(..., description="Application version")
    message: Optional[str] = Field(
        default=None, description="Additional status message"
    )


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error type")
    detail: Optional[str] = Field(default=None, description="Error details")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Error timestamp"
    )


class RootResponse(BaseModel):
    """Root endpoint response model."""

    message: str = Field(..., description="Welcome message")
    version: str = Field(..., description="Application version")
    docs: str = Field(..., description="Documentation URL")
    health: str = Field(..., description="Health check URL")


# ============================================================
# NUTRIUM MATCHING SCHEMAS - Sprint 1
# ============================================================


class PatientProfileRequest(BaseModel):
    """Patient profile for matching analysis."""

    health_goal: str = Field(..., description="Primary health goal", min_length=10)
    dietary_restrictions: List[str] = Field(
        default=[], description="Dietary restrictions"
    )
    allergies: List[str] = Field(default=[], description="Food allergies")
    health_conditions: List[str] = Field(default=[], description="Health conditions")
    age: Optional[int] = Field(default=None, ge=1, le=150, description="Patient age")
    gender: Optional[str] = Field(default=None, description="Patient gender")
    location: Optional[str] = Field(default=None, description="Patient location")
    preferred_language: str = Field(default="es", description="Preferred language")
    communication_style: Optional[str] = Field(
        default=None, description="Preferred communication style"
    )
    preferred_gender: Optional[str] = Field(
        default=None, description="Preferred nutritionist gender"
    )
    budget_range: Optional[str] = Field(
        default=None, description="Budget range for consultations"
    )


class NutritionistProfileData(BaseModel):
    """Nutritionist data for matching."""

    id: str = Field(..., description="Nutritionist ID")
    name: str = Field(..., description="Nutritionist name")
    specializations: List[str] = Field(
        default=[], description="Areas of specialization"
    )
    years_of_experience: int = Field(..., ge=0, description="Years of experience")
    languages: List[str] = Field(default=["es"], description="Languages spoken")
    location: Optional[str] = Field(default=None, description="Practice location")
    rating: float = Field(default=0.0, ge=0.0, le=5.0, description="Average rating")
    total_reviews: int = Field(default=0, ge=0, description="Total number of reviews")
    consultation_fee_range: Optional[str] = Field(default=None, description="Fee range")
    bio: Optional[str] = Field(default=None, description="Professional bio")
    accepts_new_patients: bool = Field(
        default=True, description="Accepting new patients"
    )


class MatchReason(BaseModel):
    """Individual reason for the match."""

    category: str = Field(..., description="Reason category")
    description: str = Field(..., description="Detailed explanation")
    weight: float = Field(
        ..., ge=0.0, le=1.0, description="Impact weight on final score"
    )


class NutritionistMatch(BaseModel):
    """Individual nutritionist match result."""

    nutritionist_id: str = Field(..., description="Nutritionist ID")
    nutritionist_name: str = Field(..., description="Nutritionist name")
    compatibility_score: float = Field(
        ..., ge=0.0, le=100.0, description="Compatibility score"
    )
    match_reasons: List[MatchReason] = Field(..., description="Reasons for the match")
    specializations: List[str] = Field(..., description="Nutritionist specializations")
    years_of_experience: int = Field(..., description="Years of experience")
    rating: float = Field(..., description="Average rating")
    location: Optional[str] = Field(default=None, description="Location")
    consultation_fee_range: Optional[str] = Field(default=None, description="Fee range")
    bio_excerpt: Optional[str] = Field(default=None, description="Short bio excerpt")


class MatchAnalysisRequest(BaseModel):
    """Request for nutritionist matching analysis."""

    patient_profile: PatientProfileRequest = Field(
        ..., description="Patient profile data"
    )
    nutritionists: List[NutritionistProfileData] = Field(
        ..., description="List of nutritionists to analyze", min_items=1
    )
    top_n: int = Field(
        default=5, ge=1, le=20, description="Number of top matches to return"
    )
    ai_model: str = Field(
        default="qwen/qwen3.5-35b-a3b", description="AI model to use for analysis"
    )


class MatchAnalysisResponse(BaseModel):
    """Response with matched nutritionists."""

    patient_health_goal: str = Field(..., description="Patient's primary health goal")
    total_analyzed: int = Field(..., description="Total nutritionists analyzed")
    matches: List[NutritionistMatch] = Field(
        ..., description="Top matched nutritionists"
    )
    analysis_summary: str = Field(..., description="Overall analysis summary")
    generated_at: datetime = Field(
        default_factory=datetime.now, description="Analysis timestamp"
    )
    model_used: str = Field(..., description="AI model used for analysis")
