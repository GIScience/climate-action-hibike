from functools import partial

import geopandas as gpd
import pandas as pd
import pytest
import shapely
from ohsome import OhsomeClient, OhsomeResponse
from urllib3 import Retry

from bikeability.indicators.dooring_risk import (
    DooringRiskCategory,
    apply_dooring_filters,
    find_nearest_parking,
)
from bikeability.indicators.path_categories import apply_path_category_filters
from bikeability.utils import (
    ohsome_filter,
    parallel_parking_filter,
)


@pytest.fixture(scope='module')
def bpolys():
    """Small bounding boxes."""
    bpolys = gpd.GeoSeries(
        data=[
            # large box around Heidelberg:
            shapely.box(8.65354, 49.37019, 8.7836, 49.4447),
            # perpendicular parking cases:
            shapely.box(8.478101, 49.464160, 8.490192, 49.480128),
            # diagonal parking cases:
            shapely.box(8.645821, 50.106273, 8.656443, 50.115557),
            # parking separate cases:
            shapely.box(8.640989, 50.121719, 8.642748, 50.122811),
            # separate parking without tags on the street:
            shapely.box(8.402949, 49.473049, 8.403547, 49.473839),
        ],
        crs='EPSG:4326',
    )
    return bpolys


@pytest.fixture(scope='module')
def request_ohsome(bpolys):
    return partial(
        OhsomeClient(
            user_agent='HeiGIT Climate Action Bikeability Tester', retry=Retry(total=1)
        ).elements.geometry.post,
        bpolys=bpolys,
        properties='tags',
        time='2024-01-01',
        timeout=60,
    )


validation_objects = {
    DooringRiskCategory.DOORING_RISK: {
        'way/24644359',
        'way/24485180',
        'way/1026216148',
        'way/155055444',
        'way/1115530967',
        'way/24485185',
        'way/1081736395',
        'way/622579778',
    },
    # https://www.openstreetmap.org/way/1026216148 parking:both:orientation=parallel
    # https://www.openstreetmap.org/way/24485180 parking:right:orientation=parallel
    # https://www.openstreetmap.org/way/24644359 parking:left:orientation=parallel
    # https://www.openstreetmap.org/way/1081736395 parking:left=separate, parking:right=separate with parallel parking
    # https://www.openstreetmap.org/way/622579778 no parking related tags, but amenity=parking and orientation=parallel adjacent
    # The following are deprecated ways of tagging on street parking
    # https://www.openstreetmap.org/way/155055444 parking:lane:both=parallel
    # https://www.openstreetmap.org/way/1115530967 parking:lane:left=parallel
    # https://www.openstreetmap.org/way/24485185 parking:lane:left=parallel
    DooringRiskCategory.DOORING_SAFE: {
        'way/1124445170',
        'way/190443683',
        'way/1109137744',
        'way/1213267125',
        'way/142603608',
        'way/9824020',
        'way/58164685',
    },
    # https://www.openstreetmap.org/way/1124445170 parking:lane:both=no
    # https://www.openstreetmap.org/way/190443683 parkinng:both:orientation=perpendicular
    # https://www.openstreetmap.org/way/1109137744 parking:right:orientation=perpendicular and parking:left:orientation=perpendicular
    # https://www.openstreetmap.org/way/1213267125 parking:left:orientation=perpendicular and parkinng:right=no
    # https://www.openstreetmap.org/way/142603608 parking:both:orientation=diagonal
    # https://www.openstreetmap.org/way/9824020 parking:left:orientation=diagonal and parking:right=no
    # https://www.openstreetmap.org/way/58164685 parking:right:orientation=diagonal and parking:left=no
    DooringRiskCategory.UNKNOWN: set(),
}


@pytest.fixture(scope='module')
def id_filter_dooring() -> str:
    full_ids = set().union(*validation_objects.values())
    return f'id:({",".join(full_ids)})'


@pytest.fixture(scope='module')
def osm_parking_data(request_ohsome: partial[OhsomeResponse]) -> pd.DataFrame:
    return request_ohsome(filter=f'({parallel_parking_filter("polygon")})').as_dataframe()


@pytest.fixture(scope='module')
def osm_dooring_return_data(
    request_ohsome: partial[OhsomeResponse], id_filter_dooring: str, osm_parking_data: gpd.GeoDataFrame
) -> pd.DataFrame:
    osm_line_data = request_ohsome(filter=f'({ohsome_filter("line")})  and ({id_filter_dooring})').as_dataframe(
        multi_index=False
    )

    osm_line_data['category'] = osm_line_data.apply(apply_path_category_filters, axis=1)

    osm_line_data = find_nearest_parking(osm_line_data, osm_parking_data)
    osm_line_data['dooring_category'] = osm_line_data.apply(apply_dooring_filters, axis=1)

    return osm_line_data


@pytest.mark.parametrize('category', validation_objects)
def test_construct_dooring_filter_validate(osm_dooring_return_data: pd.DataFrame, category: DooringRiskCategory):
    osm_dooring_return_data = osm_dooring_return_data[osm_dooring_return_data['dooring_category'] == category]

    assert set(osm_dooring_return_data['@osmId']) == validation_objects[category]
