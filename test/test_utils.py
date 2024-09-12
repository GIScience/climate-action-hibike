from functools import partial

import geopandas as gpd
import geopandas.testing
import pandas as pd
import pytest
import shapely
from ohsome import OhsomeClient
from pydantic_extra_types.color import Color
from shapely.testing import assert_geometries_equal
from urllib3 import Retry

from bikeability.utils import (
    construct_filters,
    PathCategory,
    fetch_osm_data,
    get_color,
    apply_path_category_filters,
    boost_route_members,
    fix_geometry_collection,
)

validation_objects = {
    PathCategory.DESIGNATED: {'way/47942994'},
    PathCategory.FORBIDDEN: {'way/721923984'},
}


@pytest.fixture(scope='module')
def bpolys():
    """Small bounding boxes."""
    bpolys = gpd.GeoSeries(
        data=[
            shapely.box(8.672649, 49.416945, 8.676812, 49.419764),
        ],
        crs='EPSG:4326',
    )

    return bpolys


@pytest.fixture(scope='module')
def request_ohsome(bpolys):
    return partial(
        OhsomeClient(
            user_agent='HeiGIT Climate Action Walkability Tester', retry=Retry(total=1)
        ).elements.geometry.post,
        bpolys=bpolys,
        properties='tags',
        time='2024-01-01',
        timeout=60,
    )


@pytest.fixture(scope='module')
def id_filter() -> str:
    """Optimization to make the ohsome API request time faster."""
    full_ids = {''}
    for ids in validation_objects.values():
        full_ids.update(ids)
    full_ids.remove('')
    return f'id:({",".join(full_ids)})'


@pytest.fixture(scope='module')
def osm_return_data(request_ohsome, id_filter) -> gpd.GeoDataFrame:
    ohsome_filter = str(
        '(geometry:line or geometry:polygon) and '
        '(highway=* or route=ferry) and not '
        '(cycleway=separate or cycleway=separate or cycleway:both=separate or '
        '(cycleway:right=separate and cycleway:left=separate) or '
        '(cycleway:right=separate and cycleway:left=no) or (cycleway:right=no and cycleway:left=separate))'
    )
    osm_data = request_ohsome(filter=f'({ohsome_filter})  and ({id_filter})').as_dataframe(multi_index=False)
    osm_data['category'] = osm_data.apply(apply_path_category_filters, axis=1, filters=construct_filters().items())
    return osm_data


@pytest.mark.parametrize('category', validation_objects)
def test_construct_filter_validate(osm_return_data, category):
    osm_return_data = osm_return_data.query('category == @category')

    assert set(osm_return_data['@osmId']) == validation_objects[category]


def test_fetch_osm_data(expected_compute_input, responses_mock):
    with open('resources/test/ohsome_line_response.geojson', 'rb') as vector:
        responses_mock.post(
            'https://api.ohsome.org/v1/elements/geometry',
            body=vector.read(),
        )

    expected_osm_data = gpd.GeoDataFrame(
        data={
            '@other_tags': [{}],
        },
        geometry=[shapely.LineString([(12.3, 48.22), (12.3, 48.2205), (12.3005, 48.22)])],
        crs=4326,
    )
    computed_osm_data = fetch_osm_data(expected_compute_input.get_aoi_geom(), 'dummy=yes', OhsomeClient())
    geopandas.testing.assert_geodataframe_equal(computed_osm_data, expected_osm_data, check_like=True)


def test_boost_route_members(expected_compute_input, responses_mock):
    with open('resources/test/ohsome_line_response.geojson', 'rb') as vector:
        responses_mock.post(
            'https://api.ohsome.org/v1/elements/geometry',
            body=vector.read(),
        )

    expected_output = pd.Series(data=[PathCategory.DESIGNATED, PathCategory.DESIGNATED])

    paths_input = gpd.GeoDataFrame(
        data={
            'category': [
                PathCategory.DESIGNATED,
                PathCategory.FORBIDDEN,
            ]
        },
        geometry=[
            shapely.LineString([(12.3, 48.22), (12.3, 48.2205), (12.3005, 48.22)]),
            shapely.LineString([(12.3, 48.22), (12.3, 48.2205), (12.3005, 48.22)]),
        ],
        crs=4326,
    )
    computed_output = boost_route_members(expected_compute_input.get_aoi_geom(), paths_input, OhsomeClient())
    pd.testing.assert_series_equal(computed_output, expected_output)


def test_boost_route_members_overlapping_routes(expected_compute_input, responses_mock):
    with open('resources/test/ohsome_route_response.geojson', 'rb') as vector:
        responses_mock.post(
            'https://api.ohsome.org/v1/elements/geometry',
            body=vector.read(),
        )

    expected_output = pd.Series(data=[PathCategory.DESIGNATED])

    paths_input = gpd.GeoDataFrame(
        data={'category': [PathCategory.FORBIDDEN]},
        geometry=[
            shapely.LineString([(0, 0), (1, 1)]),
        ],
        crs=4326,
    )
    computed_output = boost_route_members(expected_compute_input.get_aoi_geom(), paths_input, OhsomeClient())
    pd.testing.assert_series_equal(computed_output, expected_output)


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
