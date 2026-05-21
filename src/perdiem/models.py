from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator


class ResponseFormat(str, Enum):
    MARKDOWN = "markdown"
    JSON = "json"


class RatesByCityInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    city: str = Field(
        ...,
        description="Destination city name (e.g., 'San Francisco'). Special characters like periods, apostrophes, and hyphens are handled automatically.",
        min_length=1,
        max_length=100,
    )
    state: str = Field(
        ...,
        description="Two-letter state abbreviation (e.g., 'CA', 'TX')",
        min_length=2,
        max_length=2,
        pattern=r"^[A-Za-z]{2}$",
    )
    year: int = Field(
        ...,
        description="Federal fiscal year (e.g., 2024 covers Oct 2023 – Sep 2024). Up to 3 years available.",
        ge=2010,
        le=2035,
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable",
    )

    @field_validator("state")
    @classmethod
    def uppercase_state(cls, v: str) -> str:
        return v.upper()


class RatesByStateInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    state: str = Field(
        ...,
        description="Two-letter state abbreviation (e.g., 'CA', 'TX')",
        min_length=2,
        max_length=2,
        pattern=r"^[A-Za-z]{2}$",
    )
    year: int = Field(
        ...,
        description="Federal fiscal year",
        ge=2010,
        le=2035,
    )
    limit: Optional[int] = Field(
        default=50,
        description="Maximum number of destinations to return (default: 50, max: 200)",
        ge=1,
        le=200,
    )
    offset: Optional[int] = Field(
        default=0,
        description="Number of destinations to skip for pagination",
        ge=0,
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable",
    )

    @field_validator("state")
    @classmethod
    def uppercase_state(cls, v: str) -> str:
        return v.upper()


class RatesByZipInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    zip_code: str = Field(
        ...,
        description="5-digit ZIP code of the destination (e.g., '94102')",
        pattern=r"^\d{5}$",
    )
    year: int = Field(
        ...,
        description="Federal fiscal year",
        ge=2010,
        le=2035,
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable",
    )


class ConusRatesInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    year: int = Field(
        ...,
        description="Federal fiscal year",
        ge=2010,
        le=2035,
    )
    limit: Optional[int] = Field(
        default=50,
        description="Maximum number of destinations to return (default: 50, max: 200)",
        ge=1,
        le=200,
    )
    offset: Optional[int] = Field(
        default=0,
        description="Number of destinations to skip for pagination",
        ge=0,
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable",
    )


class MieRatesInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    year: int = Field(
        ...,
        description="Federal fiscal year",
        ge=2010,
        le=2035,
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable",
    )


class ZipCodeMappingInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    year: int = Field(
        ...,
        description="Federal fiscal year",
        ge=2010,
        le=2035,
    )
    limit: Optional[int] = Field(
        default=100,
        description="Maximum number of ZIP code mappings to return (default: 100, max: 500)",
        ge=1,
        le=500,
    )
    offset: Optional[int] = Field(
        default=0,
        description="Number of entries to skip for pagination",
        ge=0,
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable",
    )
