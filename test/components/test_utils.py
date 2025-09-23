import geopandas as gpd
import geopandas.testing
import pytest
import shapely
from ohsome import OhsomeClient
from ohsome_filter_to_sql.main import ohsome_filter_to_sql

from bikeability.utils import (
    fetch_osm_data,
    ohsome_filter,
    parallel_parking_filter,
    zebra_crossings_filter,
)


def test_fetch_osm_data(default_aoi, expected_compute_input, responses_mock):
    with open('resources/test/ohsome_line_response.geojson', 'rb') as vector:
        responses_mock.post(
            'https://api.ohsome.org/v1/elements/geometry',
            body=vector.read(),
        )

    expected_osm_data = gpd.GeoDataFrame(
        data={
            '@osmId': ['way/171574582', 'way/171574582'],
            '@other_tags': [
                {'bicycle': 'no'},
                {
                    'highway': 'track',
                    'bicycle': 'yes',
                    'smoothness': 'intermediate',
                    'surface': 'fine_gravel',
                    'parking:both': 'no',
                },
            ],
        },
        geometry=[
            shapely.LineString([(12.3, 48.22), (12.3, 48.2205), (12.3005, 48.22)]),
            shapely.LineString([(12.3, 48.22), (12.3, 48.2205), (12.3005, 48.22)]),
        ],
        crs=4326,
    )
    computed_osm_data = fetch_osm_data(default_aoi, 'dummy=yes', OhsomeClient())
    geopandas.testing.assert_geodataframe_equal(computed_osm_data, expected_osm_data, check_like=True)


@pytest.mark.parametrize('geometry_type', ['line', 'polygon'])
def test_ohsome_filter(geometry_type):
    ohsome_filter_to_sql(ohsome_filter(geometry_type))


@pytest.mark.parametrize('geometry_type', ['line', 'polygon'])
def test_parking_filter(geometry_type):
    ohsome_filter_to_sql(parallel_parking_filter(geometry_type))


def test_crossings_filter():
    ohsome_filter_to_sql(zebra_crossings_filter())
