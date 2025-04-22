import geopandas as gpd
import pytest
import shapely
from geopandas import testing

from bikeability.indicators.path_categories import (
    PathCategory,
    categorize_paths,
    recategorise_zebra_crossings,
)


@pytest.fixture
def test_line_with_crossing() -> gpd.GeoDataFrame:
    line_geom = shapely.LineString(
        [
            (8.692353, 49.413160),
            (8.692814, 49.413228),
            (8.692870, 49.413334),
            (8.6928656, 49.4133677),
            (8.692836, 49.413484),
        ]
    )
    return gpd.GeoDataFrame(
        data={
            'category': [PathCategory.DESIGNATED_EXCLUSIVE],
            'rating': [1.0],
            'geometry': [line_geom],
            '@other_tags': [{'highway': 'cycleway', 'bicycle': 'yes'}],
        },
        crs='EPSG:4326',
    )


@pytest.fixture
def test_crossing_nodes() -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        data={
            'geometry': [shapely.Point(8.6928656, 49.4133677), shapely.Point(8.692814, 49.413228)],
            '@other_tags': [
                {'crossing': 'uncontrolled', 'crossing:markings': 'zebra'},
                {'crossing': 'uncontrolled', 'crossing:markings': 'zebra'},
            ],
        },
        crs='EPSG:4326',
    )


def test_categorize_paths(test_line, test_polygon, expected_compute_input):
    input_line = test_line.drop(['category'], axis=1)
    input_polygon = test_polygon.drop(['category'], axis=1)

    expected_lines = test_line
    expected_polygons = test_polygon

    computed_lines, computed_polygons = categorize_paths(input_line, input_polygon)

    testing.assert_geodataframe_equal(
        computed_lines,
        expected_lines,
        check_like=True,
        check_geom_type=True,
        check_less_precise=True,
    )
    testing.assert_geodataframe_equal(
        computed_polygons,
        expected_polygons,
        check_like=True,
        check_geom_type=True,
        check_less_precise=True,
    )


def test_split_paths_around_crossing_single_crossing(test_line_with_crossing, test_crossing_nodes):
    computed_lines = recategorise_zebra_crossings(test_line_with_crossing, test_crossing_nodes.drop(1))
    assert len(computed_lines) == 3
    assert len(computed_lines[computed_lines['category'] == PathCategory.REQUIRES_DISMOUNTING]) == 1


def test_split_paths_around_crossing_multiple_crossings(test_line_with_crossing, test_crossing_nodes):
    computed_lines = recategorise_zebra_crossings(test_line_with_crossing, test_crossing_nodes)
    assert len(computed_lines) == 5
    assert len(computed_lines[computed_lines['category'] == PathCategory.REQUIRES_DISMOUNTING]) == 2
