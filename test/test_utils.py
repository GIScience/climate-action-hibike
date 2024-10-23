from functools import partial

import geopandas as gpd
import geopandas.testing
import pandas as pd
import pytest
import shapely
from approvaltests.approvals import verify
from approvaltests.namer import NamerFactory
from ohsome import OhsomeClient, OhsomeResponse
from pydantic_extra_types.color import Color
from shapely.testing import assert_geometries_equal
from urllib3 import Retry

from bikeability.utils import (
    PathCategory,
    fetch_osm_data,
    get_color,
    apply_path_category_filters,
    boost_route_members,
    fix_geometry_collection,
    ohsome_filter,
)

validation_objects = {
    PathCategory.NOT_BIKEABLE: {'way/4084008', 'way/24635973', 'way/343029968'},
    # https://www.openstreetmap.org/way/4084008 highway=trunk
    # https://www.openstreetmap.org/way/24635973 highway=secondary and bicycle=no
    # https://www.openstreetmap.org/way/343029968 highway=primary and motorroad=yes
    PathCategory.DESIGNATED_EXCLUSIVE: {'way/246387137', 'way/118975501'},
    # https://www.openstreetmap.org/way/246387137 highway=cycleway and foot=no
    # https://www.openstreetmap.org/way/118975501 highway=path and foot=yes and segregated=yes
    PathCategory.DESIGNATED_SHARED_WITH_PEDESTRIANS: {'way/587937936', 'way/27620739', 'way/406929620'},
    # https://www.openstreetmap.org/way/587937936 highway=path and bicycle=designated and foot=designated and segregated=no
    # https://www.openstreetmap.org/way/27620739 highway=footway and bicycle=yes but no foot tag
    # https://www.openstreetmap.org/way/406929620 highway=track
    PathCategory.SHARED_WITH_MOTORISED_TRAFFIC_WALKING_SPEED: {
        'way/34386123',
        'way/27342468',
        'way/715905252',
        'way/35978590',
        'way/274709010',
        'way/440466305',
        'way/83188869',
        'way/191212309',
    },
    # https://www.openstreetmap.org/way/34386123 highway=living_street and bicycle=yes
    # https://www.openstreetmap.org/way/27342468 highway=living_street cycleway:both=no
    # https://www.openstreetmap.org/way/715905252 highway=service and bicycle=yes
    # https://www.openstreetmap.org/way/35978590 highway=service and no bicycle tag
    # https://www.openstreetmap.org/way/274709010 highway=residential and maxspeed=10 and cycleway:both=no
    # https://www.openstreetmap.org/way/440466305 highway=living_street and maxspeed=walk
    # https://www.openstreetmap.org/way/83188869 highway=residential and maxspeed=15 and cycleway:both=no
    # https://www.openstreetmap.org/way/191212309 highway=residential and bicylce=designated ("Fahrradstraße") and maxspeed=15 and motorvehicle=destination
    PathCategory.SHARED_WITH_MOTORISED_TRAFFIC_LOW_SPEED: {
        'way/37685272',
        'way/244287984',
        'way/258562283',
        'way/28891216',
        'way/932097064',
        'way/277455037',
    },
    # https://www.openstreetmap.org/way/37685272 highway=residential and bicycle=designated and bicycle_road=yes ('Fahrradstraße') and maxspeed=30 and motor_vehicle=yes
    # https://www.openstreetmap.org/way/244287984 highway=residential and cycleway:both=no and maxspeed=20
    # https://www.openstreetmap.org/way/258562283 highway=tertiary and cycleway:left=no and cycleway:right=lane and maxspeed=30
    # https://www.openstreetmap.org/way/28891216 highway=primary cycleway:both=lane and maxspeed=30
    # https://www.openstreetmap.org/way/932097064 highway=residential and maxspeed=30 and cycleway:both=no
    # https://www.openstreetmap.org/way/277455037 highway=tertiary and zone:maxspeed=DE:30 and cycleway:right=no
    PathCategory.SHARED_WITH_MOTORISED_TRAFFIC_MEDIUM_SPEED: {
        'way/254010814',
        'way/596760204',
        'way/26816187',
        # 'way/152645928', # Lagos testcase commented out for speed reasons
    },
    # https://www.openstreetmap.org/way/254010814 highway=residential and cycleway:both=lane and maxspeed=50
    # https://www.openstreetmap.org/way/596760204 highway=tertiary and cycleway:both=no and maxspeed=50
    # https://www.openstreetmap.org/way/26816187 highway=residential and maxspeed:type=DE:urban
    # https://www.openstreetmap.org/way/152645928 highway=residential (commented out for speed reasons)
    PathCategory.SHARED_WITH_MOTORISED_TRAFFIC_HIGH_SPEED: {'way/372602113', 'way/189054375', 'way/155281272'},
    # https://www.openstreetmap.org/way/372602113 highway=tertiary and mayspeed=70 and cycleway:both=no
    # https://www.openstreetmap.org/way/189054375 highway=unclassified and maxspeed:type=DE:rural
    # https://www.openstreetmap.org/way/155281272 highway=secondary and maxspeed=70 and cycleway:left=no and cyclewayright=separate
    PathCategory.REQUIRES_DISMOUNTING: {
        'way/810025053',
        'way/131478149',
        'way/24968605',
        'way/27797958',
        'way/87956068',
    },
    # https://www.openstreetmap.org/way/810025053 highway=footway and bicycle=dismount
    # https://www.openstreetmap.org/way/131478149 highway=steps and ramp:bicycle=yes
    # https://www.openstreetmap.org/way/24968605 highway=steps and ramp=yes and ramp:stroller=yes
    # https://www.openstreetmap.org/way/27797958 railway=platform
    # https://www.openstreetmap.org/way/87956068 highway=track and ford=yes
    PathCategory.PEDESTRIAN_EXCLUSIVE: {'way/26028197', 'way/870757384', 'way/694458151'},
    # https://www.openstreetmap.org/way/26028197 highway=footway and bicycle=no
    # https://www.openstreetmap.org/way/870757384 highway=pedestrian and bicycle=no
    # https://www.openstreetmap.org/way/694458151 footway=yes
    PathCategory.RESTRICTED_ACCESS: {'way/320034117', 'way/849049867', 'way/25805786'},
    # https://www.openstreetmap.org/way/849049867 highway=service and access=no and bus=yes
    # https://www.openstreetmap.org/way/25805786 highway=service and access=private
    # https://www.openstreetmap.org/way/320034117 highway=footway and access=private
    PathCategory.UNKNOWN: set(),
}


