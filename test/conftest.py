import uuid
from pathlib import Path
from typing import List
from unittest.mock import patch

import pytest
import rasterio
import responses
from climatoology.base.artifact import ArtifactModality
from climatoology.base.computation import ComputationScope
from climatoology.base.operator import Concern, Info, PluginAuthor, _Artifact
from semver import Version

from plugin_blueprint.input import ComputeInput
from plugin_blueprint.operator_worker import OperatorBlueprint


@pytest.fixture
def expected_compute_input() -> ComputeInput:
    # noinspection PyTypeChecker
    return ComputeInput(
        bool_blueprint=True,
        aoi_blueprint={
            'type': 'Feature',
            'properties': None,
            'geometry': {
                'type': 'MultiPolygon',
                'coordinates': [
                    [
                        [
                            [12.3, 48.22],
                            [12.3, 48.34],
                            [12.48, 48.34],
                            [12.48, 48.22],
                            [12.3, 48.22],
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
        name='Plugin Blueprint',
        icon=Path('resources/info/icon.jpeg'),
        authors=[
            PluginAuthor(
                name='Moritz Schott',
                affiliation='HeiGIT gGmbH',
                website='https://heigit.org/heigit-team/',
            ),
            PluginAuthor(
                name='Maciej Adamiak',
                affiliation='Consultant at HeiGIT gGmbH',
                website='https://heigit.org/heigit-team/',
            ),
        ],
        version=Version(0, 0, 1),
        concerns=[Concern.CLIMATE_ACTION__GHG_EMISSION],
        purpose=Path('resources/info/purpose.md').read_text(),
        methodology=Path('resources/info/methodology.md').read_text(),
        sources=Path('resources/info/sources.bib'),
    )


@pytest.fixture
def expected_compute_output(compute_resources) -> List[_Artifact]:
    markdown_artifact = _Artifact(
        name='A Text',
        modality=ArtifactModality.MARKDOWN,
        file_path=Path(compute_resources.computation_dir / 'markdown_blueprint.md'),
        summary='A JSON-block of the input parameters',
    )
    table_artifact = _Artifact(
        name='Character Count',
        modality=ArtifactModality.TABLE,
        file_path=Path(compute_resources.computation_dir / 'table_blueprint.csv'),
        summary='The table lists the number of occurrences for each character in the input parameters.',
        description='A table with two columns.',
    )
    image_artifact = _Artifact(
        name='Image',
        modality=ArtifactModality.IMAGE,
        file_path=Path(compute_resources.computation_dir / 'image_blueprint.png'),
        summary='A nice image.',
        description='The image is under CC0 license taken from [pexels](https://www.pexels.com/'
        'photo/person-holding-a-green-plant-1072824/).',
    )
    scatter_chart_artifact = _Artifact(
        name='The Points',
        modality=ArtifactModality.CHART,
        file_path=Path(compute_resources.computation_dir / 'scatter_chart_blueprint.json'),
        summary='A simple scatter plot.',
        description='Beautiful points.',
    )
    line_chart_artifact = _Artifact(
        name='The Line',
        modality=ArtifactModality.CHART,
        file_path=Path(compute_resources.computation_dir / 'line_chart_blueprint.json'),
        summary='A simple line of negative incline.',
    )
    bar_chart_artifact = _Artifact(
        name='The Bars',
        modality=ArtifactModality.CHART,
        file_path=Path(compute_resources.computation_dir / 'bar_chart_blueprint.json'),
        summary='A simple bar chart.',
    )
    pie_chart_artifact = _Artifact(
        name='The Pie',
        modality=ArtifactModality.CHART,
        file_path=Path(compute_resources.computation_dir / 'pie_chart_blueprint.json'),
        summary='A simple pie.',
    )
    point_artifact = _Artifact(
        name='Points',
        modality=ArtifactModality.MAP_LAYER_GEOJSON,
        file_path=Path(compute_resources.computation_dir / 'points_blueprint.geojson'),
        summary='Schools in the area of interest including a dummy school in the center.',
        description='The schools are taken from OSM at the date given in the input form.',
    )
    line_artifact = _Artifact(
        name='Lines',
        modality=ArtifactModality.MAP_LAYER_GEOJSON,
        file_path=Path(compute_resources.computation_dir / 'lines_blueprint.geojson'),
        summary='Buffers around schools in the area of interest including a dummy school in the center.',
        description='The schools are taken from OSM at the date given in the input form.',
    )
    polygon_artifact = _Artifact(
        name='Polygons',
        modality=ArtifactModality.MAP_LAYER_GEOJSON,
        file_path=Path(compute_resources.computation_dir / 'polygons_blueprint.geojson'),
        summary='Schools in the area of interest including a dummy school in the center, buffered by ca. 100m.',
        description='The schools are taken from OSM at the date given in the input form.',
    )
    raster_artifact = _Artifact(
        name='LULC Classification',
        modality=ArtifactModality.MAP_LAYER_GEOTIFF,
        file_path=Path(compute_resources.computation_dir / 'raster_blueprint.tiff'),
        summary='A land-use and land-cover classification of a user defined area.',
        description='The classification is created using a deep learning model.',
    )
    return [
        markdown_artifact,
        table_artifact,
        image_artifact,
        scatter_chart_artifact,
        line_chart_artifact,
        bar_chart_artifact,
        pie_chart_artifact,
        point_artifact,
        line_artifact,
        polygon_artifact,
        raster_artifact,
    ]


# The following fixtures can be ignored on plugin setup
@pytest.fixture
def compute_resources():
    with ComputationScope(uuid.uuid4()) as resources:
        yield resources


@pytest.fixture
def operator(lulc_utility):
    return OperatorBlueprint(lulc_utility)


@pytest.fixture
def ohsome_api():
    with responses.RequestsMock() as rsps, open('resources/test/ohsome.geojson', 'rb') as vector:
        rsps.post('https://api.ohsome.org/v1/elements/centroid', body=vector.read())
        yield rsps


@pytest.fixture
def lulc_utility():
    with patch('climatoology.utility.api.LulcUtility') as lulc_utility:
        lulc_utility.compute_raster.return_value.__enter__.return_value = rasterio.open(
            'resources/test/segmentation.tiff'
        )
        yield lulc_utility
