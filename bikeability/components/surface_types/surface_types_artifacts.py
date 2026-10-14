from importlib.resources import read_text

import geopandas as gpd
from climatoology.base.artifact import Artifact, ArtifactMetadata, Legend
from climatoology.base.artifact_creators import create_vector_artifact
from climatoology.base.computation import ComputationResources

from bikeability.components.surface_types.surface_types import SurfaceType
from bikeability.components.utils.utils import Topics


def build_surface_types_artifact(
    surface_type_paths: gpd.GeoDataFrame,
    resources: ComputationResources,
    cmap_name: str = 'tab20',
) -> Artifact:
    # Define color and legend
    legend_data = SurfaceType.get_qualitative_colors(colormap=cmap_name)

    surface_type_paths['label'] = surface_type_paths.surface_type.apply(lambda r: r.value)
    surface_type_paths['color'] = surface_type_paths.label.map(legend_data)

    metadata = ArtifactMetadata(
        name='Surface Types',
        summary=read_text('bikeability.resources.info.surface_types', 'summary.md'),
        description=read_text('bikeability.resources.info.surface_types', 'description.md'),
        tags={Topics.SURFACE},
        filename='surface_types',
    )

    return create_vector_artifact(
        data=surface_type_paths[['osm_id', 'osm_type', 'color', 'label', 'geometry']],
        metadata=metadata,
        resources=resources,
        legend=Legend(legend_data=legend_data),
    )
