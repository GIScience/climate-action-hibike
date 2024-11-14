from geopandas import testing


def test_get_paths(operator, expected_compute_input, ohsome_api, test_line, test_polygon):
    expected_lines = test_line.drop(['category', 'rating'], axis=1)
    expected_polygons = test_polygon.drop(['category', 'rating'], axis=1)
    computed_lines, computed_polygons = operator.get_paths(expected_compute_input.get_aoi_geom())

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
