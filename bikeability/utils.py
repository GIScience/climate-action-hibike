import logging
from typing import Callable, Any, Tuple, Union
from urllib.parse import parse_qsl

import geopandas as gpd
import matplotlib
import pandas as pd
from pyproj import CRS, Transformer
import shapely
from matplotlib.colors import to_hex, Normalize
from ohsome import OhsomeClient
from pydantic_extra_types.color import Color
from requests import PreparedRequest
from shapely import LineString
from shapely.ops import transform

from bikeability.indicators.path_categories import PathCategory
from bikeability.indicators.surface_types import SurfaceType
from bikeability.indicators.dooring_risk import DooringRiskCategory
from bikeability.indicators.smoothness import SmoothnessCategory

log = logging.getLogger(__name__)


def fetch_osm_data(aoi: shapely.MultiPolygon, osm_filter: str, ohsome: OhsomeClient) -> gpd.GeoDataFrame:
    elements = ohsome.elements.geometry.post(
        bpolys=aoi, clipGeometry=True, properties='tags', filter=osm_filter
    ).as_dataframe()
    elements = elements.reset_index()
    return elements[['@osmId', 'geometry', '@other_tags']]


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


def get_qualitative_color(
    category: Union[PathCategory, SmoothnessCategory, SurfaceType, DooringRiskCategory], cmap_name: str
) -> Color:
    norm = Normalize(0, 1)
    cmap = matplotlib.cm.ScalarMappable(norm=norm, cmap=cmap_name).get_cmap()
    cmap.set_under('#808080')

    category_norm = {name: idx / (len(category.get_visible()) - 1) for idx, name in enumerate(category.get_visible())}

    if category.value == 'unknown':
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
