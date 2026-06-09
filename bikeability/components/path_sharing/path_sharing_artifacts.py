from importlib.resources import read_text

import geopandas as gpd
from climatoology.base.artifact import Artifact, ArtifactMetadata, Legend
from climatoology.base.artifact_creators import create_vector_artifact
from climatoology.base.computation import ComputationResources

from bikeability.components.path_sharing.path_sharing import PathSharing
from bikeability.components.utils.colors import get_qualitative_color
from bikeability.components.utils.utils import Topics


def build_path_categories_artifact(
    paths: gpd.GeoDataFrame,
    resources: ComputationResources,
    cmap_name: str = 'coolwarm',
) -> Artifact:
    paths_without_restriction = paths[paths.path_sharing.isin(PathSharing.get_visible())].copy(deep=False)

    paths_without_restriction['color'] = paths_without_restriction.path_sharing.apply(
        get_qualitative_color, cmap_name=cmap_name
    )

    paths_without_restriction['label'] = paths_without_restriction.path_sharing.apply(lambda r: r.value)

    metadata = ArtifactMetadata(
        name='Path Sharing',
        primary=True,
        tags={Topics.TRAFFIC},
        summary=read_text('bikeability.resources.info.path_sharing', 'summary.md'),
        description=read_text('bikeability.resources.info.path_sharing', 'description.md'),
    )

    return create_vector_artifact(
        data=paths_without_restriction[['@osmId', 'color', 'label', 'geometry']],
        metadata=metadata,
        resources=resources,
        legend=Legend(
            title='Who Shares This Path with Me?',
            legend_data={
                category.value: get_qualitative_color(category, cmap_name) for category in PathSharing.get_visible()
            },
        ),
    )
