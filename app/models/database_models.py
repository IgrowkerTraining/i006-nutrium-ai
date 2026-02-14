"""Database ORM models for Nutrium."""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean, Column, DateTime, Integer, String, Text, 
    Numeric, ForeignKey, CheckConstraint, Index, func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.config.database import Base


class User(Base):
    """User model for authentication and basic info."""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    email_verified = Column(Boolean, default=False)
    
    # Relationships
    patient_profile = relationship("PatientProfile", back_populates="user", uselist=False)
    nutritionist_profile = relationship("NutritionistProfile", back_populates="user", uselist=False)
    
    __table_args__ = (
        CheckConstraint("role IN ('patient', 'nutritionist', 'admin')"),
    )


class PatientProfile(Base):
    """Patient profile with health goals and preferences."""
    
    __tablename__ = "patient_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Demographic info
    age = Column(Integer, nullable=True)
    gender = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True)
    
    # Goals and needs
    health_goal = Column(Text, nullable=False)
    dietary_restrictions = Column(JSONB, default=list)
    allergies = Column(JSONB, default=list)
    health_conditions = Column(JSONB, default=list)
    
    # Communication preferences
    preferred_language = Column(String(50), default="es")
    communication_style = Column(String(100), nullable=True)
    availability_schedule = Column(JSONB, default=dict)
    
    # Nutritionist preferences
    preferred_gender = Column(String(50), nullable=True)
    preferred_experience_level = Column(String(100), nullable=True)
    budget_range = Column(String(100), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="patient_profile")
    
    __table_args__ = (
        CheckConstraint("age > 0 AND age < 150"),
        Index("idx_patient_health_goal", "health_goal", postgresql_using="gin", postgresql_ops={"health_goal": "gin_trgm_ops"}),
    )


class NutritionistProfile(Base):
    """Nutritionist profile with professional info and specializations."""
    
    __tablename__ = "nutritionist_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Professional info
    license_number = Column(String(100), unique=True, nullable=False)
    years_of_experience = Column(Integer, nullable=True)
    specializations = Column(JSONB, default=list)
    certifications = Column(JSONB, default=list)
    
    # Languages and communication
    languages = Column(JSONB, default=["es"])
    communication_styles = Column(JSONB, default=list)
    
    # Availability and location
    location = Column(String(255), nullable=True)
    availability_schedule = Column(JSONB, default=dict)
    accepts_new_patients = Column(Boolean, default=True)
    
    # Fees and services
    consultation_fee_range = Column(String(100), nullable=True)
    accepted_insurance = Column(JSONB, default=list)
    service_types = Column(JSONB, default=list)
    
    # Additional info
    bio = Column(Text, nullable=True)
    profile_picture_url = Column(String(500), nullable=True)
    rating = Column(Numeric(3, 2), default=0.00)
    total_reviews = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    verified_at = Column(DateTime(timezone=True), nullable=True)
    is_verified = Column(Boolean, default=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="nutritionist_profile")
    
    __table_args__ = (
        CheckConstraint("years_of_experience >= 0"),
        CheckConstraint("rating >= 0 AND rating <= 5"),
        Index("idx_nutritionist_specializations", "specializations", postgresql_using="gin"),
        Index("idx_nutritionist_rating", "rating", postgresql_order_by="rating DESC"),
    )


class Match(Base):
    """AI-generated matches between patients and nutritionists."""
    
    __tablename__ = "matches"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    nutritionist_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Scoring and compatibility
    compatibility_score = Column(Numeric(5, 2), nullable=False)
    match_reasons = Column(JSONB, default=list)
    ai_analysis = Column(Text, nullable=True)
    
    # Match status
    status = Column(String(50), default="pending", index=True)
    patient_viewed = Column(Boolean, default=False)
    nutritionist_viewed = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    matched_by_model = Column(String(100), nullable=True)
    
    __table_args__ = (
        CheckConstraint("compatibility_score >= 0 AND compatibility_score <= 100"),
        CheckConstraint("status IN ('pending', 'accepted', 'rejected', 'expired')"),
        Index("idx_match_unique", "patient_id", "nutritionist_id", unique=True),
        Index("idx_match_score", "compatibility_score", postgresql_order_by="compatibility_score DESC"),
    )


class Appointment(Base):
    """Appointments between patients and nutritionists."""
    
    __tablename__ = "appointments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    match_id = Column(UUID(as_uuid=True), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    nutritionist_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Appointment info
    scheduled_at = Column(DateTime(timezone=True), nullable=False, index=True)
    duration_minutes = Column(Integer, default=60)
    appointment_type = Column(String(100), nullable=False)
    status = Column(String(50), default="scheduled", index=True)
    
    # Notes and follow-up
    patient_notes = Column(Text, nullable=True)
    nutritionist_notes = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    
    __table_args__ = (
        CheckConstraint("status IN ('scheduled', 'completed', 'cancelled', 'no-show')"),
    )


class Review(Base):
    """Reviews and ratings for nutritionists."""
    
    __tablename__ = "reviews"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    appointment_id = Column(UUID(as_uuid=True), ForeignKey("appointments.id", ondelete="CASCADE"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    nutritionist_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Rating
    rating = Column(Integer, nullable=False, index=True)
    review_text = Column(Text, nullable=True)
    
    # Specific criteria
    communication_rating = Column(Integer, nullable=True)
    professionalism_rating = Column(Integer, nullable=True)
    effectiveness_rating = Column(Integer, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_verified = Column(Boolean, default=False)
    
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5"),
        CheckConstraint("communication_rating >= 1 AND communication_rating <= 5"),
        CheckConstraint("professionalism_rating >= 1 AND professionalism_rating <= 5"),
        CheckConstraint("effectiveness_rating >= 1 AND effectiveness_rating <= 5"),
        Index("idx_review_unique", "appointment_id", "patient_id", unique=True),
    )


class AIInteraction(Base):
    """Log of AI interactions for analytics and debugging."""
    
    __tablename__ = "ai_interactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Interaction info
    interaction_type = Column(String(100), nullable=False)
    model_used = Column(String(100), nullable=True)
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    
    # Request/Response
    request_payload = Column(JSONB, nullable=True)
    response_payload = Column(JSONB, nullable=True)
    
    # Performance
    response_time_ms = Column(Integer, nullable=True)
    status = Column(String(50), default="success")
    error_message = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
