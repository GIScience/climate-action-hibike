import logging
from enum import Enum

import geopandas as gpd
import pandas as pd

import bikeability.components.path_sharing.path_sharing_filters as filters

log = logging.getLogger(__name__)


class PathSharing(Enum):
    EXCLUSIVE = 'bike_exclusive'
    SHARED_WITH_PEDESTRIANS = 'pedestrians'
    SHARED_WITH_MOTORISED_TRAFFIC_WALKING_SPEED = 'cars_up_to_15_km/h'
    SHARED_WITH_MOTORISED_TRAFFIC_LOW_SPEED = 'cars_up_to_30_km/h'
    SHARED_WITH_MOTORISED_TRAFFIC_MEDIUM_SPEED = 'cars_up_to_50_km/h'
    SHARED_WITH_MOTORISED_TRAFFIC_HIGH_SPEED = 'cars_above_50_km/h'
    SHARED_WITH_MOTORISED_TRAFFIC_UNKNOWN_SPEED = 'cars_unknown_speed'
    REQUIRES_DISMOUNTING = 'requires_dismounting'
    PEDESTRIAN_EXCLUSIVE = 'pedestrian_exclusive'
    NO_ACCESS = 'bike_not_allowed'
    UNKNOWN = 'unknown'

    @classmethod
    def get_hidden(cls):
        return [cls.PEDESTRIAN_EXCLUSIVE, cls.NO_ACCESS]

    @classmethod
    def get_visible(cls):
        return [category for category in cls if category not in cls.get_hidden()]

    @classmethod
    def get_not_bikeable(cls):
        return [cls.PEDESTRIAN_EXCLUSIVE, cls.NO_ACCESS, cls.REQUIRES_DISMOUNTING]

    @classmethod
    def get_bikeable(cls):
        return [category for category in cls if category not in cls.get_not_bikeable()]


def apply_path_sharing_filters(row: pd.Series) -> PathSharing:
    tags = row['@other_tags']
    speed_limit = filters.parse_maxspeed_tag(tags)
    match tags:
        case x if filters.no_access(x):
            return PathSharing.NO_ACCESS
        case x if filters.requires_dismounting(x):
            return PathSharing.REQUIRES_DISMOUNTING
        case x if filters.pedestrian_exclusive(x):
            return PathSharing.PEDESTRIAN_EXCLUSIVE
        case x if filters.no_bike_access(x):
            return PathSharing.NO_ACCESS
        case x if filters.designated_exclusive(x):
            return PathSharing.EXCLUSIVE
        case x if filters.designated_shared_with_pedestrians(x):
            return PathSharing.SHARED_WITH_PEDESTRIANS
        case x if filters.shared_with_motorised_traffic_walking_speed(x, speed_limit):
            return PathSharing.SHARED_WITH_MOTORISED_TRAFFIC_WALKING_SPEED
        case x if filters.shared_with_motorised_traffic_low_speed(x, speed_limit):
            return PathSharing.SHARED_WITH_MOTORISED_TRAFFIC_LOW_SPEED
        case x if filters.shared_with_motorised_traffic_medium_speed(x, speed_limit):
            return PathSharing.SHARED_WITH_MOTORISED_TRAFFIC_MEDIUM_SPEED
        case x if filters.shared_with_motorised_traffic_high_speed(x, speed_limit):
            return PathSharing.SHARED_WITH_MOTORISED_TRAFFIC_HIGH_SPEED
        case x if filters.shared_with_motorised_traffic_unknown_speed(x, speed_limit):
            return PathSharing.SHARED_WITH_MOTORISED_TRAFFIC_UNKNOWN_SPEED
        case _:
            return PathSharing.UNKNOWN


def categorize_paths(paths: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    log.debug('Categorizing path sharing')

    paths['path_sharing'] = paths.apply(apply_path_sharing_filters, axis=1)

    return paths
