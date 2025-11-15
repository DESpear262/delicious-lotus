# AI Processing Backend - BLOCK A

**Prompt Processing & Enhancement**

This directory contains the AI processing services for the video generation pipeline, focusing on prompt analysis and enhancement to ensure consistent, high-quality video output.

## Architecture Overview

```
ai/
├── services/           # Business logic services
│   └── prompt_analysis_service.py
├── models/            # AI-specific data models
│   └── prompt_analysis.py
├── core/              # Core utilities
│   └── openai_client.py
├── tests/             # Unit and integration tests
│   └── test_prompt_analysis.py
├── requirements.txt   # Python dependencies
└── README.md
```

## Key Components

### PromptAnalysisService
- **Purpose**: Analyzes video generation prompts to extract structured metadata
- **Input**: Raw user prompt text
- **Output**: Comprehensive analysis including tone, style, themes, visual elements
- **Integration**: Called from the FastAPI generation endpoint

### Analysis Features
- **Tone Detection**: Professional, friendly, enthusiastic, etc.
- **Style Classification**: Modern, classic, cinematic, etc.
- **Theme Extraction**: Key themes for narrative consistency
- **Visual Guidelines**: Color palettes, imagery styles, pacing
- **Audience Targeting**: Business, consumers, teens, etc.
- **Narrative Structure**: Problem-solution, storytelling, demonstration, etc.

### OpenAI Integration
- Uses GPT-4o-mini for analysis
- Implements retry logic with exponential backoff
- Structured JSON output for reliable parsing
- Comprehensive error handling

## Usage

### Basic Analysis
```python
from ai.services.prompt_analysis_service import PromptAnalysisService
from ai.models.prompt_analysis import AnalysisRequest

service = PromptAnalysisService(openai_api_key="your_key", use_mock=True)
request = AnalysisRequest(prompt="Create a professional business video...")
response = await service.analyze_prompt(request)

print(f"Tone: {response.analysis.tone}")
print(f"Style: {response.analysis.style}")
print(f"Confidence: {response.analysis.confidence_score}")
```

### Integration with FastAPI
The service is automatically integrated into the `/api/v1/generations` endpoint:

```python
# In create_generation endpoint
analysis_service = PromptAnalysisService(openai_api_key=config.OPENAI_KEY, use_mock=False)
analysis_request = AnalysisRequest(prompt=generation_request.prompt)
analysis_response = await analysis_service.analyze_prompt(analysis_request)

# Analysis results are stored with generation metadata
generation_data["prompt_analysis"] = analysis_response.analysis.dict()
```

## Testing

Run tests with:
```bash
cd ai
python -m pytest tests/ -v
```

Tests include:
- Mock response validation
- Different prompt types (business, creative, minimalist)
- Processing time tracking
- Schema compliance
- Error handling

## Configuration

### Environment Variables
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### Service Configuration
```python
# Production
service = PromptAnalysisService(openai_api_key=os.getenv("OPENAI_API_KEY"), use_mock=False)

# Testing/Development
service = PromptAnalysisService(openai_api_key="dummy", use_mock=True)
```

## Output Schema

The analysis produces a comprehensive `PromptAnalysis` object with:

- **Narrative Elements**: tone, intent, structure, audience
- **Thematic Elements**: key themes, messages, pacing
- **Visual Elements**: style, theme, colors, imagery
- **Content Elements**: key elements, product focus
- **Technical Guidance**: music style, pacing
- **Quality Metrics**: confidence score, analysis notes

## Future Enhancements

See `TODO.md` in the project root for planned improvements including:
- Caching for performance
- Progressive analysis fallbacks
- User feedback integration
- Multi-language support

## Dependencies

- `openai>=1.0.0`: OpenAI API client
- `tenacity>=8.2.0`: Retry logic
- `pydantic>=2.5.0`: Data validation
- `pytest`: Testing framework

Install with:
```bash
pip install -r requirements.txt
```
