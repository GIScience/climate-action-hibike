from climatoology.base.artifact import Artifact
from climatoology.base.plugin_info import PluginInfo

from bikeability.core.input import BikeabilityIndicators


def test_plugin_info_request(operator):
    assert isinstance(operator.info(), PluginInfo)


def test_plugin_compute_request_minimal(
    operator,
    expected_compute_input,
    default_aoi,
    default_aoi_properties,
    compute_resources,
    ohsome_api_osm,
    ohsome_api_parking,
    ohsome_api_zebra,
    ohsome_api_count,
):
    computed_artifacts = operator.compute(
        resources=compute_resources,
        aoi=default_aoi,
        aoi_properties=default_aoi_properties,
        params=expected_compute_input,
    )

    assert len(computed_artifacts) == 5
    for artifact in computed_artifacts:
        assert isinstance(artifact, Artifact)


def test_plugin_compute_request_all_optionals(
    operator,
    expected_compute_input,
    default_aoi,
    default_aoi_properties,
    compute_resources,
    ohsome_api_osm,
    ohsome_api_parking,
    ohsome_api_zebra,
    ohsome_api_count,
    detour_factor_mock,
):
    expected_compute_input = expected_compute_input.model_copy(deep=True)
    expected_compute_input.optional_indicators = {e for e in BikeabilityIndicators}

    computed_artifacts = operator.compute(
        resources=compute_resources,
        aoi=default_aoi,
        aoi_properties=default_aoi_properties,
        params=expected_compute_input,
    )

    assert len(computed_artifacts) == 9
    for artifact in computed_artifacts:
        assert isinstance(artifact, Artifact)
