import geopandas as gpd
import shapely
from geopandas import testing

from bikeability.utils import (
    PathCategory,
)


def test_get_paths(operator, expected_compute_input, ohsome_api):
    line_geom = shapely.LineString([(12.3, 48.22), (12.3, 48.2205), (12.3005, 48.22)])
    polygon_geom = shapely.Polygon(((12.3, 48.22), (12.3, 48.2205), (12.3005, 48.22), (12.3, 48.22)))

    expected_lines = gpd.GeoDataFrame(
        data={
            'category': [PathCategory.NOT_BIKEABLE],
            'rating': [0.0],
            'geometry': [line_geom],
            '@other_tags': [{'bicycle': 'no'}],
        },
        crs='EPSG:4326',
    )
    expected_polygons = gpd.GeoDataFrame(
        data={
            'category': [PathCategory.NOT_BIKEABLE],
            'rating': [0.0],
            'geometry': [polygon_geom],
            '@other_tags': [{'bicycle': 'no'}],
        },
        crs='EPSG:4326',
    )
    computed_lines, computed_polygons = operator.get_paths(
        expected_compute_input.get_aoi_geom(), expected_compute_input.get_path_rating_mapping()
    )

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


def test_input_categories_match_PathCategories(expected_compute_input):
    input_categories = expected_compute_input.get_path_rating_mapping()

    assert set(input_categories.keys()) == set(PathCategory)
