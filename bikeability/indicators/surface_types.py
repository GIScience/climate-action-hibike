from enum import Enum
import logging

import geopandas as gpd
import pandas as pd

from bikeability.indicators.path_categories import PathCategory

log = logging.getLogger(__name__)


class SurfaceType(Enum):
    ASPHALT = 'asphalt'
    CONCRETE = 'concrete'
    PAVING_STONES = 'paving_stones'
    COMPACTED = 'compacted'
    FINE_GRAVEL = 'fine_gravel'
    GRAVEL = 'gravel'
    COBBLESTONE = 'cobblestone'
    PAVED = 'paved_(unspecified)'
    OTHER_PAVED = 'other_paved_surfaces'
    UNPAVED = 'unpaved_(unspecified)'
    OTHER_UNPAVED = 'other_unpaved_surfaces'
    UNKNOWN = 'unknown'

    @classmethod
    def get_hidden(cls):
        return []

    @classmethod
    def get_visible(cls):
        return [category for category in cls if category not in cls.get_hidden()]


def categorise_surface(row: pd.Series) -> SurfaceType:
    match row['@other_tags']:
        case x if x.get('surface') is None:
            return SurfaceType.UNKNOWN
        case x if x.get('surface') == 'asphalt':
            return SurfaceType.ASPHALT
        case x if x.get('surface') in ['concrete', 'concrete:lanes', 'concrete:plates']:
            return SurfaceType.CONCRETE
        case x if x.get('surface') in ['paving_stones', 'paving_stones:lanes']:
            return SurfaceType.PAVING_STONES
        case x if x.get('surface') in ['cobblestones', 'sett', 'unhewn_cobblestone']:
            return SurfaceType.COBBLESTONE
        case x if x.get('surface') == 'paved':
            return SurfaceType.PAVED
        case x if x.get('surface') in [
            'chipseal',
            'grass_paver',
            'bricks',
            'metal',
            'metal_grid',
            'wood',
            'stepping_stones',
            'rubber',
            'tiles',
        ]:
            return SurfaceType.OTHER_PAVED
        case x if x.get('surface') == 'compacted':
            return SurfaceType.COMPACTED
        case x if x.get('surface') == 'fine_gravel':
            return SurfaceType.FINE_GRAVEL
        case x if x.get('surface') == 'gravel':
            return SurfaceType.GRAVEL
        case x if x.get('surface') == 'unpaved':
            return SurfaceType.UNPAVED
        case x if x.get('surface') in [
            'shells',
            'rock',
            'pebblestone',
            'ground',
            'dirt',
            'earth',
            'grass',
            'mud',
            'sand',
            'snow',
            'woodchips',
            'ice',
            'salt',
        ]:
            return SurfaceType.OTHER_UNPAVED
        case _:
            return SurfaceType.UNKNOWN


def get_surface_types(paths: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    log.debug('Categorizing path surfaces')
    paths = paths[paths.category.isin(PathCategory.get_visible())]
    paths['surface_type'] = paths.apply(categorise_surface, axis=1)
    return paths
