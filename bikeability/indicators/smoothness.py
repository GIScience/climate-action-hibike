import logging
from bikeability.utils import SmoothnessCategory, apply_path_smoothness_filters


import geopandas as gpd
from typing import Dict

log = logging.getLogger(__name__)


def get_smoothness(line_paths: gpd.GeoDataFrame, rating_map: Dict[SmoothnessCategory, float]) -> gpd.GeoDataFrame:
    log.debug('Applying smoothness rating')

    line_paths['smoothness'] = line_paths.apply(apply_path_smoothness_filters, axis=1)
    line_paths['smoothness_rating'] = line_paths.smoothness.apply(lambda smoothness: rating_map[smoothness])

    return line_paths
