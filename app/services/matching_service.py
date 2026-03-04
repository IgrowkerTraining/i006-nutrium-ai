"""Matching service for analyzing patient-nutritionist compatibility using AI."""

import json
from typing import List, Dict, Any
from datetime import datetime

from app.services.ai_service import AIService
from app.models.schemas import (
    PatientProfileRequest,
    NutritionistProfileData,
    NutritionistMatch,
    MatchReason,
    MatchAnalysisRequest,
    MatchAnalysisResponse,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class MatchingService:
    """Service for AI-powered nutritionist matching."""

    def __init__(self, ai_service: AIService):
        """Initialize matching service with AI service."""
        self.ai_service = ai_service

    async def analyze_match(
        self, request: MatchAnalysisRequest
    ) -> MatchAnalysisResponse:
        """
        Analyze compatibility between patient and nutritionists using AI.

        Args:
            request: Match analysis request with patient profile and nutritionist list

        Returns:
            MatchAnalysisResponse with top matches and analysis
        """
        logger.info(
            f"Starting match analysis for {len(request.nutritionists)} nutritionists"
        )

        # Build the AI prompt
        prompt = self._build_matching_prompt(
            request.patient_profile, request.nutritionists
        )

        # Call AI service for analysis
        try:
            ai_response = await self._get_ai_analysis(prompt, request.ai_model)

            # Parse AI response and build matches
            matches = self._parse_ai_response(ai_response, request.nutritionists)

            # Sort by compatibility score and take top N
            matches.sort(key=lambda x: x.compatibility_score, reverse=True)
            top_matches = matches[: request.top_n]

            # Build response
            response = MatchAnalysisResponse(
                patient_health_goal=request.patient_profile.health_goal,
                total_analyzed=len(request.nutritionists),
                matches=top_matches,
                analysis_summary=self._generate_summary(
                    request.patient_profile, top_matches
                ),
                model_used=request.ai_model,
            )

            logger.info(
                f"Match analysis completed. Found {len(top_matches)} top matches"
            )
            return response

        except Exception as e:
            logger.error(f"Error in match analysis: {str(e)}")
            raise

    def _build_matching_prompt(
        self,
        patient: PatientProfileRequest,
        nutritionists: List[NutritionistProfileData],
    ) -> str:
        """Build the AI prompt for matching analysis."""

        # Create patient profile summary
        patient_summary = f"""
PERFIL DEL PACIENTE:
- Objetivo de salud: {patient.health_goal}
- Restricciones dietéticas: {', '.join(patient.dietary_restrictions) if patient.dietary_restrictions else 'Ninguna'}
- Alergias: {', '.join(patient.allergies) if patient.allergies else 'Ninguna'}
- Condiciones de salud: {', '.join(patient.health_conditions) if patient.health_conditions else 'Ninguna'}
- Edad: {patient.age if patient.age else 'No especificada'}
- Ubicación: {patient.location if patient.location else 'No especificada'}
- Idioma preferido: {patient.preferred_language}
- Presupuesto: {patient.budget_range if patient.budget_range else 'No especificado'}
"""

        # Create nutritionists summary
        nutritionists_summary = "NUTRICIONISTAS DISPONIBLES:\n\n"
        for idx, nut in enumerate(nutritionists, 1):
            nutritionists_summary += f"""
{idx}. {nut.name} (ID: {nut.id})
   - Especializaciones: {', '.join(nut.specializations)}
   - Experiencia: {nut.years_of_experience} años
   - Idiomas: {', '.join(nut.languages)}
   - Ubicación: {nut.location if nut.location else 'No especificada'}
   - Calificación: {nut.rating}/5.0 ({nut.total_reviews} reseñas)
   - Rango de tarifas: {nut.consultation_fee_range if nut.consultation_fee_range else 'No especificado'}
   - Acepta nuevos pacientes: {'Sí' if nut.accepts_new_patients else 'No'}
"""

        # Build the full prompt
        prompt = f"""
Eres un asistente experto en nutrición que ayuda a emparejar pacientes con nutricionistas ideales.

{patient_summary}

{nutritionists_summary}

TAREA:
Analiza la compatibilidad entre el paciente y cada nutricionista. Para cada nutricionista, proporciona:
1. Un puntaje de compatibilidad del 0 al 100
2. Razones específicas para el match (categoría, descripción y peso)
3. Un análisis breve

CRITERIOS DE EVALUACIÓN:
- Especialización relevante al objetivo del paciente (peso alto)
- Experiencia con condiciones de salud similares (peso alto)
- Compatibilidad de idiomas (peso medio)
- Proximidad geográfica (peso medio)
- Compatibilidad de presupuesto (peso medio)
- Calificaciones y reseñas (peso bajo)
- Disponibilidad para nuevos pacientes (peso bajo)

Responde ÚNICAMENTE con un JSON válido en el siguiente formato:
{{
  "matches": [
    {{
      "nutritionist_id": "id_del_nutricionista",
      "compatibility_score": 85.5,
      "match_reasons": [
        {{
          "category": "Especialización",
          "description": "Especialista en pérdida de peso con 10 años de experiencia",
          "weight": 0.35
        }}
      ],
      "analysis": "Resumen de 1-2 líneas del por qué es un buen match"
    }}
  ]
}}

NO incluyas ningún texto adicional, solo el JSON.
"""

        return prompt

    async def _get_ai_analysis(self, prompt: str, model: str) -> str:
        """Get analysis from AI service."""
        from app.models.schemas import ChatRequest, ChatMessage

        chat_request = ChatRequest(
            model=model,
            messages=[
                ChatMessage(
                    role="system",
                    content="Eres un experto en nutrición que analiza compatibilidad entre pacientes y nutricionistas. Respondes solo con JSON válido.",
                ),
                ChatMessage(role="user", content=prompt),
            ],
            max_tokens=3000,
            temperature=0.5,
        )

        response = await self.ai_service.chat_completion(chat_request)

        # Extract content from response
        if response.choices and len(response.choices) > 0:
            return response.choices[0]["message"]["content"]

        raise ValueError("No response from AI service")

    def _parse_ai_response(
        self, ai_response: str, nutritionists: List[NutritionistProfileData]
    ) -> List[NutritionistMatch]:
        """Parse AI response and create NutritionistMatch objects."""

        try:
            # Parse JSON from AI response
            data = json.loads(ai_response)
            matches_data = data.get("matches", [])

            # Create a lookup dict for nutritionists
            nut_dict = {nut.id: nut for nut in nutritionists}

            matches = []
            for match_data in matches_data:
                nut_id = match_data.get("nutritionist_id")
                nutritionist = nut_dict.get(nut_id)

                if not nutritionist:
                    logger.warning(f"Nutritionist {nut_id} not found in original list")
                    continue

                # Parse match reasons
                reasons = [
                    MatchReason(
                        category=r.get("category", "General"),
                        description=r.get("description", ""),
                        weight=r.get("weight", 0.5),
                    )
                    for r in match_data.get("match_reasons", [])
                ]

                # Create match object
                match = NutritionistMatch(
                    nutritionist_id=nut_id,
                    nutritionist_name=nutritionist.name,
                    compatibility_score=match_data.get("compatibility_score", 0.0),
                    match_reasons=reasons,
                    specializations=nutritionist.specializations,
                    years_of_experience=nutritionist.years_of_experience,
                    rating=nutritionist.rating,
                    location=nutritionist.location,
                    consultation_fee_range=nutritionist.consultation_fee_range,
                    bio_excerpt=(
                        nutritionist.bio[:150] + "..."
                        if nutritionist.bio and len(nutritionist.bio) > 150
                        else nutritionist.bio
                    ),
                )

                matches.append(match)

            return matches

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {str(e)}")
            logger.error(f"AI Response: {ai_response}")
            raise ValueError("AI response is not valid JSON")
        except Exception as e:
            logger.error(f"Error parsing AI response: {str(e)}")
            raise

    def _generate_summary(
        self, patient: PatientProfileRequest, matches: List[NutritionistMatch]
    ) -> str:
        """Generate a summary of the matching analysis."""

        if not matches:
            return "No se encontraron nutricionistas compatibles con el perfil del paciente."

        top_match = matches[0]
        avg_score = sum(m.compatibility_score for m in matches) / len(matches)

        summary = f"""
Análisis completado para objetivo: "{patient.health_goal}".
Se encontraron {len(matches)} nutricionistas compatibles.
El mejor match es {top_match.nutritionist_name} con {top_match.compatibility_score:.1f}% de compatibilidad.
Puntaje promedio de compatibilidad: {avg_score:.1f}%.
        """.strip()

        return summary


# Global instance
matching_service = None


def get_matching_service(ai_service: AIService) -> MatchingService:
    """Get or create matching service instance."""
    global matching_service
    if matching_service is None:
        matching_service = MatchingService(ai_service)
    return matching_service
