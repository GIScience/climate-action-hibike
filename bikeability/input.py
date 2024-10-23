import uuid
from typing import Optional, Self, Dict

import geojson_pydantic
import geopandas as gpd
import shapely
from pydantic import BaseModel, Field, field_validator, model_validator
from pyproj import CRS, Transformer
from shapely.ops import transform

from bikeability.utils import PathCategory


class AoiProperties(BaseModel):
    name: str = Field(
        title='Name',
        description='The name of the area of interest i.e. a human readable description.',
        examples=['Heidelberg'],
    )
    id: str = Field(
        title='ID',
        description='A unique identifier of the area of interest.',
        examples=[uuid.uuid4()],
    )


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


class ComputeInputBikeability(BaseModel):
    aoi: geojson_pydantic.Feature[geojson_pydantic.MultiPolygon, AoiProperties] = Field(
        title='Area of Interest Input',
        description='A required area of interest parameter.',
        validate_default=True,
        examples=[
            {
                'type': 'Feature',
                'properties': {'name': 'Heidelberg', 'id': 'Q12345'},
                'geometry': {
                    'type': 'MultiPolygon',
                    'coordinates': [
                        [
                            [
                                [12.3, 48.22],
                                [12.3, 48.34],
                                [12.48, 48.34],
                                [12.48, 48.22],
                                [12.3, 48.22],
                            ]
                        ]
                    ],
                },
            }
        ],
    )

    path_rating: Optional[PathRating] = Field(
        title='Path Rating Mapping',
        description='Qualitative rating for each of the available path categories.',
        examples=[PathRating()],
        default=PathRating(),
    )

    @classmethod
    @field_validator('aoi')
    def assert_aoi_properties_not_null(cls, aoi: geojson_pydantic.Feature) -> geojson_pydantic.Feature:
        assert aoi.properties, 'AOI properties are required.'
        return aoi

    def get_aoi_geom(self) -> shapely.MultiPolygon:
        """Convert the input geojson geometry to a shapely geometry.

        :return: A shapely.MultiPolygon representing the area of interest defined by the user.
        """
        return shapely.geometry.shape(self.aoi.geometry)

    def get_utm_zone(self) -> CRS:
        return gpd.GeoSeries(data=self.get_aoi_geom(), crs='EPSG:4326').estimate_utm_crs()

    def get_buffered_aoi(self) -> shapely.MultiPolygon:
        wgs84 = CRS('EPSG:4326')
        utm = self.get_utm_zone()

        geographic_projection_function = Transformer.from_crs(wgs84, utm, always_xy=True).transform
        wgs84_projection_function = Transformer.from_crs(utm, wgs84, always_xy=True).transform
        projected_aoi = transform(geographic_projection_function, self.get_aoi_geom())
        # changed the distance to a fixed value of 5 km.
        buffered_aoi = projected_aoi.buffer(5000)
        return transform(wgs84_projection_function, buffered_aoi)

    def get_path_rating_mapping(self) -> Dict[PathCategory, float]:
        mapping = self.path_rating.model_dump()
        return {PathCategory(k): v for k, v in mapping.items()}
