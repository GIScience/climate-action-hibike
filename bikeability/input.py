from typing import Optional, Self, Dict

from pydantic import BaseModel, Field, model_validator

from bikeability.indicators.path_categories import PathCategory
from bikeability.indicators.smoothness import SmoothnessCategory
from bikeability.indicators.dooring_risk import DooringRiskCategory


class PathRating(BaseModel):
    designated_exclusive: float = Field(
        title='Designated Exclusive Path Rating',
        description='Qualitative rating (between 0..1) of paths that are designated for cycling and not shared with pedestrians.',
        ge=0,
        le=1,
        examples=[1.0],
        default=1.0,
    )

    designated_shared_with_pedestrians: float = Field(
        title='Designated Shared with Pedestrians Path Rating',
        description='Qualitative rating (between 0..1) of paths that are designated for cycling and shared with pedestrians.',
        ge=0,
        le=1,
        examples=[0.8],
        default=0.8,
    )

    shared_with_motorised_traffic_walking_speed: float = Field(
        title='Shared with Motorised Traffic Walking Speed Path Rating',
        description='Qualitative rating (between 0..1) of paths that are shared with motorised traffic with speed limits of roughly walking speed (<=15 km/h).',
        ge=0,
        le=1,
        examples=[0.8],
        default=0.8,
    )

    shared_with_motorised_traffic_low_speed: float = Field(
        title='Shared with Motorised Traffic Low Speed Path Rating',
        description='Qualitative rating (between 0..1) of paths that are shared with motorised traffic with max speed limits of 30 km/h.',
        ge=0,
        le=1,
        examples=[0.6],
        default=0.6,
    )

    shared_with_motorised_traffic_medium_speed: float = Field(
        title='Shared with Motorised Traffic Medium Speed Path Rating',
        description='Qualitative rating (between 0..1) of paths that are shared with motorised traffic with max speed limits of 50 km/h.',
        ge=0,
        le=1,
        examples=[0.4],
        default=0.4,
    )

    shared_with_motorised_traffic_high_speed: float = Field(
        title='Shared with Motorised Traffic High Speed Path Rating',
        description='Qualitative rating (between 0..1) of paths that are shared with motorised traffic with max speed limits of 100 km/h.',
        ge=0,
        le=1,
        examples=[0.1],
        default=0.1,
    )

    requires_dismounting: float = Field(
        title='Requires Dismounting Path Rating',
        description='Qualitative rating (between 0..1) of paths where cyclists must dismount.',
        ge=0,
        le=1,
        examples=[0.05],
        default=0.05,
    )

    not_bikeable: float = Field(
        title='Not Bikeable Path Rating',
        description='Qualitative rating (between 0..1) of paths that are not bikeable.',
        ge=0,
        le=1,
        examples=[0.0],
        default=0.0,
    )

    unknown: float = Field(
        title='Unknown Path Rating',
        description='Qualitative (between 0..1) rating of paths that are in principle bikeable but are could not be categorised (default -9999, which is out of scale)',
        ge=0,
        le=1,
        examples=[0.0],
        default=-9999,
    )

    pedestrian_exclusive: float = Field(
        title='Pedestrian Exclusive Path Rating',
        description='Shadow category (not used in Bikeable Path Category Indicator)',
        ge=0,
        le=1,
        examples=[0.0],
        default=-9999,
    )

    restricted_access: float = Field(
        title='Restricted Access Path Rating',
        description='Shadow category (not used in Bikeable Path Category Indicator)',
        ge=0,
        le=1,
        examples=[0.0],
        default=-9999,
    )

    @model_validator(mode='after')
    def check_order(self) -> Self:
        assert (
            0
            <= self.not_bikeable
            <= self.requires_dismounting
            <= self.shared_with_motorised_traffic_high_speed
            <= self.shared_with_motorised_traffic_medium_speed
            <= self.shared_with_motorised_traffic_low_speed
            <= self.shared_with_motorised_traffic_walking_speed
            <= self.designated_shared_with_pedestrians
            <= self.designated_exclusive
            <= 1
        ), 'Qualitative rating must respect semantic order of categories!'
        return self


