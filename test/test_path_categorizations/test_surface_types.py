from functools import partial

import geopandas as gpd
import pandas as pd
import pytest
import shapely
from ohsome import OhsomeResponse, OhsomeClient
from urllib3 import Retry

from bikeability.indicators.surface_types import SurfaceType, get_surface_types

from bikeability.utils import ohsome_filter


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


@pytest.fixture(scope='module')
def id_filter() -> str:
    """Optimization to make the ohsome API request time faster."""
    full_ids = set().union(*validation_objects.values())
    return f'id:({",".join(full_ids)})'


@pytest.fixture(scope='module')
def osm_return_data(request_ohsome: partial[OhsomeResponse], id_filter: str) -> pd.DataFrame:
    osm_line_data = request_ohsome(filter=f'({ohsome_filter("line")})  and ({id_filter})').as_dataframe(
        multi_index=False
    )
    osm_line_data = get_surface_types(osm_line_data)
    return osm_line_data


validation_objects = {
    SurfaceType.PAVING_STONES: {'way/320034117', 'way/849049867', 'way/25805786'},
}


@pytest.mark.parametrize(
    'input_surface,expected_output',
    [
        (None, SurfaceType.UNKNOWN),
        ('asphalt', SurfaceType.ASPHALT),
        ('concrete', SurfaceType.CONCRETE),
        ('concrete:lanes', SurfaceType.CONCRETE),
        ('paving_stones', SurfaceType.PAVING_STONES),
        ('paving_stones:lanes', SurfaceType.PAVING_STONES),
        ('cobblestones', SurfaceType.COBBLESTONE),
        ('paved', SurfaceType.PAVED),
        ('chipseal', SurfaceType.OTHER_PAVED),
        ('compacted', SurfaceType.COMPACTED),
        ('fine_gravel', SurfaceType.FINE_GRAVEL),
        ('gravel', SurfaceType.GRAVEL),
        ('unpaved', SurfaceType.UNPAVED),
        ('shells', SurfaceType.OTHER_UNPAVED),
        ('unknown', SurfaceType.UNKNOWN),
    ],
)
def test_get_surface_types(test_line, input_surface, expected_output):
    test_line['@other_tags'][1].update({'surface': input_surface})
    computed_line = get_surface_types(test_line).reset_index(drop=True)

    assert computed_line.loc[0, 'surface_type'] == expected_output
