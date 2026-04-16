from importlib.resources import read_text

import geopandas as gpd
from climatoology.base.artifact import Artifact, ArtifactMetadata
from climatoology.base.artifact_creators import create_vector_artifact
from climatoology.base.computation import ComputationResources

from bikeability.components.utils.colors import get_qualitative_color
from bikeability.components.utils.utils import Topics


def build_smoothness_artifact(
    smoothness_paths: gpd.GeoDataFrame,
    resources: ComputationResources,
    cmap_name: str = 'coolwarm',
) -> Artifact:
    smoothness_paths['color'] = smoothness_paths.smoothness.apply(get_qualitative_color, cmap_name=cmap_name)
    smoothness_paths['label'] = smoothness_paths.smoothness.apply(lambda r: r.name)
    metadata = ArtifactMetadata(
        name='Path Smoothness',
        summary=read_text('resources.info.path_smoothness', 'summary.md'),
        description=read_text('resources.info.path_smoothness', 'description.md'),
        tags={Topics.SURFACE},
        filename='smoothness',
    )

    return create_vector_artifact(
        data=smoothness_paths[['@osmId', 'color', 'label', 'geometry']], resources=resources, metadata=metadata
    )
