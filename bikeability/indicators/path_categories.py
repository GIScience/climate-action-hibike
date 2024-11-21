from enum import Enum
import logging
from typing import Dict, Tuple

import geopandas as gpd

import pandas as pd


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

    @classmethod
    def get_not_bikeable(cls):
        return [cls.NOT_BIKEABLE, cls.PEDESTRIAN_EXCLUSIVE, cls.RESTRICTED_ACCESS]

    @classmethod
    def get_bikeable(cls):
        return [category for category in cls if category not in cls.get_not_bikeable()]


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


def apply_path_category_filters(row: pd.Series) -> PathCategory:
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


def categorize_paths(
    paths_line: gpd.GeoDataFrame, paths_polygon: gpd.GeoDataFrame, rating_map: Dict[PathCategory, float]
) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    log.debug('Categorizing and rating paths')

    paths_line['category'] = paths_line.apply(apply_path_category_filters, axis=1)
    paths_polygon['category'] = paths_polygon.apply(apply_path_category_filters, axis=1)

    paths_line['rating'] = paths_line.category.apply(lambda category: rating_map[category])
    paths_polygon['rating'] = paths_polygon.category.apply(lambda category: rating_map[category])

    return paths_line, paths_polygon


pathratings_legend_fix = {
    'shared_with_motorised_traffic_walking_speed': 'shared_with_motorised_traffic_walking_speed_(<=15_km/h)',
    'shared_with_motorised_traffic_low_speed': 'shared_with_motorised_traffic_low_speed_(<=30_km/h)',
    'shared_with_motorised_traffic_medium_speed': 'shared_with_motorised_traffic_medium_speed_(<=50_km/h)',
    'shared_with_motorised_traffic_high_speed': 'shared_with_motorised_traffic_high_speed_(<=100_km/h)',
}
