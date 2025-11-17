"""
OpenAI Client Wrapper - PR 101: Prompt Parsing Module
"""

import asyncio
import json
import logging
from typing import Any, Dict, Optional
import openai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..models.prompt_analysis import PromptAnalysis


logger = logging.getLogger(__name__)


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

            logger.info(f"Sending prompt analysis request to OpenAI (model: {self.model})")

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

            # Parse the JSON response
            analysis_data = json.loads(content)

            # Validate and create PromptAnalysis object
            analysis = PromptAnalysis(**analysis_data)
            analysis.original_prompt = prompt
            analysis.analysis_timestamp = response.created.isoformat()
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

1. **Tone**: The emotional tone (professional, friendly, enthusiastic, serious, playful, dramatic, calm, energetic)

2. **Style**: Visual and narrative approach (modern, classic, minimalist, cinematic, documentary, animation, photorealistic, artistic)

3. **Narrative Intent**: What the video is trying to achieve (inform, persuade, entertain, demonstrate, etc.)

4. **Narrative Structure**: How the content should be structured (problem_solution, storytelling, demonstration, testimonial, comparison, explanation, celebration, announcement)

5. **Target Audience**: Who the video is for (business, consumers, teens, professionals, families, elders, general)

6. **Key Themes**: Main themes to maintain consistency throughout the video

7. **Key Messages**: Core messages that must be conveyed

8. **Visual Theme**: Overall aesthetic (bright, dark, warm, cool, neutral, vibrant, monochrome, earthy)

9. **Imagery Style**: Type of visual elements (photography, illustration, graphics, text_overlays, product_shots, lifestyle, abstract, realistic)

10. **Color Palette**: Suggest appropriate colors based on the content

11. **Key Elements**: Important elements that should appear in the video

12. **Product Focus**: What product/service is being featured (if any)

13. **Pacing**: Suggested video pacing (slow, moderate, fast)

14. **Music Style**: Recommended background music style

Make your best guess for elements not explicitly mentioned in the prompt. Provide a confidence score (0.0-1.0) based on how well the prompt supports your analysis.

Return your analysis as a valid JSON object matching the PromptAnalysis schema."""

    def _create_user_prompt(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Create the user prompt for analysis"""
        user_prompt = f"Please analyze this video generation prompt and extract structured information for consistent video creation:\n\n{prompt}"

        if context:
            user_prompt += f"\n\nAdditional context: {json.dumps(context)}"

        return user_prompt
