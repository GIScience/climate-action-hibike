import logging
from enum import Enum
from typing import Dict, Callable, Any, Tuple, Union
from urllib.parse import parse_qsl

import geopandas as gpd
import matplotlib
import pandas as pd
import shapely
from shapely import LineString
from matplotlib.colors import to_hex, Normalize
from ohsome import OhsomeClient
from pydantic_extra_types.color import Color
from requests import PreparedRequest

log = logging.getLogger(__name__)


class PathCategory(Enum):
    DESIGNATED = 'designated'
    FORBIDDEN = 'forbidden'
    NOT_CATEGORISED = 'not_categorised'


def construct_filters() -> Dict[PathCategory, Callable[..., Any]]:
    def designated(d: Dict) -> bool:
        return d.get('bicycle') == 'designated'

    def forbidden(d: Dict) -> bool:
        return d.get('bicycle') == 'no'

    def not_categorised(d: Dict) -> bool:
        return True

    return {
        PathCategory.DESIGNATED: designated,
        PathCategory.FORBIDDEN: forbidden,
        PathCategory.NOT_CATEGORISED: not_categorised,
    }


def fetch_osm_data(aoi: shapely.MultiPolygon, osm_filter: str, ohsome: OhsomeClient) -> gpd.GeoDataFrame:
    elements = ohsome.elements.geometry.post(
        bpolys=aoi, clipGeometry=True, properties='tags', filter=osm_filter
    ).as_dataframe()
    if elements.empty:
        return gpd.GeoDataFrame(
            crs='epsg:4326', columns=['geometry', '@other_tags']
        )  # TODO: remove once https://github.com/GIScience/ohsome-py/pull/165 is resolved
    elements = elements.reset_index(drop=True)
    return elements[['geometry', '@other_tags']]


def apply_path_category_filters(row: gpd.GeoSeries, filters):
    for category, filter_func in filters:
        if filter_func(row['@other_tags']):
            return category
    return None


def boost_route_members(
    aoi: shapely.MultiPolygon,
    paths_line: gpd.GeoDataFrame,
    ohsome: OhsomeClient,
    boost_to: PathCategory = PathCategory.DESIGNATED,
) -> pd.Series:
    trails = fetch_osm_data(aoi, 'route in (bicycle)', ohsome)
    trails.geometry = trails.geometry.apply(lambda geom: fix_geometry_collection(geom))

    paths_line = paths_line.copy()
    paths_line = gpd.sjoin(
        paths_line,
        trails,
        lsuffix='path',
        rsuffix='trail',
        how='left',
        predicate='within',
    )
    paths_line = paths_line[~paths_line.index.duplicated(keep='first')]

    return paths_line.apply(
        lambda row: boost_to
        if not pd.isna(row.index_trail) and row.category in (PathCategory.FORBIDDEN, PathCategory.DESIGNATED)
        else row.category,
        axis=1,
    )


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
