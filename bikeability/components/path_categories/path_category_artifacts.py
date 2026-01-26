from pathlib import Path

import geopandas as gpd
from climatoology.base.artifact import Artifact, ArtifactMetadata, Legend
from climatoology.base.artifact_creators import create_vector_artifact
from climatoology.base.computation import ComputationResources

from bikeability.components.path_categories.path_categories import PathCategory
from bikeability.components.utils.colors import get_qualitative_color
from bikeability.components.utils.utils import Topics


def build_path_categories_artifact(
    paths: gpd.GeoDataFrame,
    resources: ComputationResources,
    cmap_name: str = 'coolwarm',
) -> Artifact:
    paths_without_restriction = paths[paths.category.isin(PathCategory.get_visible())].copy(deep=False)

    paths_without_restriction['color'] = paths_without_restriction.category.apply(
        get_qualitative_color, cmap_name=cmap_name
    )

    paths_without_restriction['label'] = paths_without_restriction.category.apply(lambda r: r.name)

    metadata = ArtifactMetadata(
        name='Path Categories',
        primary=True,
        tags={Topics.TRAFFIC},
        summary=Path('resources/info/path_categories/summary.md').read_text(),
        description=Path('resources/info/path_categories/description.md').read_text(),
    )

    return create_vector_artifact(
        data=paths_without_restriction[['@osmId', 'color', 'label', 'geometry']],
        metadata=metadata,
        resources=resources,
        legend=Legend(
            title='Who Shares This Path with Me?',
            legend_data={
                category.value: get_qualitative_color(category, cmap_name) for category in PathCategory.get_visible()
            },
        ),
    )
