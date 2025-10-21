from enum import Enum

from pydantic import BaseModel, Field


class BikeabilityIndicators(Enum):
    DETOUR_FACTORS = 'Detour Factors'
    NATURALNESS = 'Greenness'


class ComputeInputBikeability(BaseModel):
    optional_indicators: set[BikeabilityIndicators] = Field(
        title='Optional indicators',
        description='Computing these indicators for large areas may exceed '
        'the time limit for individual assessments in the Climate Action Navigator.',
        examples=[set()],
        default=set(),
    )
