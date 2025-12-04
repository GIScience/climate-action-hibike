import logging
from enum import Enum

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


def categorize_paths(paths: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    log.debug('Categorizing and rating paths')

    paths['category'] = paths.apply(apply_path_category_filters, axis=1)

    return paths


def _aggregate_multiple_crossings_on_one_path(df: pd.DataFrame) -> pd.DataFrame:
    agg = df.iloc[0].copy()
    if len(df) > 1:
        agg.geometry = MultiPoint(list(df.geometry))
    return agg


def _split_paths_around_crossing(
    match_entry: pd.Series, line_paths: gpd.GeoDataFrame, buffer_m: float = 3
) -> pd.DataFrame:
    buffered_crossing_polygon = match_entry.geometry.buffer(buffer_m)
    split_geometry = split(line_paths.loc[match_entry['index_paths']].geometry, buffered_crossing_polygon)
    split_paths = pd.concat(
        [line_paths.loc[match_entry['index_paths']]] * len(split_geometry.geoms), ignore_index=True, axis=1
    ).T
    split_paths['geometry'] = split_geometry.geoms
    split_paths.loc[
        intersects(split_paths.geometry, match_entry.geometry),
        'category',
    ] = PathCategory.REQUIRES_DISMOUNTING
    return split_paths


def recategorise_zebra_crossings(paths: gpd.GeoDataFrame, zebra_crossing_nodes: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    polygon_paths = paths[paths.geom_type.isin(['Polygon', 'MultiPolygon'])]
    line_paths = paths[paths.geom_type.isin(['LineString', 'MultiLineString'])]

    if line_paths.empty:
        return polygon_paths

    utm_crs = line_paths.estimate_utm_crs()
    line_paths, zebra_crossing_nodes = line_paths.to_crs(utm_crs), zebra_crossing_nodes.to_crs(utm_crs)
    matches = zebra_crossing_nodes.sjoin(
        line_paths[line_paths['category'].isin([PathCategory.EXCLUSIVE, PathCategory.SHARED_WITH_PEDESTRIANS])],
        how='inner',
        lsuffix='zebra_crossings',
        rsuffix='paths',
    ).reset_index()

    if len(matches) > 0:
        matches = matches.groupby('index_paths')
        # TODO: the column naming tells me that this is not using the `explode_tags` functionality of ohsome py
        # TODO: columns that were removed, please check: 'index','@other_tags_zebra_crossings',  'category','rating','@other_tags_paths'
        matches = matches[
            [
                'index_paths',
                'geometry',
            ]
        ].apply(_aggregate_multiple_crossings_on_one_path)
        split_paths_all = pd.concat(
            matches.apply(_split_paths_around_crossing, line_paths=line_paths, buffer_m=3, axis=1).to_list()
        )
        # drop original path:
        line_paths = line_paths.drop(matches['index_paths'], axis=0)
        line_paths = gpd.GeoDataFrame(pd.concat([line_paths, split_paths_all], ignore_index=True))
    line_paths = line_paths.set_crs(utm_crs, allow_override=True)
    line_paths = line_paths.to_crs('EPSG:4326')
    return pd.concat([line_paths, polygon_paths])


def zebra_crossings_filter() -> str:
    return str('geometry:point and type:node and (crossing=zebra or crossing:markings=zebra or crossing_ref=zebra)')
