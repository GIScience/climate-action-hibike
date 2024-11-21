from geopandas import testing

from bikeability.indicators.path_categories import PathCategory, categorize_paths
from bikeability.indicators.smoothness import SmoothnessCategory
from bikeability.indicators.dooring_risk import DooringRiskCategory


def test_input_categories_match_pydantic_categories(expected_compute_input):
    input_path_rating = expected_compute_input.get_path_rating_mapping()
    input_smoothness_rating = expected_compute_input.get_path_smoothness_mapping()
    input_dooring_rating = expected_compute_input.get_path_dooring_mapping()

    assert set(input_path_rating.keys()) == set(PathCategory)
    assert set(input_smoothness_rating.keys()) == set(SmoothnessCategory)
    assert set(input_dooring_rating.keys()) == set(DooringRiskCategory)


def test_categorize_paths(test_line, test_polygon, expected_compute_input):
    input_line = test_line.drop(['category', 'rating'], axis=1)
    input_polygon = test_polygon.drop(['category', 'rating'], axis=1)

    expected_lines = test_line
    expected_polygons = test_polygon

    computed_lines, computed_polygons = categorize_paths(
        input_line, input_polygon, expected_compute_input.get_path_rating_mapping()
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
