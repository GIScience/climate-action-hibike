import logging
from enum import Enum
from typing import Dict, Callable, Any, Tuple, Union
from urllib.parse import parse_qsl

import geopandas as gpd
import matplotlib
import pandas as pd
import shapely
from matplotlib.colors import to_hex, Normalize
from ohsome import OhsomeClient
from pydantic_extra_types.color import Color
from requests import PreparedRequest
from shapely import LineString

log = logging.getLogger(__name__)


class PathCategory(Enum):
    DESIGNATED_EXCLUSIVE = 'designated_exclusive'
    DESIGNATED_SHARED_WITH_PEDESTRIANS = 'designated_shared_with_pedestrians'
    SHARED_WITH_MOTORISED_TRAFFIC_WALKING_SPEED = 'shared_with_motorised_traffic_walking_speed'
    SHARED_WITH_MOTORISED_TRAFFIC_LOW_SPEED = 'shared_with_motorised_traffic_low_speed'
    SHARED_WITH_MOTORISED_TRAFFIC_MEDIUM_SPEED = 'shared_with_motorised_traffic_medium_speed'
    SHARED_WITH_MOTORISED_TRAFFIC_HIGH_SPEED = 'shared_with_motorised_traffic_high_speed'
    REQUIRES_DISMOUNTING = 'requires_dismounting'
    NOT_BIKEABLE = 'not_bikeable'
    PEDESTRIAN_EXCLUSIVE = 'pedestrian_exclusive'
    RESTRICTED_ACCESS = 'restricted_access'
    UNKNOWN = 'unknown'

    @classmethod
    def get_hidden(cls):
        return [cls.PEDESTRIAN_EXCLUSIVE, cls.RESTRICTED_ACCESS]

    @classmethod
    def get_visible(cls):
        return [category for category in cls if category not in cls.get_hidden()]


class PathCategoryFilters:
    def __init__(self):
        self.potential_bikeable_highway_values = (
            'primary',
            'primary_link',
            'secondary',
            'secondary_link',
            'tertiary',
            'tertiary_link',
            'road',
            'unclassified',
            'residential',
            'track',
            'living_street',
            'service',
        )

    def not_bikeable(self, d: Dict) -> bool:
        return (
            d.get('highway')
            not in [*self.potential_bikeable_highway_values, 'pedestrian', 'path', 'cycleway', 'footway', 'steps']
            or d.get('bicycle') in ['no', 'private', 'use_sidepath', 'discouraged', 'destination']
            or d.get('motorroad') == 'yes'
        )

    def _shared_with_pedestrians(self, d: Dict) -> bool:
        return (d.get('foot') in ['yes', 'designated'] and d.get('segregated') != 'yes') or (
            d.get('highway') in ['footway', 'pedestrian'] and d.get('foot') is None
        )

    def designated_shared_with_pedestrians(self, d: Dict) -> bool:
        return (
            d.get('highway') in ['cycleway', 'path', 'footway', 'pedestrian'] and self._shared_with_pedestrians(d)
        ) or d.get('highway') == 'track'

    def designated_exclusive(self, d: Dict) -> bool:
        return d.get('highway') in ['cycleway', 'path', 'footway', 'pedestrian'] and not self._shared_with_pedestrians(
            d
        )

    def shared_with_motorised_traffic_walking_speed(self, d: Dict) -> bool:
        return d.get('highway') in ['living_street', 'service'] or d.get('maxspeed') in [
            '5',
            '6',
            '7',
            '8',
            '10',
            '15',
            'walk',
        ]

    def shared_with_motorised_traffic_low_speed(self, d: Dict) -> bool:
        return d.get('maxspeed') in ['20', '25', '30'] or d.get('zone:maxspeed') in ['DE:30', '30']

    def shared_with_motorised_traffic_medium_speed(self, d: Dict) -> bool:
        return (
            d.get('maxspeed') in ['35', '40', '45', '50', 'DE:urban', 'AT:urban']
            or d.get('maxspeed:forward') in ['35', '40', '45', '50', 'DE:urban', 'AT:urban']
            or d.get('maxspeed:type') == ['DE:urban', 'AT:urban']
            or d.get('zone:maxspeed') == ['DE:urban', 'AT:urban']
            or d.get('highway') == 'residential'
        )

    def shared_with_motorised_traffic_high_speed(self, d: Dict) -> bool:
        return (
            d.get('maxspeed') in ['60', '70', '80', '90', '100', 'DE:rural', 'AT:rural']
            or d.get('maxspeed:forward') in ['60', '70', '80', '90', '100', 'DE:rural', 'AT:rural']
            or d.get('maxspeed:type') == ['DE:rural', 'AT:rural']
            or d.get('zone:maxspeed') == ['DE:rural', 'AT:rural']
        ) or d.get('highway') == 'unclassified'

    def requires_dismounting(self, d: Dict) -> bool:
        return (
            d.get('bicycle') == 'dismount'
            or '1012-32' in d.get('traffic_sign', 'no')
            or (
                d.get('highway') == 'steps'
                and (
                    d.get('ramp:bicycle') == 'yes' or d.get('ramp') == 'yes' or d.get('ramp:wheelchair') == 'yes',
                    d.get('ramp:stroller') == 'yes',
                )
            )
            or d.get('railway') == 'platform'
            or d.get('ford') is not None
        )

    def pedestrian_exclusive(self, d: Dict) -> bool:
        return d.get('highway') in ['footway', 'pedestrian'] and (
            d.get('bicycle')
            not in [
                'yes',
                'designated',
                'dismount',
            ]
            or d.get('bicycle:conditional') is not None
        )

    def restricted_access(self, d: Dict) -> bool:
        return d.get('access') in ['no', 'private', 'permit', 'military', 'delivery', 'customers', 'emergency']


