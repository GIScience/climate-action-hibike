import logging
from enum import Enum
from typing import Tuple

import geopandas as gpd
import pandas as pd
from shapely import intersects
from shapely.geometry.multipoint import MultiPoint
from shapely.ops import split

import bikeability.components.path_categories.path_category_filters as filters

log = logging.getLogger(__name__)


class PathCategory(Enum):
    EXCLUSIVE = 'exclusive'
    SHARED_WITH_PEDESTRIANS = 'shared_with_pedestrians'
    SHARED_WITH_MOTORISED_TRAFFIC_WALKING_SPEED = 'shared_with_cars_up_to_15_km/h'
    SHARED_WITH_MOTORISED_TRAFFIC_LOW_SPEED = 'shared_with_cars_up_to_30_km/h'
    SHARED_WITH_MOTORISED_TRAFFIC_MEDIUM_SPEED = 'shared_with_cars_up_to_50_km/h'
    SHARED_WITH_MOTORISED_TRAFFIC_HIGH_SPEED = 'shared_with_cars_above_50_km/h'
    SHARED_WITH_MOTORISED_TRAFFIC_UNKNOWN_SPEED = 'shared_with_cars_unknown_speed'
    REQUIRES_DISMOUNTING = 'requires_dismounting'
    PEDESTRIAN_EXCLUSIVE = 'pedestrian_exclusive'
    NO_ACCESS = 'no_access'
    UNKNOWN = 'unknown'

    @classmethod
    def get_hidden(cls):
        return [cls.PEDESTRIAN_EXCLUSIVE, cls.NO_ACCESS]

    @classmethod
    def get_visible(cls):
        return [category for category in cls if category not in cls.get_hidden()]

    @classmethod
    def get_not_bikeable(cls):
        return [cls.PEDESTRIAN_EXCLUSIVE, cls.NO_ACCESS]

    @classmethod
    def get_bikeable(cls):
        return [category for category in cls if category not in cls.get_not_bikeable()]


def apply_path_category_filters(row: pd.Series) -> PathCategory:
    tags = row['@other_tags']
    speed_limit = filters.parse_maxspeed_tag(tags)
    match tags:
        case x if filters.requires_dismounting(x):
            return PathCategory.REQUIRES_DISMOUNTING
        case x if filters.pedestrian_exclusive(x):
            return PathCategory.PEDESTRIAN_EXCLUSIVE
        case x if filters.restricted_access(x):
            return PathCategory.NO_ACCESS
        case x if filters.designated_exclusive(x):
            return PathCategory.EXCLUSIVE
        case x if filters.designated_shared_with_pedestrians(x):
            return PathCategory.SHARED_WITH_PEDESTRIANS
        case x if filters.shared_with_motorised_traffic_walking_speed(x, speed_limit):
            return PathCategory.SHARED_WITH_MOTORISED_TRAFFIC_WALKING_SPEED
        case x if filters.shared_with_motorised_traffic_low_speed(x, speed_limit):
            return PathCategory.SHARED_WITH_MOTORISED_TRAFFIC_LOW_SPEED
        case x if filters.shared_with_motorised_traffic_medium_speed(x, speed_limit):
            return PathCategory.SHARED_WITH_MOTORISED_TRAFFIC_MEDIUM_SPEED
        case x if filters.shared_with_motorised_traffic_high_speed(x, speed_limit):
            return PathCategory.SHARED_WITH_MOTORISED_TRAFFIC_HIGH_SPEED
        case x if filters.shared_with_motorised_traffic_unknown_speed(x, speed_limit):
            return PathCategory.SHARED_WITH_MOTORISED_TRAFFIC_UNKNOWN_SPEED
        case _:
            return PathCategory.UNKNOWN


def categorize_paths(
    paths_line: gpd.GeoDataFrame, paths_polygon: gpd.GeoDataFrame
) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    log.debug('Categorizing and rating paths')

    if len(paths_line) > 0:
        paths_line['category'] = paths_line.apply(apply_path_category_filters, axis=1)
    if len(paths_polygon) > 0:
        paths_polygon['category'] = paths_polygon.apply(apply_path_category_filters, axis=1)

    return paths_line, paths_polygon


def _aggregate_multiple_crossings_on_one_path(df: pd.DataFrame) -> pd.DataFrame:
    agg = df.iloc[0].copy()
    if len(df) > 1:
        agg.geometry = MultiPoint(list(df.geometry))
    return agg


def _split_paths_around_crossing(
    match_entry: pd.Series, paths_line: gpd.GeoDataFrame, buffer_m: float = 3
) -> pd.DataFrame:
    buffered_crossing_polygon = match_entry.geometry.buffer(buffer_m)
    split_geometry = split(paths_line.loc[match_entry['index_paths']].geometry, buffered_crossing_polygon)
    split_paths = pd.concat(
        [paths_line.loc[match_entry['index_paths']]] * len(split_geometry.geoms), ignore_index=True, axis=1
    ).T
    split_paths['geometry'] = split_geometry.geoms
    split_paths.loc[
        intersects(split_paths.geometry, match_entry.geometry),
        'category',
    ] = PathCategory.REQUIRES_DISMOUNTING
    return split_paths


def recategorise_zebra_crossings(
    paths_line: gpd.GeoDataFrame, zebra_crossing_nodes: gpd.GeoDataFrame
) -> gpd.GeoDataFrame:
    utm_crs = paths_line.estimate_utm_crs()
    paths_line, zebra_crossing_nodes = paths_line.to_crs(utm_crs), zebra_crossing_nodes.to_crs(utm_crs)
    matches = zebra_crossing_nodes.sjoin(
        paths_line[paths_line['category'].isin([PathCategory.EXCLUSIVE, PathCategory.SHARED_WITH_PEDESTRIANS])],
        how='inner',
        lsuffix='zebra_crossings',
        rsuffix='paths',
    ).reset_index()

    if len(matches) > 0:
        matches = matches.groupby('index_paths').apply(_aggregate_multiple_crossings_on_one_path)
        split_paths_all = pd.concat(
            matches.apply(_split_paths_around_crossing, paths_line=paths_line, buffer_m=3, axis=1).to_list()
        )
        # drop original path:
        paths_line = paths_line.drop(matches['index_paths'], axis=0)
        paths_line = gpd.GeoDataFrame(pd.concat([paths_line, split_paths_all], ignore_index=True))
    paths_line = paths_line.set_crs(utm_crs, allow_override=True)
    paths_line = paths_line.to_crs('EPSG:4326')
    return paths_line


def zebra_crossings_filter() -> str:
    return str('geometry:point and type:node and (crossing=zebra or crossing:markings=zebra or crossing_ref=zebra)')
