"""
OpenAI Client Wrapper - PR 101: Prompt Parsing Module
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import openai
from pydantic import ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..models.prompt_analysis import PromptAnalysis, Tone, Style, VisualTheme, NarrativeStructure, TargetAudience, ImageryStyle


logger = logging.getLogger(__name__)


def normalize_analysis_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize and validate OpenAI response data to match PromptAnalysis schema.
    Handles enum mapping, data type conversion, and structural validation.

    This function is robust against:
    - Invalid enum values (maps to valid ones with fallbacks)
    - Wrong data types (converts strings to lists, validates numbers)
    - Missing fields (provides sensible defaults)
    - Malformed nested structures (fixes key_elements and color_palette)
    - Invalid ranges (clamps confidence_score, importance values)

    Args:
        data: Raw JSON data from OpenAI (potentially malformed)

    Returns:
        Normalized and validated data ready for PromptAnalysis creation
    """
    normalized = normalize_field_names(data)

    # Normalize enum fields with fallbacks
    enum_mappings = {
        'tone': {
            'professional': Tone.PROFESSIONAL,
            'friendly': Tone.FRIENDLY,
            'enthusiastic': Tone.ENTHUSIASTIC,
            'serious': Tone.SERIOUS,
            'playful': Tone.PLAYFUL,
            'dramatic': Tone.DRAMATIC,
            'calm': Tone.CALM,
            'energetic': Tone.ENERGETIC,
            # Fallback mappings for common variations
            'excited': Tone.ENTHUSIASTIC,
            'fun': Tone.PLAYFUL,
            'formal': Tone.PROFESSIONAL,
            'corporate': Tone.PROFESSIONAL,
            'relaxed': Tone.CALM,
        },
        'style': {
            'modern': Style.MODERN,
            'classic': Style.CLASSIC,
            'minimalist': Style.MINIMALIST,
            'cinematic': Style.CINEMATIC,
            'documentary': Style.DOCUMENTARY,
            'animation': Style.ANIMATION,
            'photorealistic': Style.PHOTOREALISTIC,
            'artistic': Style.ARTISTIC,
            # Fallback mappings
            'animated': Style.ANIMATION,
            'realistic': Style.PHOTOREALISTIC,
            'minimal': Style.MINIMALIST,
            'movie': Style.CINEMATIC,
        },
        'visual_theme': {
            'bright': VisualTheme.BRIGHT,
            'dark': VisualTheme.DARK,
            'warm': VisualTheme.WARM,
            'cool': VisualTheme.COOL,
            'neutral': VisualTheme.NEUTRAL,
            'vibrant': VisualTheme.VIBRANT,
            'monochrome': VisualTheme.MONOCHROME,
            'earthy': VisualTheme.EARTHY,
            # Fallback mappings
            'colorful': VisualTheme.VIBRANT,
            'moody': VisualTheme.DARK,
            'sunny': VisualTheme.WARM,
        },
        'narrative_structure': {
            'problem_solution': NarrativeStructure.PROBLEM_SOLUTION,
            'storytelling': NarrativeStructure.STORYTELLING,
            'demonstration': NarrativeStructure.DEMONSTRATION,
            'testimonial': NarrativeStructure.TESTIMONIAL,
            'comparison': NarrativeStructure.COMPARISON,
            'explanation': NarrativeStructure.EXPLANATION,
            'celebration': NarrativeStructure.CELEBRATION,
            'announcement': NarrativeStructure.ANNOUNCEMENT,
            # Fallback mappings
            'story': NarrativeStructure.STORYTELLING,
            'demo': NarrativeStructure.DEMONSTRATION,
            'tutorial': NarrativeStructure.DEMONSTRATION,
            'how-to': NarrativeStructure.DEMONSTRATION,
            'announce': NarrativeStructure.ANNOUNCEMENT,
        },
        'target_audience': {
            'business': TargetAudience.BUSINESS,
            'consumers': TargetAudience.CONSUMERS,
            'teens': TargetAudience.TEENS,
            'professionals': TargetAudience.PROFESSIONALS,
            'families': TargetAudience.FAMILIES,
            'elders': TargetAudience.ELDERS,
            'general': TargetAudience.GENERAL,
            # Fallback mappings
            'young': TargetAudience.TEENS,
            'kids': TargetAudience.FAMILIES,
            'children': TargetAudience.FAMILIES,
            'enterprise': TargetAudience.BUSINESS,
            'corporate': TargetAudience.BUSINESS,
            'family': TargetAudience.FAMILIES,
        },
        'imagery_style': {
            'photography': ImageryStyle.PHOTOGRAPHY,
            'illustration': ImageryStyle.ILLUSTRATION,
            'graphics': ImageryStyle.GRAPHICS,
            'text_overlays': ImageryStyle.TEXT_OVERLAYS,
            'product_shots': ImageryStyle.PRODUCT_SHOTS,
            'lifestyle': ImageryStyle.LIFESTYLE,
            'abstract': ImageryStyle.ABSTRACT,
            'realistic': ImageryStyle.REALISTIC,
            'animation': ImageryStyle.ANIMATION,
            # Fallback mappings
            'photo': ImageryStyle.PHOTOGRAPHY,
            'animated': ImageryStyle.ANIMATION,
            'graphic': ImageryStyle.GRAPHICS,
            'product': ImageryStyle.PRODUCT_SHOTS,
            'real': ImageryStyle.REALISTIC,
            'illustrated': ImageryStyle.ILLUSTRATION,
        },
    }

    # Apply enum normalization
    for field, mapping in enum_mappings.items():
        if field in normalized:
            value = normalized[field]
            if isinstance(value, str):
                normalized[field] = mapping.get(value.lower(), mapping.get('general', Tone.FRIENDLY))
            else:
                # If not a string, use a sensible default
                normalized[field] = mapping.get('general', Tone.FRIENDLY)

    # Normalize list fields
    list_fields = ['key_themes', 'key_messages', 'analysis_notes']
    for field in list_fields:
        if field in normalized:
            value = normalized[field]
            if isinstance(value, list):
                # Ensure all items are strings and limit length
                normalized[field] = [str(item) for item in value[:10]]  # Max 10 items
            elif isinstance(value, str):
                # If it's a string, try to split on common separators
                normalized[field] = [item.strip() for item in value.split(',')][:10]
            else:
                normalized[field] = []
        else:
            normalized[field] = []

    # Normalize key_elements (complex nested structure)
    if 'key_elements' in normalized:
        elements = normalized['key_elements']
        if isinstance(elements, list):
            normalized_elements = []
            for element in elements[:5]:  # Max 5 elements
                if isinstance(element, dict):
                    # Ensure required fields exist with defaults
                    elem_type = element.get('element_type', 'unknown')
                    description = element.get('description', 'No description')
                    importance = element.get('importance', 3)

                    # Validate importance is 1-5
                    if not isinstance(importance, int) or importance < 1 or importance > 5:
                        importance = 3

                    normalized_elements.append({
                        'element_type': str(elem_type),
                        'description': str(description),
                        'importance': importance
                    })
                elif isinstance(element, str):
                    # If it's just a string, create a basic element
                    normalized_elements.append({
                        'element_type': 'general',
                        'description': str(element),
                        'importance': 3
                    })
            normalized['key_elements'] = normalized_elements
        else:
            normalized['key_elements'] = []

    # Normalize color_palette (nested object)
    if 'color_palette' in normalized:
        palette = normalized['color_palette']
        if isinstance(palette, dict):
            # Ensure primary_colors and secondary_colors are lists of strings
            primary = palette.get('primary_colors', [])
            secondary = palette.get('secondary_colors', [])
            mood = palette.get('mood', 'neutral')

            if isinstance(primary, list):
                primary = [str(color) for color in primary]
            else:
                primary = []

            if isinstance(secondary, list):
                secondary = [str(color) for color in secondary]
            else:
                secondary = []

            normalized['color_palette'] = {
                'primary_colors': primary,
                'secondary_colors': secondary,
                'mood': str(mood)
            }
        else:
            # Default color palette
            normalized['color_palette'] = {
                'primary_colors': ['#0066CC'],
                'secondary_colors': ['#666666'],
                'mood': 'neutral'
            }

    # Normalize confidence_score
    if 'confidence_score' in normalized:
        score = normalized['confidence_score']
        if isinstance(score, (int, float)):
            # Ensure it's between 0.0 and 1.0
            normalized['confidence_score'] = max(0.0, min(1.0, float(score)))
        else:
            normalized['confidence_score'] = 0.5

    # Ensure required string fields exist
    string_fields = ['narrative_intent', 'pacing', 'music_style']
    for field in string_fields:
        if field in normalized:
            normalized[field] = str(normalized[field])
        else:
            normalized[field] = 'moderate' if field == 'pacing' else 'corporate' if field == 'music_style' else 'Create engaging content'

    # Handle product_focus (can be null)
    if 'product_focus' in normalized:
        value = normalized['product_focus']
        if value is None or value == 'null' or value == '':
            normalized['product_focus'] = None
        else:
            normalized['product_focus'] = str(value)

    return normalized