class SmoothnessCategory(Enum):
    EXCELLENT = 'excellent'
    GOOD = 'good'
    INTERMEDIATE = 'intermediate'
    BAD = 'bad'
    TOO_BUMPY_TO_RIDE = 'too_bumpy_to_ride'
    UNKNOWN = 'unknown'

    @classmethod
    def get_hidden(cls):
        return []

    @classmethod
    def get_visible(cls):
        return [category for category in cls if category not in cls.get_hidden()]


class PathSmoothnessFilters:
    def too_bumpy_to_ride(self, d: Dict) -> bool:
        return d.get('smoothness') in ['very_bad', 'horrible', 'very_horrible', 'impassable']

    def bad(self, d: Dict) -> bool:
        return d.get('smoothness') == 'bad'

    def intermediate(self, d: Dict) -> bool:
        return d.get('smoothness') == 'intermediate'

    def good(self, d: Dict) -> bool:
        return d.get('smoothness') == 'good'

    def excellent(self, d: Dict) -> bool:
        return d.get('smoothness') == 'excellent'


def fetch_osm_data(aoi: shapely.MultiPolygon, osm_filter: str, ohsome: OhsomeClient) -> gpd.GeoDataFrame:
    elements = ohsome.elements.geometry.post(
        bpolys=aoi, clipGeometry=True, properties='tags', filter=osm_filter
    ).as_dataframe()
    elements = elements.reset_index(drop=True)
    return elements[['geometry', '@other_tags']]


def apply_path_category_filters(row: pd.Series):
    filters = PathCategoryFilters()

    match row['@other_tags']:
        case x if filters.restricted_access(x):
            return PathCategory.RESTRICTED_ACCESS
        case x if filters.pedestrian_exclusive(x):
            return PathCategory.PEDESTRIAN_EXCLUSIVE
        case x if filters.requires_dismounting(x):
            return PathCategory.REQUIRES_DISMOUNTING
        case x if filters.not_bikeable(x):
            return PathCategory.NOT_BIKEABLE
        case x if filters.designated_exclusive(x):
            return PathCategory.DESIGNATED_EXCLUSIVE
        case x if filters.designated_shared_with_pedestrians(x):
            return PathCategory.DESIGNATED_SHARED_WITH_PEDESTRIANS
        case x if filters.shared_with_motorised_traffic_walking_speed(x):
            return PathCategory.SHARED_WITH_MOTORISED_TRAFFIC_WALKING_SPEED
        case x if filters.shared_with_motorised_traffic_low_speed(x):
            return PathCategory.SHARED_WITH_MOTORISED_TRAFFIC_LOW_SPEED
        case x if filters.shared_with_motorised_traffic_medium_speed(x):
            return PathCategory.SHARED_WITH_MOTORISED_TRAFFIC_MEDIUM_SPEED
        case x if filters.shared_with_motorised_traffic_high_speed(x):
            return PathCategory.SHARED_WITH_MOTORISED_TRAFFIC_HIGH_SPEED
        case _:
            return PathCategory.UNKNOWN


