import logging
from enum import StrEnum

import geopandas as gpd
import shapely
from climatoology.base.exception import ClimatoologyUserError, InputValidationError
from ohsome_filter_to_sql.main import OhsomeFilter
from ohsome_py2.client import OhsomeAPIError, OhsomeClient
from pyproj import CRS, Transformer
from shapely.ops import transform

log = logging.getLogger(__name__)


class Topics(StrEnum):
    TRAFFIC = 'traffic'
    SURFACE = 'surface'
    SUMMARY = 'summary'
    CONNECTIVITY = 'connectivity'
    BARRIERS = 'barriers'
    SAFETY = 'safety'
    GREENNESS = 'greenness'


def check_paths_count_limit(aoi: shapely.MultiPolygon, ohsome: OhsomeClient, count_limit: int) -> None:
    """
    Check whether paths count is over the limit. (NOTE: just check path_lines)
    """
    path_lines_count = ohsome.features_stats(aoi=aoi, osm_filter=ohsome_filter('line'), measure='count')
    log.info(f'There are {path_lines_count} paths selected.')
    if path_lines_count > count_limit:
        raise InputValidationError(
            f'There are too many path segments in the selected area: {path_lines_count} path segments. '
            f'Currently, only areas with a maximum of {count_limit} path segments are allowed. '
            f'Please select a smaller area or a sub-region of your selected area.'
        )


def fetch_osm_data(aoi: shapely.MultiPolygon, osm_filter: OhsomeFilter, ohsome: OhsomeClient) -> gpd.GeoDataFrame:
    try:
        elements = ohsome.features_extraction(aoi=aoi, osm_filter=osm_filter, clip=True)
    except OhsomeAPIError:
        raise ClimatoologyUserError('There was an error collecting OSM data. Please try again later.')
    except Exception:
        log.exception('Unexpected error when downloading OSM data.')
        raise ClimatoologyUserError('Unexpected error when collecting OSM data. Please contact us to find out more.')

    elements = elements.rename_geometry('geometry')
    elements['osm_id'] = elements['osm_id'].astype(str)  # v2 returns osm_id as int, while v1 returns them as str.
    return elements[['osm_id', 'osm_type', 'geometry', 'osm_tags']]


def ohsome_filter(geometry_type: str) -> OhsomeFilter:
    return str(
        f'geometry:{geometry_type} and '
        '(highway=* or railway=platform) and not '
        '(cycleway=separate or cycleway:both=separate or '
        '(cycleway:right=separate and cycleway:left=separate) or '
        'indoor=yes or indoor=corridor)'
    )


def get_utm_zone(aoi: shapely.MultiPolygon) -> CRS:
    return gpd.GeoSeries(data=aoi, crs='EPSG:4326').estimate_utm_crs()


def get_buffered_aoi(aoi: shapely.MultiPolygon) -> shapely.MultiPolygon:
    wgs84 = CRS('EPSG:4326')
    utm = get_utm_zone(aoi)

    geographic_projection_function = Transformer.from_crs(wgs84, utm, always_xy=True).transform
    wgs84_projection_function = Transformer.from_crs(utm, wgs84, always_xy=True).transform
    projected_aoi = transform(geographic_projection_function, aoi)
    # changed the distance to a fixed value of 5 km.
    buffered_aoi = projected_aoi.buffer(5000)
    return transform(wgs84_projection_function, buffered_aoi)


def calculate_length(length_resolution_m, paths, projected_crs):
    stats = paths.copy()
    stats = stats.loc[stats.geometry.geom_type.isin(('MultiLineString', 'LineString'))]
    stats = stats.to_crs(projected_crs)
    stats['length'] = stats.length / length_resolution_m
    stats['length'] = round(stats['length'], 2)
    return stats


def length_weighted_mean(gdf: gpd.GeoDataFrame, col: str) -> float:
    projected_data = gdf.to_crs(gdf.estimate_utm_crs())

    weighted_slopes = projected_data.length * projected_data[col]

    total_length = projected_data.length.sum()
    weighted_mean = weighted_slopes.sum() / total_length
    return weighted_mean
