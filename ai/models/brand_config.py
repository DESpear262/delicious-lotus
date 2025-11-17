"""
Brand Configuration Models - PR 102: Brand & Metadata Extraction Layer
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator, HttpUrl


class BrandCategory(str, Enum):
    """Primary brand category/industry"""
    CORPORATE = "corporate"
    STARTUP = "startup"
    LUXURY = "luxury"
    RETAIL = "retail"
    HEALTHCARE = "healthcare"
    TECHNOLOGY = "technology"
    FOOD_BEVERAGE = "food_beverage"
    FINANCIAL = "financial"
    EDUCATION = "education"
    NONPROFIT = "nonprofit"
    AUTOMOTIVE = "automotive"
    OTHER = "other"


class ColorPalette(BaseModel):
    """Brand color palette with primary and secondary colors"""
    primary: List[str] = Field(..., description="Primary brand colors (hex codes)", min_items=1)
    secondary: Optional[List[str]] = Field(default=None, description="Secondary/accent colors (hex codes)")
    background: Optional[str] = Field(default=None, description="Background color (hex code)")

    @validator('primary', 'secondary')
    def validate_hex_colors(cls, v):
        """Validate that colors are valid hex codes"""
        if v is None:
            return v
        for color in v:
            if not isinstance(color, str) or not color.startswith('#') or len(color) != 7:
                raise ValueError(f"Invalid hex color format: {color}. Must be in format #RRGGBB")
        return v


class Typography(BaseModel):
    """Brand typography preferences"""
    primary_font: str = Field(..., description="Primary font family name")
    secondary_font: Optional[str] = Field(default=None, description="Secondary font family name")
    font_weights: Optional[List[str]] = Field(default=None, description="Preferred font weights (light, regular, bold, etc.)")


class VisualStyle(BaseModel):
    """Visual style preferences"""
    aesthetic: str = Field(default="modern", description="Overall aesthetic (modern, classic, minimal, etc.)")
    mood: str = Field(default="professional", description="Brand mood/tone (professional, friendly, energetic, etc.)")
    imagery_style: str = Field(default="photorealistic", description="Preferred imagery style")


class BrandAssets(BaseModel):
    """Brand asset references"""
    logo_url: Optional[str] = Field(default=None, description="URL to primary logo")
    logo_variants: Optional[List[str]] = Field(default=None, description="URLs to logo variants")
    icon_url: Optional[str] = Field(default=None, description="URL to brand icon/favicon")
    product_images: Optional[List[str]] = Field(default=None, description="URLs to product images")


class BrandGuidelines(BaseModel):
    """Brand usage guidelines and restrictions"""
    do_not_use: Optional[List[str]] = Field(default=None, description="Elements/brands to avoid")
    style_restrictions: Optional[Dict[str, Any]] = Field(default=None, description="Specific style restrictions")
    content_guidelines: Optional[Dict[str, Any]] = Field(default=None, description="Content creation guidelines")


class BrandConfig(BaseModel):
    """Complete brand configuration schema"""

    # Required fields
    name: str = Field(..., description="Brand/company name", min_length=1, max_length=100)

    # Strongly recommended fields
    category: BrandCategory = Field(default=BrandCategory.OTHER, description="Primary brand category")
    colors: ColorPalette = Field(..., description="Brand color palette")

    # Optional but important fields
    tagline: Optional[str] = Field(default=None, description="Brand tagline or slogan", max_length=200)
    description: Optional[str] = Field(default=None, description="Brief brand description", max_length=500)
    target_audience: Optional[str] = Field(default=None, description="Primary target audience description")
    values: Optional[List[str]] = Field(default=None, description="Core brand values")

    # Visual elements
    typography: Optional[Typography] = Field(default=None, description="Typography preferences")
    visual_style: Optional[VisualStyle] = Field(default=None, description="Visual style preferences")
    assets: Optional[BrandAssets] = Field(default=None, description="Brand asset URLs")

    # Guidelines and restrictions
    guidelines: Optional[BrandGuidelines] = Field(default=None, description="Brand usage guidelines")

    # Extensibility field for unforeseen requirements
    other: Optional[Dict[str, Any]] = Field(default=None, description="Additional brand-specific configuration")

    # Metadata
    version: Optional[str] = Field(default="1.0", description="Brand config version")
    last_updated: Optional[str] = Field(default=None, description="When brand config was last updated")

    @validator('name')
    def validate_brand_name(cls, v):
        """Basic validation for brand name"""
        if not v.strip():
            raise ValueError("Brand name cannot be empty or whitespace only")
        return v.strip()

    @validator('values')
    def validate_values_length(cls, v):
        """Limit number of brand values"""
        if v and len(v) > 10:
            raise ValueError("Cannot have more than 10 brand values")
        return v

    class Config:
        """Pydantic configuration"""
        use_enum_values = True
        json_encoders = {
            # Ensure proper serialization of enums
        }


# Default brand configurations for when brand config is missing
DEFAULT_BRAND_CONFIGS = {
    "corporate": {
        "name": "Corporate Brand",
        "category": "corporate",
        "colors": {
            "primary": ["#1a365d", "#2d3748"],  # Navy and dark gray
            "secondary": ["#4299e1", "#63b3ed"],  # Blue variants
            "background": "#ffffff"
        },
        "typography": {
            "primary_font": "Arial",
            "secondary_font": "Helvetica"
        },
        "visual_style": {
            "aesthetic": "modern",
            "mood": "professional",
            "imagery_style": "photorealistic"
        }
    },

    "startup": {
        "name": "Startup Brand",
        "category": "startup",
        "colors": {
            "primary": ["#667eea", "#764ba2"],  # Purple/blue gradient
            "secondary": ["#f093fb", "#f5576c"],  # Pink/red gradient
            "background": "#ffffff"
        },
        "typography": {
            "primary_font": "Inter",
            "secondary_font": "Roboto"
        },
        "visual_style": {
            "aesthetic": "modern",
            "mood": "energetic",
            "imagery_style": "photorealistic"
        }
    },

    "luxury": {
        "name": "Luxury Brand",
        "category": "luxury",
        "colors": {
            "primary": ["#000000", "#ffffff"],  # Black and white
            "secondary": ["#ffd700", "#c0c0c0"],  # Gold and silver
            "background": "#f8f8f8"
        },
        "typography": {
            "primary_font": "Times New Roman",
            "secondary_font": "Garamond"
        },
        "visual_style": {
            "aesthetic": "elegant",
            "mood": "sophisticated",
            "imagery_style": "photorealistic"
        }
    },

    "automotive": {
        "name": "Automotive Brand",
        "category": "automotive",
        "colors": {
            "primary": ["#FF0000", "#000000"],  # Red and black (classic automotive)
            "secondary": ["#C0C0C0", "#FFFFFF"],  # Silver and white
            "background": "#f0f0f0"
        },
        "typography": {
            "primary_font": "Helvetica",
            "secondary_font": "Arial"
        },
        "visual_style": {
            "aesthetic": "modern",
            "mood": "powerful",
            "imagery_style": "photorealistic"
        }
    }
}


def get_default_brand_config(category: str = "corporate") -> BrandConfig:
    """Get a default brand configuration for a given category"""
    config_data = DEFAULT_BRAND_CONFIGS.get(category, DEFAULT_BRAND_CONFIGS["corporate"])
    return BrandConfig(**config_data)