def apply_path_smoothness_filters(row: pd.Series):
    filters = PathSmoothnessFilters()

    match row['@other_tags']:
        case x if filters.too_bumpy_to_ride(x):
            return SmoothnessCategory.TOO_BUMPY_TO_RIDE
        case x if filters.bad(x):
            return SmoothnessCategory.BAD
        case x if filters.intermediate(x):
            return SmoothnessCategory.INTERMEDIATE
        case x if filters.good(x):
            return SmoothnessCategory.GOOD
        case x if filters.excellent(x):
            return SmoothnessCategory.EXCELLENT
        case _:
            return SmoothnessCategory.UNKNOWN


def fix_geometry_collection(
    geom: shapely.Geometry,
) -> Union[shapely.LineString, shapely.MultiLineString]:
    # Hack due to https://github.com/GIScience/oshdb/issues/463
    if geom.geom_type == 'GeometryCollection':
        inner_geoms = []
        for inner_geom in geom.geoms:
            if inner_geom.geom_type in ('LineString', 'MultiLineString'):
                inner_geoms.append(inner_geom)
        geom = shapely.union_all(inner_geoms)

    if geom.geom_type in ('LineString', 'MultiLineString'):
        return geom
    else:
        return LineString()


def get_qualitative_color(category: Union[PathCategory, SmoothnessCategory], cmap_name: str) -> Color:
    norm = Normalize(0, 1)
    cmap = matplotlib.cm.ScalarMappable(norm=norm, cmap=cmap_name).get_cmap()
    cmap.set_under('#808080')

    category_norm = {name: idx / (len(category.get_visible()) - 1) for idx, name in enumerate(category.get_visible())}

    if category == PathCategory.UNKNOWN or category == SmoothnessCategory.UNKNOWN:
        return Color(to_hex(cmap(-9999)))
    else:
        return Color(to_hex(cmap(category_norm[category])))


def get_color(values: pd.Series, cmap_name: str = 'RdYlGn') -> pd.Series:
    norm = Normalize(0, 1)
    cmap = matplotlib.cm.ScalarMappable(norm=norm, cmap=cmap_name).get_cmap()
    cmap.set_under('#808080')
    return values.apply(lambda v: Color(to_hex(cmap(v))))


def get_single_color(rating: float, cmap_name: str = 'RdYlGn') -> Color:
    norm = Normalize(0, 1)
    cmap = matplotlib.cm.ScalarMappable(norm=norm, cmap=cmap_name).get_cmap()
    cmap.set_under('#808080')
    return Color(to_hex(cmap(rating)))


def filter_start_matcher(filter_start: str) -> Callable[..., Any]:
    def match(request: PreparedRequest) -> Tuple[bool, str]:
        request_body = request.body
        qsl_body = dict(parse_qsl(request_body, keep_blank_values=False)) if request_body else {}

        if request_body is None:
            return False, 'The given request has no body'
        elif qsl_body.get('filter') is None:
            return False, 'Filter parameter not set'
        else:
            valid = qsl_body.get('filter', '').startswith(filter_start)
            return (True, '') if valid else (False, f'The filter parameter does not start with {filter_start}')

    return match


def ohsome_filter(geometry_type: str) -> str:
    return str(
        f'geometry:{geometry_type} and '
        '(highway=* or railway=platform) and not '
        '(cycleway=separate or cycleway:both=separate or '
        '(cycleway:right=separate and cycleway:left=separate))'
    )


pathratings_legend_fix = {
    'shared_with_motorised_traffic_walking_speed': 'shared_with_motorised_traffic_walking_speed_(<=15_km/h)',
    'shared_with_motorised_traffic_low_speed': 'shared_with_motorised_traffic_low_speed_(<=30_km/h)',
    'shared_with_motorised_traffic_medium_speed': 'shared_with_motorised_traffic_medium_speed_(<=50_km/h)',
    'shared_with_motorised_traffic_high_speed': 'shared_with_motorised_traffic_high_speed_(<=100_km/h)',
}