@pytest.fixture(scope='module')
def bpolys():
    """Small bounding boxes."""
    bpolys = gpd.GeoSeries(
        data=[
            # large box around Heidelberg:
            shapely.box(8.65354, 49.37019, 8.7836, 49.4447),
            # Lagos: (small box for way/152645928, commented out for speed reasons)
            # shapely.box(3.354680, 6.444900, 3.369928, 6.455165),
            # Ford:
            shapely.box(8.786665, 49.370061, 8.786965, 49.370305),
            # Motorroad:
            shapely.box(8.491960, 49.476107, 8.496047, 49.477822),
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
    full_ids = set().union(*validation_objects.values())
    return f'id:({",".join(full_ids)})'


@pytest.fixture(scope='module')
def osm_return_data(request_ohsome: partial[OhsomeResponse], id_filter: str) -> pd.DataFrame:
    osm_line_data = request_ohsome(filter=f'({ohsome_filter("line")})  and ({id_filter})').as_dataframe(
        multi_index=False
    )
    osm_line_data['category'] = osm_line_data.apply(apply_path_category_filters, axis=1)

    osm_polygon_data = request_ohsome(filter=f'({ohsome_filter("polygon")})  and ({id_filter})').as_dataframe(
        multi_index=False
    )
    osm_polygon_data['category'] = osm_polygon_data.apply(apply_path_category_filters, axis=1)

    return pd.concat([osm_line_data, osm_polygon_data])


@pytest.mark.parametrize('category', validation_objects)
def test_construct_filter_validate(osm_return_data: pd.DataFrame, category: PathCategory):
    osm_return_data = osm_return_data[osm_return_data['category'] == category]

    assert set(osm_return_data['@osmId']) == validation_objects[category]


def test_fetch_osm_data(expected_compute_input, responses_mock):
    with open('resources/test/ohsome_line_response.geojson', 'rb') as vector:
        responses_mock.post(
            'https://api.ohsome.org/v1/elements/geometry',
            body=vector.read(),
        )

    expected_osm_data = gpd.GeoDataFrame(
        data={
            '@other_tags': [{'bicycle': 'no'}],
        },
        geometry=[shapely.LineString([(12.3, 48.22), (12.3, 48.2205), (12.3005, 48.22)])],
        crs=4326,
    )
    computed_osm_data = fetch_osm_data(expected_compute_input.get_aoi_geom(), 'dummy=yes', OhsomeClient())
    geopandas.testing.assert_geodataframe_equal(computed_osm_data, expected_osm_data, check_like=True)


def test_boost_route_members(expected_compute_input, responses_mock):
    """Testing the correct behavior of the boosting."""
    with open('resources/test/ohsome_line_response.geojson', 'rb') as vector:
        responses_mock.post(
            'https://api.ohsome.org/v1/elements/geometry',
            body=vector.read(),
        )

    paths_input = gpd.GeoDataFrame(
        data={
            'category': [
                PathCategory.NOT_BIKEABLE,  # overlapping, but not in boostable categories -> should stay
                PathCategory.UNKNOWN,  # not overlapping, but in boostable categories -> should stay
                PathCategory.UNKNOWN,  # overlapping and in boostable categories -> should be boosted
            ]
        },
        geometry=[
            shapely.LineString([(12.3, 48.22), (12.3, 48.2205), (12.3005, 48.22)]),
            shapely.LineString([(12.3, 48.22), (12.3005, 48.2208), (12.3010, 48.22)]),
            shapely.LineString([(12.3, 48.22), (12.3, 48.2205), (12.3005, 48.22)]),
        ],
        crs=4326,
    )

    expected_output = pd.Series(
        data=[PathCategory.NOT_BIKEABLE, PathCategory.UNKNOWN, PathCategory.DESIGNATED_EXCLUSIVE], name='category'
    )

    computed_output = boost_route_members(expected_compute_input.get_aoi_geom(), paths_input, OhsomeClient())
    pd.testing.assert_series_equal(computed_output, expected_output)


def test_boost_route_members_overlapping_routes(expected_compute_input, responses_mock):
    """
    Testing the case if routes are overlapping themselves (i.e. two identical lines in the response of the route query).
    """
    with open('resources/test/ohsome_route_response.geojson', 'rb') as vector:
        responses_mock.post(
            'https://api.ohsome.org/v1/elements/geometry',
            body=vector.read(),
        )

    paths_input = gpd.GeoDataFrame(
        data={'category': [PathCategory.UNKNOWN]},
        geometry=[
            shapely.LineString([(0, 0), (1, 1)]),
        ],
        crs=4326,
    )

    expected_output = pd.Series(data=[PathCategory.DESIGNATED_EXCLUSIVE], name='category')

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


@pytest.mark.parametrize('geometry_type', ['line', 'polygon'])
def test_ohsome_filter(geometry_type):
    verify(ohsome_filter(geometry_type), options=NamerFactory.with_parameters(geometry_type))