def normalize_field_names(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform OpenAI response field names to match PromptAnalysis schema.
    Converts capitalized field names (e.g., 'Tone', 'Confidence Score') to
    lowercase snake_case (e.g., 'tone', 'confidence_score').

    Args:
        data: Raw JSON data from OpenAI

    Returns:
        Normalized data with correct field names
    """
    # Mapping of possible OpenAI field names to expected schema field names
    field_mapping = {
        'Tone': 'tone',
        'Style': 'style',
        'Narrative Intent': 'narrative_intent',
        'Narrative Structure': 'narrative_structure',
        'Target Audience': 'target_audience',
        'Key Themes': 'key_themes',
        'Key Messages': 'key_messages',
        'Visual Theme': 'visual_theme',
        'Imagery Style': 'imagery_style',
        'Color Palette': 'color_palette',
        'Key Elements': 'key_elements',
        'Product Focus': 'product_focus',
        'Pacing': 'pacing',
        'Music Style': 'music_style',
        'Confidence Score': 'confidence_score',
        'Analysis Notes': 'analysis_notes',
        # Also handle lowercase versions in case they're partially correct
        'narrative intent': 'narrative_intent',
        'narrative structure': 'narrative_structure',
        'target audience': 'target_audience',
        'key themes': 'key_themes',
        'key messages': 'key_messages',
        'visual theme': 'visual_theme',
        'imagery style': 'imagery_style',
        'color palette': 'color_palette',
        'key elements': 'key_elements',
        'product focus': 'product_focus',
        'music style': 'music_style',
        'confidence score': 'confidence_score',
        'analysis notes': 'analysis_notes',
    }

    normalized = {}
    for key, value in data.items():
        # Use mapping if available, otherwise keep original key
        normalized_key = field_mapping.get(key, key)
        normalized[normalized_key] = value

    return normalized


class OpenAIClient:
    """Wrapper for OpenAI API calls with retry logic and error handling"""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        self.client = openai.AsyncOpenAI(api_key=api_key)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((openai.APIError, openai.APIConnectionError, openai.RateLimitError))
    )
    async def analyze_prompt(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> PromptAnalysis:
        """
        Analyze a video generation prompt using OpenAI

        Args:
            prompt: The user's prompt text
            context: Optional additional context

        Returns:
            PromptAnalysis: Structured analysis of the prompt

        Raises:
            Exception: If analysis fails after retries
        """
        try:
            # Create the analysis prompt
            system_prompt = self._create_system_prompt()
            user_prompt = self._create_user_prompt(prompt, context)

            logger.warning(f"[CHATGPT_INPUT] ===== SENDING TO CHATGPT FOR PREPROCESSING =====")
            logger.warning(f"[CHATGPT_INPUT] System Prompt: {system_prompt}")
            logger.warning(f"[CHATGPT_INPUT] User Prompt: {user_prompt}")
            logger.warning(f"[CHATGPT_INPUT] Model: {self.model}")
            logger.warning(f"[CHATGPT_INPUT] ===== END CHATGPT INPUT =====")

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent analysis
                max_tokens=1500,  # Limit response length
                response_format={"type": "json_object"}  # Ensure JSON response
            )

            # Extract and parse the response
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from OpenAI")

            logger.warning(f"[CHATGPT_OUTPUT] ===== RECEIVED FROM CHATGPT =====")
            logger.warning(f"[CHATGPT_OUTPUT] Raw Response: {content}")
            logger.warning(f"[CHATGPT_OUTPUT] ===== END CHATGPT OUTPUT =====")

            # Parse the JSON response
            analysis_data = json.loads(content)

            logger.warning(f"[FIELD_TRANSFORM] Original fields: {list(analysis_data.keys())}")

            # Normalize field names and data types to match schema (handles capitalized names and data validation)
            analysis_data = normalize_analysis_data(analysis_data)

            logger.warning(f"[FIELD_TRANSFORM] Normalized fields: {list(analysis_data.keys())}")

            # Validate and create PromptAnalysis object (should now be robust against malformed data)
            try:
                analysis = PromptAnalysis(**analysis_data)
            except ValidationError as e:
                logger.error(f"PromptAnalysis validation failed after normalization: {e}")
                raise Exception(f"Failed to create valid analysis from OpenAI response: {str(e)}")
            analysis.original_prompt = prompt

            # Convert OpenAI's unix timestamp (or datetime) into a UTC ISO 8601 string for downstream services.
            raw_created = getattr(response, "created", None)
            if isinstance(raw_created, (int, float)):
                created_dt = datetime.fromtimestamp(raw_created, tz=timezone.utc)
                analysis.analysis_timestamp = created_dt.isoformat().replace("+00:00", "Z")
            elif isinstance(raw_created, datetime):
                created_dt = raw_created.astimezone(timezone.utc)
                analysis.analysis_timestamp = created_dt.isoformat().replace("+00:00", "Z")
            else:
                analysis.analysis_timestamp = str(raw_created) if raw_created is not None else datetime.utcnow().replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")

            analysis.model_version = self.model

            logger.info(f"Successfully analyzed prompt (confidence: {analysis.confidence_score})")
            return analysis

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response as JSON: {e}")
            raise Exception("Failed to parse analysis response")
        except openai.AuthenticationError as e:
            logger.error(f"OpenAI authentication error: {e}")
            raise Exception("OpenAI authentication failed")
        except openai.PermissionDeniedError as e:
            logger.error(f"OpenAI permission denied: {e}")
            raise Exception("OpenAI permission denied")
        except openai.RateLimitError as e:
            logger.error(f"OpenAI rate limit exceeded: {e}")
            raise Exception("OpenAI rate limit exceeded - please try again later")
        except openai.APIConnectionError as e:
            logger.error(f"OpenAI connection error: {e}")
            raise Exception("Failed to connect to OpenAI API")
        except Exception as e:
            logger.error(f"Unexpected error during prompt analysis: {e}")
            raise Exception(f"Prompt analysis failed: {str(e)}")

    def _create_system_prompt(self) -> str:
        """Create the system prompt for prompt analysis"""
        return """You are an expert video content strategist and prompt analyzer. Your task is to analyze user prompts for video generation and extract structured information that will ensure narrative, thematic, stylistic, and imagery consistency across the entire video.

For each prompt, analyze and extract:

1. **tone**: The emotional tone (professional, friendly, enthusiastic, serious, playful, dramatic, calm, energetic)

2. **style**: Visual and narrative approach (modern, classic, minimalist, cinematic, documentary, animation, photorealistic, artistic)

3. **narrative_intent**: What the video is trying to achieve (inform, persuade, entertain, demonstrate, etc.)

4. **narrative_structure**: How the content should be structured (problem_solution, storytelling, demonstration, testimonial, comparison, explanation, celebration, announcement)

5. **target_audience**: Who the video is for (business, consumers, teens, professionals, families, elders, general)

6. **key_themes**: Main themes to maintain consistency throughout the video (array of strings)

7. **key_messages**: Core messages that must be conveyed (array of strings)

8. **visual_theme**: Overall aesthetic (bright, dark, warm, cool, neutral, vibrant, monochrome, earthy)

9. **imagery_style**: Type of visual elements (photography, illustration, graphics, text_overlays, product_shots, lifestyle, abstract, realistic, animation)

10. **color_palette**: Object with primary_colors (array of hex codes), secondary_colors (array of hex codes), and mood (string)

11. **key_elements**: Important elements that should appear in the video (array of objects with element_type, description, importance 1-5)

12. **product_focus**: What product/service is being featured (string or null if none)

13. **pacing**: Suggested video pacing (slow, moderate, fast)

14. **music_style**: Recommended background music style

15. **confidence_score**: Your confidence in this analysis (0.0-1.0)

16. **analysis_notes**: Additional analysis notes (array of strings)

Make your best guess for elements not explicitly mentioned in the prompt. Provide a confidence score (0.0-1.0) based on how well the prompt supports your analysis.

IMPORTANT: Return your analysis as a valid JSON object with EXACTLY these field names (all lowercase with underscores):
{
  "tone": "professional",
  "style": "modern",
  "narrative_intent": "string describing the intent",
  "narrative_structure": "problem_solution",
  "target_audience": "business",
  "key_themes": ["theme1", "theme2"],
  "key_messages": ["message1", "message2"],
  "visual_theme": "bright",
  "imagery_style": "photography",
  "color_palette": {
    "primary_colors": ["#HEXCODE"],
    "secondary_colors": ["#HEXCODE"],
    "mood": "professional"
  },
  "key_elements": [
    {
      "element_type": "product",
      "description": "description here",
      "importance": 5
    }
  ],
  "product_focus": "product name or null",
  "pacing": "moderate",
  "music_style": "corporate",
  "confidence_score": 0.85,
  "analysis_notes": ["note1", "note2"]
}

Use these EXACT field names - all lowercase with underscores between words."""

    def _create_user_prompt(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Create the user prompt for analysis"""
        user_prompt = f"Please analyze this video generation prompt and extract structured information for consistent video creation:\n\n{prompt}"

        if context:
            user_prompt += f"\n\nAdditional context: {json.dumps(context)}"

        return user_prompt
