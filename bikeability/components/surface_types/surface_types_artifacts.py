from pathlib import Path

import geopandas as gpd
from climatoology.base.artifact import _Artifact, create_geojson_artifact
from climatoology.base.computation import ComputationResources
from pydantic_extra_types.color import Color

from bikeability.components.surface_types.surface_types import SurfaceType
from bikeability.components.utils.colors import get_qualitative_color
from bikeability.components.utils.utils import Topics


def build_surface_types_artifact(
    surface_type_paths: gpd.GeoDataFrame,
    resources: ComputationResources,
    cmap_name: str = 'tab20',
) -> _Artifact:
    # Define color and legend
    legend = {}
    for surface_type in SurfaceType.get_visible():
        legend_color = get_qualitative_color(surface_type, cmap_name)
        legend[surface_type.value] = legend_color if legend_color != Color('#7f7f7f') else Color('#3c3c3c')
    color = surface_type_paths.surface_type.apply(lambda path_surface_type: legend[path_surface_type.value])

    return create_geojson_artifact(
        features=surface_type_paths.geometry,
        layer_name='Surface Types',
        caption=Path('resources/info/surface_types/caption.md').read_text(),
        description=Path('resources/info/surface_types/description.md').read_text(),
        label=surface_type_paths.surface_type.apply(lambda r: r.name).to_list(),
        color=color,
        legend_data=legend,
        resources=resources,
        filename='',
        tags={Topics.SURFACE},
    )
