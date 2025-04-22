import logging
from enum import Enum
from typing import Dict

import geopandas as gpd
import pandas as pd

from bikeability.indicators.path_categories import PathCategory

log = logging.getLogger(__name__)


class DooringRiskCategory(Enum):
    DOORING_SAFE = 'safe_route'
    DOORING_RISK = 'risk_of_dooring'
    UNKNOWN = 'unknown'

    @classmethod
    def get_hidden(cls):
        return []

    @classmethod
    def get_visible(cls):
        return [category for category in cls if category not in cls.get_hidden()]


class DooringRiskFilters:
    def dooring_safe(self, d: Dict) -> bool:
        safe_orientations = ['diagonal', 'perpendicular']
        return (
            d.get('parking:both') == 'no'
            or (d.get('parking:both:orientation') in safe_orientations)
            or (
                d.get('parking:left:orientation') in safe_orientations
                and d.get('parking:right:orientation') in safe_orientations
            )
            or (d.get('parking:left') == 'no' and d.get('parking:right:orientation') in safe_orientations)
            or (d.get('parking:right') == 'no' and d.get('parking:left:orientation') in safe_orientations)
            or (
                d.get('parking:both:restriction') in ['no_parking', 'no_stopping']
                and not d.get('parking:both:restriction:conditional')
            )
            or (
                d.get('parking:left:restriction') in ['no_parking', 'no_stopping']
                and not d.get('parking:left:restriction:conditional')
            )
            # deprecated but still common way of tagging parking
            or (d.get('parking:lane:both') == 'no')
        )

    def dooring_risk(self, d: Dict) -> bool:
        parking_orientation_tags = [
            'parking:both:orientation',
            'parking:left:orientation',
            'parking:right:orientation',
            'parking:lane:both',
            'parking:lane:left',
            'parking:lane:right',
        ]
        parking_orientation = [d.get(tag) for tag in parking_orientation_tags]
        return 'parallel' in parking_orientation


def apply_dooring_filters(row: pd.Series) -> DooringRiskCategory:
    if row['category'] in [
        PathCategory.DESIGNATED_EXCLUSIVE,
        PathCategory.DESIGNATED_SHARED_WITH_PEDESTRIANS,
        PathCategory.REQUIRES_DISMOUNTING,
    ]:
        # Treat Paths that are not shared with motorised traffic as safe from dooring
        return DooringRiskCategory.DOORING_SAFE

    if row['parking']:
        # Paths with Separate Parking
        return DooringRiskCategory.DOORING_RISK

    filters = DooringRiskFilters()

    match row['@other_tags']:
        case x if filters.dooring_risk(x):
            return DooringRiskCategory.DOORING_RISK
        case x if filters.dooring_safe(x):
            return DooringRiskCategory.DOORING_SAFE
        case _:
            return DooringRiskCategory.UNKNOWN


def get_dooring_risk(line_paths: gpd.GeoDataFrame, parking: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    log.debug('Applying dooring risk rating')

    line_paths = line_paths[line_paths.category.isin(PathCategory.get_bikeable())]

    line_paths_with_parking = find_nearest_parking(line_paths, parking)

    line_paths_with_parking['dooring_category'] = line_paths_with_parking.apply(apply_dooring_filters, axis=1)
    return line_paths_with_parking


def find_nearest_parking(line_paths, parking):
    utm_crs = line_paths.estimate_utm_crs()
    line_paths = line_paths.to_crs(utm_crs)
    parking = parking.to_crs(utm_crs)
    line_paths_with_parking = line_paths.sjoin_nearest(parking, how='left', max_distance=10, distance_col='distance')

    line_paths_with_parking['parking'] = line_paths_with_parking.apply(lambda row: pd.notna(row['distance']), axis=1)
    line_paths_with_parking = line_paths_with_parking.to_crs('EPSG:4326')

    line_paths = line_paths_with_parking.rename(columns={'@other_tags_left': '@other_tags', '@osmId_left': '@osmId'})

    line_paths = line_paths[['geometry', '@osmId', '@other_tags', 'parking', 'category']]

    return line_paths
