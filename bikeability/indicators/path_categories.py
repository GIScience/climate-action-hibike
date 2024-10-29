import logging
from typing import Dict, Tuple

import geopandas as gpd

from bikeability.utils import (
    PathCategory,
    apply_path_category_filters,
)

log = logging.getLogger(__name__)


def categorize_paths(
    paths_line: gpd.GeoDataFrame, paths_polygon: gpd.GeoDataFrame, rating_map: Dict[PathCategory, float]
) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    log.debug('Categorizing and rating paths')

    paths_line['category'] = paths_line.apply(apply_path_category_filters, axis=1)
    paths_polygon['category'] = paths_polygon.apply(apply_path_category_filters, axis=1)

    paths_line['rating'] = paths_line.category.apply(lambda category: rating_map[category])
    paths_polygon['rating'] = paths_polygon.category.apply(lambda category: rating_map[category])

    return paths_line, paths_polygon
