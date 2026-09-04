from unittest.mock import patch

import geopandas as gpd
import geopandas.testing
import pytest
import shapely
from climatoology.base.exception import ClimatoologyUserError, InputValidationError
from numpy.testing import assert_almost_equal
from ohsome.exceptions import OhsomeException
from ohsome_filter_to_sql.main import validate_filter
from ohsome_py2.client import OhsomeClient

from bikeability.components.utils.utils import (
    check_paths_count_limit,
    fetch_osm_data,
    length_weighted_mean,
    ohsome_filter,
)


@pytest.mark.vcr
def test_check_paths_count_limit(parametrized_ohsome_client, small_aoi):
    with pytest.raises(InputValidationError):
        check_paths_count_limit(
            aoi=small_aoi,
            count_limit=100,
            ohsome=parametrized_ohsome_client,
        )


@pytest.mark.vcr
def test_fetch_osm_data(small_aoi, parametrized_ohsome_client):
    # Basic test that could probably be deleted (it is a very short function that just calls external code)

    computed_osm_data = fetch_osm_data(
        aoi=small_aoi,
        osm_filter='geometry:polygon and highway=*',
        ohsome=parametrized_ohsome_client,
    )

    assert isinstance(computed_osm_data, gpd.GeoDataFrame)
    assert not computed_osm_data.empty
    assert all([col in computed_osm_data for col in ['osm_id', 'osm_type', 'osm_tags', 'geometry']])


class MockPostClient:
    def post(self, **kwags):
        raise OhsomeException('test: Broken Response', error_code=500)


class MockElements:
    @property
    def geometry(self):
        return MockPostClient()


@patch.object(OhsomeClient, attribute='features_extraction', new=MockElements())
def test_fetch_osm_data_ohsome_error(default_aoi, parametrized_ohsome_client):
    # We won't test this with V2 because it doesn't need the API, just the mocks defined above
    with pytest.raises(ClimatoologyUserError):
        fetch_osm_data(
            aoi=default_aoi,
            osm_filter='dummy=yes',
            ohsome=parametrized_ohsome_client,
        )


@pytest.mark.parametrize('geometry_type', ['line', 'polygon'])
def test_ohsome_filter(geometry_type):
    validate_filter(ohsome_filter(geometry_type))


def test_length_weighted_mean():
    col = 'column'
    input_data = gpd.GeoDataFrame(
        data={col: [1, 4]},
        geometry=[shapely.LineString([(0.0, 0.0), (0.0, 0.2)]), shapely.LineString([(0.0, 0.0), (0.0, 0.1)])],
        crs=4326,
    )

    expected = 2

    received = length_weighted_mean(input_data, col=col)

    assert_almost_equal(received, expected)
