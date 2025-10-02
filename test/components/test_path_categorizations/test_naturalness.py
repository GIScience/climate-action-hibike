import geopandas as gpd
import geopandas.testing as gpdtest
import pytest
import shapely
from climatoology.utility.Naturalness import NaturalnessIndex

# from climatoology.utility.Naturalness import NaturalnessIndex
from pyproj import CRS
from shapely import LineString

from bikeability.indicators.naturalness import _valid_path_lines, get_naturalness


@pytest.fixture
def naturalness_test_lines() -> gpd.GeoDataFrame:
    path_lines = gpd.GeoDataFrame(
        index=[1, 2, 3],
        geometry=[
            LineString([[12.4, 48.25], [12.4, 48.30]]),  # width = 0
            LineString([[12.41, 48.25], [12.41, 48.30]]),  # width = 0
            LineString([[12.4, 48.25], [12.45, 48.25]]),  # height = 0
        ],
        crs='EPSG:4326',
    )

    return path_lines


@pytest.fixture
def naturalness_test_polygons() -> gpd.GeoDataFrame:
    polygon_geom = shapely.Polygon(((12.3, 48.2), (12.3, 48.25), (12.35, 48.25), (12.3, 48.25)))
    polygons = gpd.GeoDataFrame(
        index=[1, 2],
        geometry=[polygon_geom, polygon_geom],
        crs='EPSG:4326',
    )

    return polygons


def test_pathnaturalness_valid_path_line(naturalness_utility_mock, naturalness_test_lines, naturalness_test_polygons):
    expected_valid_path_lines = gpd.GeoDataFrame(
        index=[1, 2, 3],
        geometry=[
            LineString([[12.4, 48.25], [12.4 + 0.000009, 48.30]]),  # width = 0
            LineString([[12.41, 48.25], [12.41 + 0.000009, 48.30]]),  # width = 0
            LineString([[12.4, 48.25], [12.45, 48.25 + 0.000009]]),  # height = 0
        ],
        crs='EPSG:4326',
    )

    computed_valid_path_lines = _valid_path_lines(naturalness_test_lines)

    gpdtest.assert_geodataframe_equal(computed_valid_path_lines, expected_valid_path_lines, check_like=True)


def test_get_naturalness(naturalness_utility_mock, naturalness_test_lines, naturalness_test_polygons):
    path_lines = gpd.GeoDataFrame(
        index=[1, 2, 3],
        geometry=[
            LineString([[12.4, 48.25], [12.4, 48.30]]),  # width = 0
            LineString([[12.41, 48.25], [12.41, 48.30]]),  # width = 0
            LineString([[12.4, 48.25], [12.45, 48.25]]),  # height = 0
        ],
        crs='EPSG:4326',
    )

    computed_naturalness = get_naturalness(
        path_lines=path_lines,
        path_polygons=naturalness_test_polygons,
        nature_utility=naturalness_utility_mock,
        nature_index=NaturalnessIndex.NDVI,
    )

    expected_naturalness = gpd.GeoDataFrame(
        index=[0, 1, 2, 3],
        geometry=[
            LineString([[12.4, 48.25], [12.4, 48.30]]),
            LineString([[12.41, 48.25], [12.41, 48.30]]),
            LineString([[12.4, 48.25], [12.4, 48.30]]),
            LineString([[12.41, 48.25], [12.41, 48.30]]),
        ],
        data={'naturalness': [0.6, 0.6, 0.6, 0.6]},  # Walkability: 0.5, 0.6
        crs=CRS.from_epsg(4326),
    )

    gpdtest.assert_geodataframe_equal(computed_naturalness, expected_naturalness, check_like=True)