class PathSmoothnessRating(BaseModel):
    excellent: float = Field(
        title='Excellent Smoothness Rating',
        description='Qualitative rating (between 0..1) of paths with excellent smoothness.',
        ge=0,
        le=1,
        examples=[1.0],
        default=1.0,
    )

    good: float = Field(
        title='Good Smoothness Rating',
        description='Qualitative rating (between 0..1) of paths with good smoothness.',
        ge=0,
        le=1,
        examples=[0.75],
        default=0.75,
    )

    intermediate: float = Field(
        title='Intermediate Smoothness Rating',
        description='Qualitative rating (between 0..1) of paths with intermediate smoothness.',
        ge=0,
        le=1,
        examples=[0.5],
        default=0.5,
    )

    bad: float = Field(
        title='Bad Smoothness Rating',
        description='Qualitative rating (between 0..1) of paths with bad smoothness.',
        ge=0,
        le=1,
        examples=[0.25],
        default=0.25,
    )

    too_bumpy_to_ride: float = Field(
        title='Too Bumpy to Ride Smoothness Rating',
        description='Qualitative rating (between 0..1) of paths with very bad or worse smoothness.',
        ge=0,
        le=1,
        examples=[0.0],
        default=0.0,
    )

    unknown: float = Field(
        title='Unknown Smoothness Rating',
        description='Qualitative (between 0..1) rating of paths that could not be categorised (default -9999, which is out of scale)',
        ge=0,
        le=1,
        examples=[0.0],
        default=-9999,
    )

    @model_validator(mode='after')
    def check_order(self) -> Self:
        assert (
            0 <= self.too_bumpy_to_ride <= self.bad <= self.intermediate <= self.good <= self.excellent <= 1
        ), 'Qualitative rating must respect semantic order of categories!'
        return self


class PathDooringRiskRating(BaseModel):
    safe_route: float = Field(
        title='Safe Route Dooring Risk Rating',
        description='Qualitative rating (between 0..1) of paths with no or significantly less risk of dooring.',
        ge=0,
        le=1,
        examples=[1.0],
        default=1.0,
    )

    risk_of_dooring: float = Field(
        title='Risk of Dooring Risk Rating',
        description='Qualitative rating (between 0..1) of paths with a high risk of dooring.',
        ge=0,
        le=1,
        examples=[0.0],
        default=0.0,
    )

    unknown: float = Field(
        title='Unknown Dooring Risk Rating',
        description='Qualitative (between 0..1) rating of paths whose dooring risk could not be determined (default -9999, which is out of scale)',
        ge=0,
        le=1,
        examples=[0.0],
        default=-9999,
    )

    @model_validator(mode='after')
    def check_order(self) -> Self:
        assert (
            0 <= self.risk_of_dooring <= self.safe_route <= 1
        ), 'Qualitative rating must respect semantic order of categories!'
        return self


class ComputeInputBikeability(BaseModel):
    path_rating: Optional[PathRating] = Field(
        title='Path Rating Mapping',
        description='Qualitative rating for each of the available path categories.',
        examples=[PathRating()],
        default=PathRating(),
    )

    smoothness_rating: Optional[PathSmoothnessRating] = Field(
        title='Path Smoothness Mapping',
        description='Qualitative rating for each available smoothness category',
        examples=[PathSmoothnessRating()],
        default=PathSmoothnessRating(),
    )

    dooring_risk_rating: Optional[PathDooringRiskRating] = Field(
        title='Path Dooring Risk Rating',
        description='Qualitative rating for dooring risk',
        examples=[PathDooringRiskRating()],
        default=PathDooringRiskRating(),
    )

    def get_path_rating_mapping(self) -> Dict[PathCategory, float]:
        mapping = self.path_rating.model_dump()
        return {PathCategory(k): v for k, v in mapping.items()}

    def get_path_smoothness_mapping(self) -> Dict[SmoothnessCategory, float]:
        mapping = self.smoothness_rating.model_dump()
        return {SmoothnessCategory(k): v for k, v in mapping.items()}

    def get_path_dooring_mapping(self) -> Dict[DooringRiskCategory, float]:
        mapping = self.dooring_risk_rating.model_dump()
        return {DooringRiskCategory(k): v for k, v in mapping.items()}
