from geopandas import testing

from bikeability.utils import filter_start_matcher


def test_get_paths(operator, expected_compute_input, default_aoi, test_line, test_polygon, responses_mock):
    expected_lines = test_line.drop(['category'], axis=1)
    expected_polygons = test_polygon.drop(['category'], axis=1)

    with (
        open('resources/test/ohsome_line_response.geojson', 'rb') as vector,
        open('resources/test/ohsome_polygon_response.geojson', 'rb') as polygon,
    ):
        responses_mock.post(
            'https://api.ohsome.org/v1/elements/geometry',
            body=vector.read(),
            match=[filter_start_matcher('geometry:line')],
        )
        responses_mock.post(
            'https://api.ohsome.org/v1/elements/geometry',
            body=polygon.read(),
            match=[filter_start_matcher('geometry:polygon')],
        )
        computed_lines, computed_polygons = operator.get_paths(default_aoi)

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
