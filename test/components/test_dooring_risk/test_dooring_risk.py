import geopandas as gpd
import geopandas.testing
import pandas as pd
import pytest
import shapely
from approvaltests import verify
from ohsome import OhsomeClient
from ohsome_filter_to_sql.main import validate_filter
from pandas.testing import assert_series_equal

from bikeability.components.dooring_risk.dooring_risk import (
    DooringRiskCategory,
    apply_dooring_filters,
    find_nearest_parking,
    get_dooring_risk,
    parallel_parking_filter,
)
from bikeability.components.path_categories.path_categories import PathCategory
from bikeability.components.utils.utils import (
    fetch_osm_data,
)

expected_parking_line = gpd.GeoDataFrame(
    data={
        '@osmId': ['way/1205391562'],
        '@other_tags': [{'amenity': 'parking', 'orientation': 'parallel', 'parking': 'street_side'}],
    },
    geometry=[
        shapely.LineString([(12.3, 48.22), (12.3, 48.2205), (12.3005, 48.22)]),
    ],
    crs=4326,
)


expected_parking_polygon = gpd.GeoDataFrame(
    data={
        '@osmId': ['way/1205391562'],
        '@other_tags': [{'amenity': 'parking', 'orientation': 'parallel', 'parking': 'street_side'}],
    },
    geometry=[
        shapely.from_wkt(
            'POLYGON ((8.45979 49.4326487, 8.4597687 49.4326603, 8.4597353 49.4326784, 8.4594568 49.4324616, 8.4594874 49.432445, 8.4595115 49.4324319, 8.4597393 49.4326092, 8.45979 49.4326487))'
        ),
    ],
    crs=4326,
)


@pytest.fixture
def dooring_risk():
    tags = [
        {'parking:both:orientation': 'parallel'},
        {'parking:right:orientation': 'parallel'},
        {'parking:left:orientation': 'parallel'},
        {'parking:lane:both': 'parallel'},
        {'parking:lane:left': 'parallel'},
        {'parking:lane:right': 'parallel'},
        {'parking:both': 'separate'},
    ]

    parking = [False for _ in tags]
    parking[-1] = True
    dooring_risk_tags = pd.DataFrame(
        data={
            '@other_tags': tags,
            'expected_dooring_risk': [DooringRiskCategory.DOORING_RISK for _ in tags],
            'parking': parking,
            'category': [PathCategory.SHARED_WITH_MOTORISED_TRAFFIC_MEDIUM_SPEED for _ in tags],
        }
    )

    return dooring_risk_tags


@pytest.fixture
def dooring_safe():
    tags = [
        {'parking:lane:both': 'no'},
        {'parking:both:orientation': 'perpendicular'},
        {'parking:right:orientation': 'perpendicular', 'parking:left:orientation': 'perpendicular'},
        {'parking:left:orientation': 'perpendicular', 'parking:right': 'no'},
        {'parking:both:orientation': 'diagonal'},
        {'parking:left:orientation': 'diagonal', 'parking:right': 'no'},
        {'parking:right:orientation': 'diagonal', 'parking:left': 'no'},
        {'parking:both:orientation': 'parallel'},
    ]

    category = [PathCategory.SHARED_WITH_MOTORISED_TRAFFIC_MEDIUM_SPEED for _ in tags]
    category[-1] = PathCategory.EXCLUSIVE

    dooring_risk_tags = pd.DataFrame(
        data={
            '@other_tags': tags,
            'expected_dooring_risk': [DooringRiskCategory.DOORING_SAFE for _ in tags],
            'parking': [False for _ in tags],
            'category': category,
        }
    )

    return dooring_risk_tags


@pytest.fixture
def dooring_unknown():
    return pd.DataFrame(
        data={
            '@other_tags': [{}],
            'expected_dooring_risk': [DooringRiskCategory.UNKNOWN],
            'category': [PathCategory.SHARED_WITH_MOTORISED_TRAFFIC_LOW_SPEED],
            'parking': [False],
        }
    )


@pytest.fixture
def dooring_test_cases(dooring_risk, dooring_safe, dooring_unknown):
    return pd.concat([dooring_risk, dooring_safe, dooring_unknown])


def test_find_nearest_parking(responses_mock, default_aoi):
    with (
        open('resources/test/ohsome_line_response.geojson', 'rb') as line_file,
        open('resources/test/ohsome_parking_response.geojson', 'rb') as parking_file,
    ):
        responses_mock.post('https://api.ohsome.org/v1/elements/geometry', body=line_file.read())
        responses_mock.post('https://api.ohsome.org/v1/elements/geometry', body=parking_file.read())

    line_paths = fetch_osm_data(default_aoi, 'dummy=yes', OhsomeClient())
    line_paths = fetch_osm_data(default_aoi, 'dummy=yes', OhsomeClient())
    line_paths['category'] = None  # FIXME
    parking_polygons = fetch_osm_data(default_aoi, parallel_parking_filter('polygon'), OhsomeClient())

    line_paths_with_parking = find_nearest_parking(line_paths, parking_polygons)

    assert line_paths_with_parking.columns.to_list() == ['geometry', '@osmId', '@other_tags', 'parking', 'category']
    assert line_paths_with_parking.crs.to_epsg() == 4326


@pytest.mark.parametrize(
    'geometry_type, expected_parking_data, expected_geometry_type',
    [
        ('polygon', expected_parking_polygon, 'Polygon'),
    ],
)
def test_parking_filter(responses_mock, default_aoi, geometry_type, expected_parking_data, expected_geometry_type):
    with open('resources/test/ohsome_parking_response.geojson', 'rb') as vector:
        responses_mock.post(
            'https://api.ohsome.org/v1/elements/geometry',
            body=vector.read(),
        )

    fetch_parking_data = fetch_osm_data(default_aoi, parallel_parking_filter(geometry_type), OhsomeClient())

    geopandas.testing.assert_geodataframe_equal(fetch_parking_data, expected_parking_data, check_like=True)
    assert fetch_parking_data.geom_type[0] == expected_geometry_type


@pytest.mark.parametrize('geometry_type', ['line', 'polygon'])
def test_parking_filter_syntax(geometry_type):
    validate_filter(parallel_parking_filter(geometry_type))


def test_dooring_filter(dooring_test_cases):
    result = dooring_test_cases.apply(apply_dooring_filters, axis=1)

    assert_series_equal(result, dooring_test_cases['expected_dooring_risk'], check_names=False)


def test_get_dooring_risk(default_paths, expected_parking_polygon):
    result = get_dooring_risk(default_paths, expected_parking_polygon)
    verify(result.to_csv())


def test_get_dooring_risk_missing_geometry_types(test_line, test_polygon, expected_parking_polygon):
    dooring_risk_line_paths = get_dooring_risk(test_polygon, expected_parking_polygon)
    dooring_risk_polygon_paths = get_dooring_risk(test_line, expected_parking_polygon)

    result = pd.concat([dooring_risk_line_paths, dooring_risk_polygon_paths], ignore_index=True)
    verify(result.to_csv())
