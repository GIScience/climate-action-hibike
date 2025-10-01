import uuid

import geopandas as gpd
import pytest
import responses
import shapely
from climatoology.base.baseoperator import AoiProperties
from climatoology.base.computation import ComputationScope

from bikeability.indicators.path_categories import PathCategory
from bikeability.input import ComputeInputBikeability
from bikeability.operator_worker import OperatorBikeability
from test.utils import filter_start_matcher


@pytest.fixture
def expected_compute_input() -> ComputeInputBikeability:
    return ComputeInputBikeability()


@pytest.fixture
def default_aoi() -> shapely.MultiPolygon:
    return shapely.MultiPolygon(
        polygons=[
            [
                [
                    [12.3, 48.22],
                    [12.3, 48.34],
                    [12.48, 48.34],
                    [12.48, 48.22],
                    [12.3, 48.22],
                ]
            ]
        ]
    )


@pytest.fixture
def default_aoi_properties() -> AoiProperties:
    return AoiProperties(name='Heidelberg', id='heidelberg')


# The following fixtures can be ignored on plugin setup
@pytest.fixture
def compute_resources():
    with ComputationScope(uuid.uuid4()) as resources:
        yield resources


@pytest.fixture()
def responses_mock():
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture
def operator():
    return OperatorBikeability()


@pytest.fixture
def ohsome_api_osm(responses_mock):
    with (
        open('resources/test/ohsome_line_response.geojson', 'r') as line_file,
        open('resources/test/ohsome_polygon_response.geojson', 'r') as polygon_file,
    ):
        line_body = line_file.read()
        polygon_body = polygon_file.read()

    responses_mock.post(
        'https://api.ohsome.org/v1/elements/geometry',
        body=line_body,
        match=[filter_start_matcher('geometry:line and (highway')],
    )
    responses_mock.post(
        'https://api.ohsome.org/v1/elements/geometry',
        body=polygon_body,
        match=[filter_start_matcher('geometry:polygon and (highway')],
    )

    return responses_mock


@pytest.fixture
def ohsome_api_zebra(responses_mock):
    with open('resources/test/ohsome_node_response.geojson', 'r') as node_file:
        node_body = node_file.read()

    responses_mock.post(
        'https://api.ohsome.org/v1/elements/geometry',
        body=node_body,
        match=[filter_start_matcher('geometry:point')],
    )

    return responses_mock


@pytest.fixture
def ohsome_api_parking(responses_mock):
    with (
        open('resources/test/ohsome_parking_response.geojson', 'r') as parking_line_file,
        open('resources/test/ohsome_parking_response.geojson', 'r') as parking_polygon_file,
    ):
        parking_line_body = parking_line_file.read()
        parking_polygon_body = parking_polygon_file.read()

    responses_mock.post(
        'https://api.ohsome.org/v1/elements/geometry',
        body=parking_line_body,
        match=[filter_start_matcher('geometry:line and amenity=parking')],
    )
    responses_mock.post(
        'https://api.ohsome.org/v1/elements/geometry',
        body=parking_polygon_body,
        match=[filter_start_matcher('geometry:polygon and amenity=parking')],
    )

    return responses_mock


@pytest.fixture
def ohsome_api_count(responses_mock):
    with open('resources/test/ohsome_count_response.json', 'rb') as paths_count_file:
        paths_count_body = paths_count_file.read()

    responses_mock.post(
        'https://api.ohsome.org/v1/elements/count',
        body=paths_count_body,
    )

    return responses_mock


@pytest.fixture
def test_line() -> gpd.GeoDataFrame:
    line_geom = shapely.LineString([(12.3, 48.22), (12.3, 48.2205), (12.3005, 48.22)])
    return gpd.GeoDataFrame(
        data={
            '@osmId': ['way/171574582', 'way/171574582'],
            'category': [
                PathCategory.NO_ACCESS,
                PathCategory.SHARED_WITH_PEDESTRIANS,
            ],
            'geometry': [line_geom, line_geom],
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
        crs='EPSG:4326',
    )


@pytest.fixture
def test_polygon() -> gpd.GeoDataFrame:
    polygon_geom = shapely.Polygon(((12.3, 48.22), (12.3, 48.2205), (12.3005, 48.22), (12.3, 48.22)))
    return gpd.GeoDataFrame(
        data={
            '@osmId': ['way/171574582'],
            'category': [PathCategory.NO_ACCESS],
            'geometry': [polygon_geom],
            '@other_tags': [{'bicycle': 'no'}],
        },
        crs='EPSG:4326',
    )


@pytest.fixture
def test_polygon_empty() -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        data={
            '@osmId': [],
            'geometry': [],
            '@other_tags': [],
        },
        crs='EPSG:4326',
    )


@pytest.fixture
def expected_parking_polygon() -> gpd.GeoDataFrame:
    polygon_geom = shapely.from_wkt(
        'POLYGON ((8.45979 49.4326487, 8.4597687 49.4326603, 8.4597353 49.4326784, 8.4594568 49.4324616, 8.4594874 49.432445, 8.4595115 49.4324319, 8.4597393 49.4326092, 8.45979 49.4326487))'
    )
    return gpd.GeoDataFrame(
        data={
            '@osmId': ['way/1205391562'],
            'geometry': [polygon_geom],
            '@other_tags': [
                {
                    'amenity': 'parking',
                    'orientation': 'parallel',
                    'parking': 'street_side',
                }
            ],
        },
        crs='EPSG:4326',
    )
