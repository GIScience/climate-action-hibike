from pathlib import Path

import geopandas as gpd
import pandas as pd
import shapely
from climatoology.base.artifact import (
    _Artifact,
    create_geojson_artifact,
)
from climatoology.base.computation import ComputationResources

from bikeability.input import PathRating
from bikeability.utils import (
    pathratings_legend_fix,
    get_qualitative_color,
    PathCategory,
)


def build_paths_artifact(
    paths_line: gpd.GeoDataFrame,
    paths_polygon: gpd.GeoDataFrame,
    ratings: PathRating,
    clip_aoi: shapely.MultiPolygon,
    resources: ComputationResources,
    cmap_name: str = 'RdYlBu_r',
) -> _Artifact:
    paths_line = paths_line.clip(clip_aoi, keep_geom_type=True)
    paths_polygon = paths_polygon.clip(clip_aoi, keep_geom_type=True)
    paths_all = pd.concat([paths_line, paths_polygon], ignore_index=True)

    paths_all['color'] = paths_all.category.apply(get_qualitative_color, cmap_name=cmap_name)
    return create_geojson_artifact(
        features=paths_all.geometry,
        layer_name='Cycling infrastructure path categories',
        caption=Path('resources/info/path_categories/caption.md').read_text(),
        description=Path('resources/info/path_categories/description.md').read_text(),
        label=paths_all.category.apply(lambda r: r.name).to_list(),
        color=paths_all.color.to_list(),
        legend_data={
            pathratings_legend_fix.get(category.value, category.value): get_qualitative_color(category, cmap_name)
            for category in PathCategory
        },
        resources=resources,
        filename='cycling_infrastructure_path_categories',
    )
