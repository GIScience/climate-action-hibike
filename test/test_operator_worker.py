from geopandas import testing


def test_get_paths(operator, expected_compute_input, default_aoi, ohsome_api_osm, test_line, test_polygon):
    expected_lines = test_line.drop(columns=['category'])
    expected_polygons = test_polygon.drop(columns=['category'])
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


def test_get_parking(operator, default_aoi, ohsome_api_parking, expected_parking_polygon):
    computed_parking_polygon = operator.get_parallel_parking(default_aoi)

    testing.assert_geodataframe_equal(
        computed_parking_polygon.drop_duplicates(subset=['@osmId', 'geometry']),
        expected_parking_polygon,
        check_like=True,
        check_geom_type=True,
        check_less_precise=True,
    )
