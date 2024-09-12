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
        purpose='This is a dummy for the rework of the plugin.',
        methodology='The dummy is based on the functionality of walkability.',
        sources=Path('resources/literature.bib'),
    )


@pytest.fixture
def expected_compute_output(compute_resources) -> List[_Artifact]:
    paths_artifact = _Artifact(
        name='Cycling infrastructure path categories',
        modality=ArtifactModality.MAP_LAYER_GEOJSON,
        file_path=Path(compute_resources.computation_dir / 'cycling_infrastructure_path_categories.geojson'),
        summary='TBD',
        description='TBD',
        attachments={
            AttachmentType.LEGEND: Legend(
                legend_data={
                    'designated': Color('#006837'),
                    'forbidden': Color('#a50026'),
                    'not_categorised': Color('grey'),
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
        open('resources/test/ohsome_line_and_polygon_response.geojson', 'r') as line_and_polygon_file,
        open('resources/test/ohsome_route_response.geojson', 'r') as route_file,
    ):
        line_and_polygon_body = line_and_polygon_file.read()
        route_body = route_file.read()
    responses_mock.post(
        'https://api.ohsome.org/v1/elements/geometry',
        body=line_and_polygon_body,
        match=[filter_start_matcher('(geometry:line or geometry:polygon)')],
    )
    responses_mock.post(
        'https://api.ohsome.org/v1/elements/geometry',
        body=route_body,
        match=[filter_start_matcher('route in (bicycle)')],
    )
    return responses_mock
