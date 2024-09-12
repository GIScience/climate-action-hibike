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
    get_color,
    get_single_color,
)


def build_paths_artifact(
    paths_line: gpd.GeoDataFrame,
    paths_polygon: gpd.GeoDataFrame,
    ratings: PathRating,
    clip_aoi: shapely.MultiPolygon,
    resources: ComputationResources,
    cmap_name: str = 'RdYlGn',
) -> _Artifact:
    paths_line = paths_line.clip(clip_aoi, keep_geom_type=True)
    paths_polygon = paths_polygon.clip(clip_aoi, keep_geom_type=True)
    paths_all = pd.concat([paths_line, paths_polygon], ignore_index=True)

    paths_all['color'] = get_color(paths_all.rating, cmap_name)
    return create_geojson_artifact(
        features=paths_all.geometry,
        layer_name='Cycling infrastructure path categories',
        caption='TBD',
        description='TBD',
        label=paths_all.category.apply(lambda r: r.name).to_list(),
        color=paths_all.color.to_list(),
        legend_data={rating[0]: get_single_color(rating[1]) for rating in ratings},
        resources=resources,
        filename='cycling_infrastructure_path_categories',
    )
