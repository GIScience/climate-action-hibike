import geopandas as gpd
import geopandas.testing
import pandas as pd
import pytest
import shapely
from approvaltests.approvals import verify
from approvaltests.namer import NamerFactory
from ohsome import OhsomeClient
from pydantic_extra_types.color import Color
from shapely.testing import assert_geometries_equal

from bikeability.utils import (
    fetch_osm_data,
    get_color,
    fix_geometry_collection,
    ohsome_filter,
    zebra_crossings_filter,
    parallel_parking_filter,
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


def test_fix_geometry_collection():
    expected_geom = shapely.LineString([(0, 0), (1, 0), (1, 1)])

    geometry_collection_input = shapely.GeometryCollection(
        [
            shapely.Point(-1, -1),
            expected_geom,
        ]
    )
    point_input = shapely.Point(-1, -1)

    input_output_map = {
        'unchanged': {'input': expected_geom, 'output': expected_geom},
        'extracted': {'input': geometry_collection_input, 'output': expected_geom},
        'ignored': {'input': point_input, 'output': shapely.LineString()},
    }
    for _, map in input_output_map.items():
        computed_geom = fix_geometry_collection(map['input'])
        assert_geometries_equal(computed_geom, map['output'])


def test_get_color():
    expected_output = pd.Series([Color('#006837'), Color('#feffbe'), Color('#a50026')])

    expected_input = pd.Series([1.0, 0.5, 0.0])
    computed_output = get_color(expected_input)

    pd.testing.assert_series_equal(computed_output, expected_output)


@pytest.mark.parametrize('geometry_type', ['line', 'polygon'])
def test_ohsome_filter(geometry_type):
    verify(ohsome_filter(geometry_type), options=NamerFactory.with_parameters(geometry_type))


@pytest.mark.parametrize('geometry_type', ['line', 'polygon'])
def test_parking_filter(geometry_type):
    verify(parallel_parking_filter(geometry_type), options=NamerFactory.with_parameters(geometry_type))


def test_crossings_filter():
    verify(zebra_crossings_filter())
