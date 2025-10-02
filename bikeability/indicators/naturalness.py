import datetime as dt
import logging

import geopandas as gpd
import pandas as pd
import shapely
from climatoology.utility.api import TimeRange
from climatoology.utility.Naturalness import NaturalnessIndex, NaturalnessUtility

log = logging.getLogger(__name__)


def _preprocess_path_line(path_line: shapely.LineString, is_0x: bool) -> shapely.LineString:
    buffer_offset = 0.000009  # ~1 m

    coords = list(path_line.coords)
    last_coords = coords[-1]
    if is_0x:
        new_coords = coords[:-1] + [(last_coords[0] + buffer_offset, last_coords[1])]
    else:
        new_coords = coords[:-1] + [(last_coords[0], last_coords[1] + buffer_offset)]

    return shapely.LineString(new_coords)


def _valid_path_lines(path_lines: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    path_lines_bounds = path_lines.geometry.bounds
    path_lines_width = path_lines_bounds['maxx'] - path_lines_bounds['minx']
    path_lines_height = path_lines_bounds['maxy'] - path_lines_bounds['miny']

    # fix width = 0
    path_lines.loc[(path_lines_width == 0), 'geometry'] = path_lines.loc[(path_lines_width == 0), 'geometry'].apply(
        lambda row: _preprocess_path_line(row, True)
    )

    # fix height = 0 (when width != 0)
    path_lines.loc[(path_lines_width != 0) & (path_lines_height == 0), 'geometry'] = path_lines.loc[
        (path_lines_width != 0) & (path_lines_height == 0), 'geometry'
    ].apply(lambda row: _preprocess_path_line(row, False))

    return path_lines


def fetch_naturalness_by_vector(
    nature_utility: NaturalnessUtility,
    time_range: TimeRange,
    vectors: list[gpd.GeoSeries],
    index: NaturalnessIndex,
    agg_stats: list[str],
    resolution: int = 30,
) -> gpd.GeoDataFrame:
    naturalness_gdf = nature_utility.compute_vector(
        index=index,
        aggregation_stats=agg_stats,
        vectors=vectors,
        time_range=time_range,
        resolution=resolution,
    )

    naturalness_gdf = naturalness_gdf.rename(columns={'median': 'naturalness'})
    return naturalness_gdf


def get_naturalness(
    path_lines: gpd.GeoDataFrame,
    path_polygons: gpd.GeoDataFrame,
    nature_utility: NaturalnessUtility,
    nature_index: NaturalnessIndex,
    agg_stats: list[str] = ['median'],
) -> gpd.GeoDataFrame:
    """
    Get naturalness/NDVI along street within the AOI.
    """
    log.info('Naturalness calculation starts...')

    log.debug("Pre-process lingstring (path_line) to avoid the case 'width/height = 0'")
    lines_valid = _valid_path_lines(path_lines.copy())

    log.debug('compute naturalness by sentinelhub... (path_lines)')
    lines_ndvi = fetch_naturalness_by_vector(
        nature_utility=nature_utility,
        time_range=TimeRange(end_date=dt.datetime.now().replace(day=1).date()),
        vectors=[lines_valid.geometry],
        index=nature_index,
        agg_stats=agg_stats,
    )

    log.debug('Post-process: reset path_line geometry which is not pre-processed')
    lines_ndvi.geometry = path_lines.geometry

    log.debug('compute naturalness by sentinelhub... (path_polygons)')
    polygons_ndvi = fetch_naturalness_by_vector(
        nature_utility=nature_utility,
        time_range=TimeRange(end_date=dt.datetime.now().replace(day=1).date()),
        vectors=[path_polygons.geometry],
        index=nature_index,
        agg_stats=agg_stats,
    )

    # merge path_lines and path_polygons result here and return one dataframe
    paths_all_ndvi = pd.concat([lines_ndvi, polygons_ndvi], ignore_index=True)

    log.info('Naturalness calculation completed.')

    return paths_all_ndvi
