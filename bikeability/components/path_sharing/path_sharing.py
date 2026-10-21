import logging
from typing import Self

import geopandas as gpd
import matplotlib
import pandas as pd
from matplotlib.colors import Colormap, Normalize, to_hex
from pydantic_extra_types import Color

import bikeability.components.path_sharing.path_sharing_filters as filters
from bikeability.components.utils.colors import ColorCategories

log = logging.getLogger(__name__)


class PathSharing(ColorCategories):
    EXCLUSIVE = 'bike_exclusive'
    SHARED_WITH_PEDESTRIANS = 'pedestrians'
    SHARED_WITH_MOTORISED_TRAFFIC_LOW_SPEED = 'cars_up_to_30_km/h'
    SHARED_WITH_MOTORISED_TRAFFIC_MEDIUM_SPEED = 'cars_up_to_50_km/h'
    SHARED_WITH_MOTORISED_TRAFFIC_HIGH_SPEED = 'cars_above_50_km/h'
    SHARED_WITH_MOTORISED_TRAFFIC_UNKNOWN_SPEED = 'cars_unknown_speed'
    REQUIRES_DISMOUNTING = 'requires_dismounting'
    PEDESTRIAN_EXCLUSIVE = 'pedestrian_exclusive'
    NO_ACCESS = 'bike_not_allowed'
    UNKNOWN = 'unknown'

    @classmethod
    def get_hidden(cls) -> list[Self]:
        return [cls.PEDESTRIAN_EXCLUSIVE, cls.NO_ACCESS]

    @classmethod
    def get_visible(cls) -> list[Self]:
        return [category for category in cls if category not in cls.get_hidden()]

    @classmethod
    def get_not_bikeable(cls) -> list[Self]:
        return [cls.PEDESTRIAN_EXCLUSIVE, cls.NO_ACCESS, cls.REQUIRES_DISMOUNTING]

    @classmethod
    def get_bikeable(cls) -> list[Self]:
        bikeable_categories = [category for category in cls if category not in cls.get_not_bikeable()]
        bikeable_categories.remove(cls.UNKNOWN)
        bikeable_categories.insert(int(len(bikeable_categories) / 2), cls.UNKNOWN)
        return bikeable_categories

    @classmethod
    def get_qualitative_colors(cls, colormap: str | Colormap) -> dict[str | float, Color]:
        # if you try to change this, it needs fiddling to keep useful colours with our chosen colour map
        considered_colors = cls.get_bikeable()
        considered_colors.remove(cls.SHARED_WITH_MOTORISED_TRAFFIC_UNKNOWN_SPEED)

        norm = Normalize(0, 1)
        if isinstance(colormap, str):
            colormap: Colormap = matplotlib.cm.ScalarMappable(norm=norm, cmap=colormap).get_cmap()

        category_norm = {
            name.value: Color(to_hex(colormap(idx / (len(considered_colors) - 1))))
            for idx, name in enumerate(considered_colors)
        }

        category_norm[cls.SHARED_WITH_MOTORISED_TRAFFIC_UNKNOWN_SPEED.value] = Color('#fb325a')
        category_norm[cls.REQUIRES_DISMOUNTING.value] = Color('#f47a7a')
        category_norm.pop(cls.UNKNOWN.value)
        category_norm[cls.UNKNOWN.value] = Color('#808080')

        return category_norm


def apply_path_sharing_filters(row: pd.Series) -> PathSharing:
    tags = row['osm_tags']
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
