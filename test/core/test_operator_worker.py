import pytest


@pytest.mark.vcr
def test_get_paths(operator, parametrized_ohsome_client, small_aoi):
    operator.ohsome = parametrized_ohsome_client
    received_paths = operator.get_paths(small_aoi)

    assert set(received_paths.columns) >= {'osm_id', 'osm_type', 'geometry', 'osm_tags'}


@pytest.mark.vcr
def test_get_parking(operator, parametrized_ohsome_client, default_aoi):
    operator.ohsome = parametrized_ohsome_client
    computed_parking_polygon = operator.get_parallel_parking(default_aoi)

    assert set(computed_parking_polygon.columns) >= {'osm_id', 'osm_type', 'geometry', 'osm_tags'}
