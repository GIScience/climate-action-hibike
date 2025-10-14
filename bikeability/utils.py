import logging
from typing import Union

import geopandas as gpd
import matplotlib
import pandas as pd
import shapely
from climatoology.utility.exception import ClimatoologyUserError
from matplotlib.colors import Normalize, to_hex
from ohsome import OhsomeClient
from pydantic_extra_types.color import Color
from pyproj import CRS, Transformer
from shapely.ops import transform

from bikeability.indicators.dooring_risk import DooringRiskCategory
from bikeability.indicators.path_categories import PathCategory
from bikeability.indicators.smoothness import SmoothnessCategory
from bikeability.indicators.surface_types import SurfaceType

log = logging.getLogger(__name__)


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


def fetch_osm_data(aoi: shapely.MultiPolygon, osm_filter: str, ohsome: OhsomeClient) -> gpd.GeoDataFrame:
    elements = ohsome.elements.geometry.post(
        bpolys=aoi, clipGeometry=True, properties='tags', filter=osm_filter
    ).as_dataframe()
    elements = elements.reset_index()
    return elements[['@osmId', 'geometry', '@other_tags']]


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


def get_continuous_colors(category: pd.Series, cmap_name: str) -> list[Color]:
    norm = matplotlib.colors.Normalize(vmin=0, vmax=1)
    cmap = matplotlib.colormaps.get(cmap_name)
    cmap.set_bad('#808080')
    mapped_colors = [Color(matplotlib.colors.to_hex(col)) for col in cmap(norm(category))]
    return mapped_colors


def ohsome_filter(geometry_type: str) -> str:
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


def zebra_crossings_filter() -> str:
    return str('geometry:point and type:node and (crossing=zebra or crossing:markings=zebra or crossing_ref=zebra)')


def parallel_parking_filter(geometry_type) -> str:
    return str(f'geometry:{geometry_type} and amenity=parking and orientation=parallel')
