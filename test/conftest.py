import uuid
from pathlib import Path
from typing import List

import pytest
import responses
from climatoology.base.artifact import ArtifactModality, AttachmentType, Legend
from climatoology.base.computation import ComputationScope
from climatoology.base.operator import Concern, Info, PluginAuthor, _Artifact
from pydantic_extra_types.color import Color
from semver import Version

from bikeability.input import ComputeInputBikeability
from bikeability.operator_worker import OperatorBikeability
from bikeability.utils import filter_start_matcher


@pytest.fixture
def expected_compute_input() -> ComputeInputBikeability:
    # noinspection PyTypeChecker
    return ComputeInputBikeability(
        aoi={
            'type': 'Feature',
            'properties': {'name': 'Heidelberg', 'id': 'Q12345'},
            'geometry': {
                'type': 'MultiPolygon',
                'coordinates': [
                    [
                        [
                            [12.300, 48.220],
                            [12.300, 48.221],
                            [12.301, 48.221],
                            [12.301, 48.220],
                            [12.300, 48.220],
                        ]
                    ]
                ],
            },
        },
    )


@pytest.fixture
def expected_info_output() -> Info:
    # noinspection PyTypeChecker
    return Info(
        name='Bikeability',
        icon=Path('resources/info/icon.jpeg'),
        authors=[
            PluginAuthor(
                name='Jonas Kemmer',
                affiliation='HeiGIT gGmbH',
                website='https://heigit.org/heigit-team/',
            ),
            PluginAuthor(
                name='Moritz Schott',
                affiliation='HeiGIT gGmbH',
                website='https://heigit.org/heigit-team/',
            ),
        ],
        version=Version(0, 0, 1),
        concerns=[Concern.MOBILITY_CYCLING],
        purpose=Path('resources/info/purpose.md').read_text(),
        methodology=Path('resources/info/methodology.md').read_text(),
        sources=Path('resources/literature.bib'),
    )


@pytest.fixture
def expected_compute_output(compute_resources) -> List[_Artifact]:
    paths_artifact = _Artifact(
        name='Cycling infrastructure path categories',
        modality=ArtifactModality.MAP_LAYER_GEOJSON,
        file_path=Path(compute_resources.computation_dir / 'cycling_infrastructure_path_categories.geojson'),
        summary=Path('resources/info/path_categories/caption.md').read_text(),
        description=Path('resources/info/path_categories/description.md').read_text(),
        attachments={
            AttachmentType.LEGEND: Legend(
                legend_data={
                    'designated_exclusive': Color('#313695'),
                    'designated_shared_with_pedestrians': Color('#5183bb'),
                    'shared_with_motorised_traffic_walking_speed_(<=15_km/h)': Color('#90c3dd'),
                    'shared_with_motorised_traffic_low_speed_(<=30_km/h)': Color('#d4edf4'),
                    'shared_with_motorised_traffic_medium_speed_(<=50_km/h)': Color('#fffebe'),
                    'shared_with_motorised_traffic_high_speed_(<=100_km/h)': Color('#fed283'),
                    'requires_dismounting': Color('#f88c51'),
                    'not_bikeable': Color('#dd3d2d'),
                    'unknown': Color('grey'),
                }
            )
        },
    )

    return [paths_artifact]


# The following fixtures can be ignored on plugin setup
@pytest.fixture
def compute_resources():
    with ComputationScope(uuid.uuid4()) as resources:
        yield resources


@pytest.fixture
def responses_mock():
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture
def operator():
    return OperatorBikeability()


@pytest.fixture
def ohsome_api(responses_mock):
    with (
        open('resources/test/ohsome_line_response.geojson', 'r') as line_file,
        open('resources/test/ohsome_polygon_response.geojson', 'r') as polygon_file,
        open('resources/test/ohsome_route_response.geojson', 'r') as route_file,
    ):
        line_body = line_file.read()
        polygon_body = polygon_file.read()
        route_body = route_file.read()
    responses_mock.post(
        'https://api.ohsome.org/v1/elements/geometry',
        body=line_body,
        match=[filter_start_matcher('geometry:line')],
    )
    responses_mock.post(
        'https://api.ohsome.org/v1/elements/geometry',
        body=polygon_body,
        match=[filter_start_matcher('geometry:polygon')],
    )
    responses_mock.post(
        'https://api.ohsome.org/v1/elements/geometry',
        body=route_body,
        match=[filter_start_matcher('route in (bicycle)')],
    )
    return responses_mock
