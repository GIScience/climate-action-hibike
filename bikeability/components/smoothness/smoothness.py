import logging
from enum import Enum

import geopandas as gpd
import pandas as pd

from bikeability.components.path_categories.path_categories import PathCategory
from bikeability.components.smoothness import filters

log = logging.getLogger(__name__)


class SmoothnessCategory(Enum):
    EXCELLENT = 'excellent'
    GOOD = 'good'
    INTERMEDIATE = 'intermediate'
    BAD = 'bad'
    TOO_BUMPY_TO_RIDE = 'too_bumpy_to_ride'
    UNKNOWN = 'unknown'

    @classmethod
    def get_hidden(cls):
        return []

    @classmethod
    def get_visible(cls):
        return [category for category in cls if category not in cls.get_hidden()]


def apply_path_smoothness_filters(row: pd.Series) -> SmoothnessCategory:
    match row['@other_tags']:
        case x if filters.too_bumpy_to_ride(x):
            return SmoothnessCategory.TOO_BUMPY_TO_RIDE
        case x if filters.bad(x):
            return SmoothnessCategory.BAD
        case x if filters.intermediate(x):
            return SmoothnessCategory.INTERMEDIATE
        case x if filters.good(x):
            return SmoothnessCategory.GOOD
        case x if filters.excellent(x):
            return SmoothnessCategory.EXCELLENT
        case _:
            return SmoothnessCategory.UNKNOWN


def get_smoothness(paths: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    log.debug('Applying smoothness rating')

    paths = paths[paths.category.isin(PathCategory.get_bikeable())].copy(deep=False)

    paths['smoothness'] = paths.apply(apply_path_smoothness_filters, axis=1)

    return paths
