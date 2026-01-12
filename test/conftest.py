import uuid
from unittest.mock import patch

import geopandas as gpd
import pandas as pd
import pytest
import responses
import shapely
from climatoology.base.baseoperator import AoiProperties
from climatoology.base.computation import ComputationScope
from climatoology.utility.api import TimeRange
from climatoology.utility.naturalness import NaturalnessIndex
from mobility_tools.ors_settings import ORSSettings

from bikeability.components.path_categories.path_categories import PathCategory
from bikeability.core.input import ComputeInputBikeability
from bikeability.core.operator_worker import OperatorBikeability
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
            ]  # type: ignore
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
def default_ors_settings() -> ORSSettings:
    return ORSSettings()


@pytest.fixture
def operator(default_ors_settings, naturalness_utility_mock):
    return OperatorBikeability(naturalness_utility_mock, default_ors_settings)


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
def default_paths(test_line, test_polygon):
    return pd.concat([test_line, test_polygon], ignore_index=True)


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


@pytest.fixture
def naturalness_utility_mock():
    def mock_get_vector(
        index: NaturalnessIndex,
        aggregation_stats: list[str],
        vectors: list[gpd.GeoSeries],
        time_range: TimeRange,
        resolution: int = 90,
        max_raster_size: int = 1000,
    ) -> gpd.GeoDataFrame:
        lines = gpd.GeoSeries(
            index=[1, 2],
            data=[
                shapely.LineString([[12.4, 48.25], [12.4, 48.30]]),
                shapely.LineString([[12.41, 48.25], [12.41, 48.30]]),
            ],
            crs='EPSG:4326',
        )
        polygons = gpd.GeoSeries(index=[3], data=[shapely.Polygon([[12.4, 48.25], [12.4, 48.30], [12.41, 48.30]])])
        line_vectors = gpd.GeoDataFrame(index=[1, 2], data={'median': [0.6, 0.6]}, geometry=lines, crs='EPSG:4326')
        polygon_vectors = gpd.GeoDataFrame(index=[3], data={'median': [0.6]}, geometry=polygons, crs='EPSG:4326')

        if vectors[0].iloc[0].geom_type == 'LineString':
            return line_vectors
        elif vectors[0].iloc[0].geom_type == 'Polygon':
            return polygon_vectors

        raise ValueError

    with patch('climatoology.utility.naturalness.NaturalnessUtility') as naturalness_utility:
        naturalness_utility.compute_vector.side_effect = mock_get_vector
        yield naturalness_utility


@pytest.fixture
def expected_detour_factors() -> gpd.GeoDataFrame:
    detour_factors = pd.DataFrame(
        data={
            'detour_factor': [
                1.3995538900828162,
                1.219719961221372,
                1.454343083874761,
                1.7969363677141994,
                1.4832090368368422,
                2.8521635465676833,
                3.3880294081510607,
            ],
            'id': [
                '8a1faa996847fff',
                '8a1faa99684ffff',
                '8a1faa996857fff',
                '8a1faa99685ffff',
                '8a1faa9968c7fff',
                '8a1faa9968effff',
                '8a1faa996bb7fff',
            ],
        }
    ).set_index('id')
    return detour_factors.h3.h3_to_geo_boundary()


@pytest.fixture
def detour_factor_mock(expected_detour_factors):
    with patch('bikeability.components.detour_factors.detour_analysis.get_detour_factors') as get_detour_factors:
        get_detour_factors.return_value = expected_detour_factors
        yield get_detour_factors


@pytest.fixture
def default_path_geometry() -> shapely.LineString:
    return shapely.LineString([(12.3, 48.22), (12.3, 48.2205), (12.3005, 48.22)])


@pytest.fixture
def default_polygon_geometry() -> shapely.Polygon:
    return shapely.Polygon(((12.3, 48.22), (12.3, 48.2205), (12.3005, 48.22), (12.3, 48.22)))
