from climatoology.base.artifact import _Artifact
from climatoology.base.info import _Info


def test_plugin_info_request(operator):
    assert isinstance(operator.info(), _Info)


def test_plugin_compute_request(
    operator,
    expected_compute_input,
    default_aoi,
    default_aoi_properties,
    compute_resources,
    ohsome_api_osm,
    ohsome_api_parking,
    ohsome_api_zebra,
):
    computed_artifacts = operator.compute(
        resources=compute_resources,
        aoi=default_aoi,
        aoi_properties=default_aoi_properties,
        params=expected_compute_input,
    )

    assert len(computed_artifacts) == 4
    for artifact in computed_artifacts:
        assert isinstance(artifact, _Artifact)
