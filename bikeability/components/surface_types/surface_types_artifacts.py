from pathlib import Path

import geopandas as gpd
from climatoology.base.artifact import Artifact, ArtifactMetadata, Legend
from climatoology.base.artifact_creators import create_vector_artifact
from climatoology.base.computation import ComputationResources
from pydantic_extra_types.color import Color

from bikeability.components.surface_types.surface_types import SurfaceType
from bikeability.components.utils.colors import get_qualitative_color
from bikeability.components.utils.utils import Topics


def build_surface_types_artifact(
    surface_type_paths: gpd.GeoDataFrame,
    resources: ComputationResources,
    cmap_name: str = 'tab20',
) -> Artifact:
    # Define color and legend
    legend_data = {}
    for surface_type in SurfaceType.get_visible():
        legend_color = get_qualitative_color(surface_type, cmap_name)
        legend_data[surface_type.value] = legend_color if legend_color != Color('#7f7f7f') else Color('#3c3c3c')

    surface_type_paths['color'] = surface_type_paths.surface_type.apply(
        lambda path_surface_type: legend_data[path_surface_type.value]
    )
    surface_type_paths['label'] = surface_type_paths.surface_type.apply(lambda r: r.name)

    metadata = ArtifactMetadata(
        name='Surface Types',
        summary=Path('resources/info/surface_types/summary.md').read_text(),
        description=Path('resources/info/surface_types/description.md').read_text(),
        tags={Topics.SURFACE},
        filename='surface_types',
    )

    return create_vector_artifact(
        data=surface_type_paths[['@osmId', 'color', 'label', 'geometry']],
        metadata=metadata,
        resources=resources,
        legend=Legend(legend_data=legend_data),
    )
