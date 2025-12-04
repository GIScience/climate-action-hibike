from pathlib import Path

import geopandas as gpd
from climatoology.base.artifact import _Artifact, create_geojson_artifact
from climatoology.base.computation import ComputationResources

from bikeability.components.smoothness.smoothness import SmoothnessCategory
from bikeability.components.utils.colors import get_qualitative_color
from bikeability.components.utils.utils import Topics


def build_smoothness_artifact(
    smoothness_paths: gpd.GeoDataFrame,
    resources: ComputationResources,
    cmap_name: str = 'coolwarm',
) -> _Artifact:
    smoothness_paths['color'] = smoothness_paths.smoothness.apply(get_qualitative_color, cmap_name=cmap_name)

    return create_geojson_artifact(
        features=smoothness_paths.geometry,
        layer_name='Path Smoothness',
        caption=Path('resources/info/path_smoothness/caption.md').read_text(),
        description=Path('resources/info/path_smoothness/description.md').read_text(),
        label=smoothness_paths.smoothness.apply(lambda r: r.name).to_list(),
        color=smoothness_paths.color.to_list(),
        legend_data={
            category.value: get_qualitative_color(category, cmap_name) for category in SmoothnessCategory.get_visible()
        },
        resources=resources,
        filename='cycling_infrastructure_path_smoothness',
        tags={Topics.SURFACE},
    )
