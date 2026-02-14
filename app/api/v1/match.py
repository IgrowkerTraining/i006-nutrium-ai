"""Matching API endpoints for nutritionist-patient compatibility analysis."""

from fastapi import APIRouter, HTTPException, Depends
from typing import List

from app.models.schemas import (
    MatchAnalysisRequest,
    MatchAnalysisResponse,
    ErrorResponse
)
from app.services.ai_service import AIService
from app.services.matching_service import MatchingService, get_matching_service
from app.api.dependencies import get_ai_service
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/match", tags=["matching"])


@router.post("/analyze", response_model=MatchAnalysisResponse)
async def analyze_nutritionist_match(
    request: MatchAnalysisRequest,
    ai_service: AIService = Depends(get_ai_service)
):
    """
    Analyze compatibility between a patient and nutritionists using AI.
    
    This endpoint uses advanced AI models to evaluate the compatibility between
    a patient's profile (health goals, dietary restrictions, preferences) and
    multiple nutritionists (specializations, experience, location, etc.).
    
    **Key Features:**
    - AI-powered analysis using GPT-4 or Claude
    - Multiple compatibility criteria evaluation
    - Detailed match reasons with weighted scores
    - Top N recommendations
    
    **Request Body:**
    - **patient_profile**: Patient's health goals and preferences
    - **nutritionists**: List of nutritionists to analyze
    - **top_n**: Number of top matches to return (default: 5)
    - **ai_model**: AI model to use (default: openai/gpt-4)
    
    **Response:**
    - List of top matched nutritionists with compatibility scores
    - Detailed reasons for each match
    - Overall analysis summary
    
    **Example Use Case:**
    A patient looking to lose weight with diabetes can be matched with
    nutritionists specialized in weight management and diabetic diets.
    """
    try:
        logger.info(f"Received match analysis request for {len(request.nutritionists)} nutritionists")
        
        # Get matching service
        matching_service = get_matching_service(ai_service)
        
        # Perform analysis
        response = await matching_service.analyze_match(request)
        
        logger.info(f"Match analysis successful. Returned {len(response.matches)} matches")
        return response
        
    except ValueError as e:
        logger.error(f"Validation error in match analysis: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in match analysis: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze matches: {str(e)}"
        )


@router.get("/health")
async def match_service_health():
    """
    Health check endpoint for matching service.
    
    Returns the status of the matching service.
    """
    return {
        "status": "healthy",
        "service": "matching",
        "version": "1.0.0",
        "message": "Matching service is operational"
    }
