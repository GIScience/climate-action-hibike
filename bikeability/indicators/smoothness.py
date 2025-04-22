from enum import Enum
import logging

import pandas as pd
from bikeability.indicators.path_categories import PathCategory


import geopandas as gpd
from typing import Dict

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


class PathSmoothnessFilters:
    def too_bumpy_to_ride(self, d: Dict) -> bool:
        return d.get('smoothness') in ['very_bad', 'horrible', 'very_horrible', 'impassable']

    def bad(self, d: Dict) -> bool:
        return d.get('smoothness') == 'bad'

    def intermediate(self, d: Dict) -> bool:
        return d.get('smoothness') == 'intermediate'

    def good(self, d: Dict) -> bool:
        return d.get('smoothness') == 'good'

    def excellent(self, d: Dict) -> bool:
        return d.get('smoothness') == 'excellent'


def apply_path_smoothness_filters(row: pd.Series) -> SmoothnessCategory:
    filters = PathSmoothnessFilters()
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


def get_smoothness(line_paths: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    log.debug('Applying smoothness rating')

    line_paths = line_paths[line_paths.category.isin(PathCategory.get_bikeable())]

    line_paths['smoothness'] = line_paths.apply(apply_path_smoothness_filters, axis=1)

    return line_paths
