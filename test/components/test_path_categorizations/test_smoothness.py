import pandas as pd
import shapely
import geopandas as gpd
import pytest

from bikeability.indicators.smoothness import SmoothnessCategory, apply_path_smoothness_filters
from bikeability.utils import ohsome_filter
from ohsome import OhsomeClient, OhsomeResponse
from functools import partial
from urllib3 import Retry


@pytest.fixture(scope='module')
def bpolys():
    """Small bounding boxes."""
    bpolys = gpd.GeoSeries(
        data=[
            # large box around Heidelberg:
            shapely.box(8.65354, 49.37019, 8.7836, 49.4447)
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
    SmoothnessCategory.EXCELLENT: {'way/28660531'},
    # https://www.openstreetmap.org/way/28660531 smoothness=excellent
    SmoothnessCategory.GOOD: {'way/27342468'},
    # https://www.openstreetmap.org/way/27342468 smoothness=good
    SmoothnessCategory.INTERMEDIATE: {'way/282619573'},
    # https://www.openstreetmap.org/way/282619573 smoothness=intermediate
    SmoothnessCategory.BAD: {'way/32277268'},
    # https://www.openstreetmap.org/way/32277268 smoothness=bad
    SmoothnessCategory.TOO_BUMPY_TO_RIDE: {'way/1132948390', 'way/175444345', 'way/32277580', 'way/27753943'},
    # https://www.openstreetmap.org/way/1132948390 smoothness=impassable
    # https://www.openstreetmap.org/way/175444345 smoothness=very_horrible
    # https://www.openstreetmap.org/way/32277580 smoothness=horrible
    # https://www.openstreetmap.org/way/27753943 smoothness=very_bad
    SmoothnessCategory.UNKNOWN: set(),
}


@pytest.fixture(scope='module')
def id_filter_smoothness() -> str:
    """Optimization to make the ohsome API request time faster."""
    full_ids = set().union(*validation_objects.values())
    return f'id:({",".join(full_ids)})'


@pytest.fixture(scope='module')
def osm_smoothness_return_data(request_ohsome: partial[OhsomeResponse], id_filter_smoothness: str) -> pd.DataFrame:
    osm_line_data = request_ohsome(filter=f'({ohsome_filter("line")})  and ({id_filter_smoothness})').as_dataframe(
        multi_index=False
    )
    osm_line_data['smoothness_category'] = osm_line_data.apply(apply_path_smoothness_filters, axis=1)

    return osm_line_data


@pytest.mark.parametrize('category', validation_objects)
def test_construct_smoothness_validate(osm_smoothness_return_data: pd.DataFrame, category: SmoothnessCategory):
    osm_smoothness_return_data = osm_smoothness_return_data[
        osm_smoothness_return_data['smoothness_category'] == category
    ]

    assert set(osm_smoothness_return_data['@osmId']) == validation_objects[category]
