import logging
from enum import StrEnum

import geopandas as gpd
import shapely
from climatoology.base.exception import ClimatoologyUserError
from ohsome import OhsomeClient
from ohsome.exceptions import OhsomeException
from ohsome_filter_to_sql.main import OhsomeFilter
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
    Check whether paths count is over than limit. (NOTE: just check path_lines)
    """

    ohsome_responses = ohsome.elements.count.post(bpolys=aoi, filter=ohsome_filter('line')).data
    path_lines_count = sum([response['value'] for response in ohsome_responses['result']])
    log.info(f'There are {path_lines_count} are selected.')
    if path_lines_count > count_limit:
        raise ClimatoologyUserError(
            f'There are too many path segments in the selected area: {path_lines_count} path segments. '
            f'Currently, only areas with a maximum of 500,000 path segments are allowed. '
            f'Please select a smaller area or a sub-region of your selected area.'
        )


def fetch_osm_data(aoi: shapely.MultiPolygon, osm_filter: OhsomeFilter, ohsome: OhsomeClient) -> gpd.GeoDataFrame:
    try:
        elements = ohsome.elements.geometry.post(
            bpolys=aoi, clipGeometry=True, properties='tags', filter=osm_filter
        ).as_dataframe()
    except OhsomeException as e:
        if e.error_code in [500, 501, 502, 503, 507]:
            raise ClimatoologyUserError('Ohsome is currently not available.')
        else:
            raise e

    elements = elements.reset_index()
    return elements[['@osmId', 'geometry', '@other_tags']]


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
