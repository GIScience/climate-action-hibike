from pathlib import Path

import geopandas as gpd
from climatoology.base.artifact import _Artifact, create_geojson_artifact
from climatoology.base.computation import ComputationResources

from bikeability.components.path_categories.path_categories import PathCategory
from bikeability.components.utils.colors import get_qualitative_color
from bikeability.components.utils.utils import Topics


def build_path_categories_artifact(
    paths: gpd.GeoDataFrame,
    resources: ComputationResources,
    cmap_name: str = 'coolwarm',
) -> _Artifact:
    paths_without_restriction = paths[paths.category.isin(PathCategory.get_visible())].copy(deep=False)

    paths_without_restriction['color'] = paths_without_restriction.category.apply(
        get_qualitative_color, cmap_name=cmap_name
    )
    return create_geojson_artifact(
        features=paths_without_restriction.geometry,
        layer_name='Path Categories',
        caption=Path('resources/info/path_categories/caption.md').read_text(),
        description=Path('resources/info/path_categories/description.md').read_text(),
        label=paths_without_restriction.category.apply(lambda r: r.name).to_list(),
        color=paths_without_restriction.color.to_list(),
        legend_data={
            category.value: get_qualitative_color(category, cmap_name) for category in PathCategory.get_visible()
        },
        resources=resources,
        filename='cycling_infrastructure_path_categories',
        tags={Topics.TRAFFIC},
    )
