from pathlib import Path

import geopandas as gpd
import pandas as pd
import shapely
from pydantic_extra_types.color import Color
from climatoology.base.artifact import (
    _Artifact,
    create_geojson_artifact,
)
from climatoology.base.computation import ComputationResources

from bikeability.indicators.dooring_risk import DooringRiskCategory
from bikeability.indicators.smoothness import SmoothnessCategory
from bikeability.indicators.surface_types import SurfaceType
from bikeability.indicators.path_categories import PathCategory, path_ratings_legend_fix
from bikeability.utils import (
    get_qualitative_color,
)


def build_path_categories_artifact(
    paths_line: gpd.GeoDataFrame,
    paths_polygon: gpd.GeoDataFrame,
    clip_aoi: shapely.MultiPolygon,
    resources: ComputationResources,
    cmap_name: str = 'RdYlBu_r',
) -> _Artifact:
    paths_line = paths_line.clip(clip_aoi, keep_geom_type=True)
    paths_polygon = paths_polygon.clip(clip_aoi, keep_geom_type=True)
    paths_all = pd.concat([paths_line, paths_polygon], ignore_index=True)

    paths_without_restriction = paths_all[paths_all.category.isin(PathCategory.get_visible())]

    paths_without_restriction['color'] = paths_without_restriction.category.apply(
        get_qualitative_color, cmap_name=cmap_name
    )
    return create_geojson_artifact(
        features=paths_without_restriction.geometry,
        layer_name='Bikeable Path Categories',
        caption=Path('resources/info/path_categories/caption.md').read_text(),
        description=Path('resources/info/path_categories/description.md').read_text(),
        label=paths_without_restriction.category.apply(lambda r: r.name).to_list(),
        color=paths_without_restriction.color.to_list(),
        legend_data={
            path_ratings_legend_fix.get(category.value, category.value): get_qualitative_color(category, cmap_name)
            for category in PathCategory.get_visible()
        },
        resources=resources,
        filename='cycling_infrastructure_path_categories',
    )


def build_smoothness_artifact(
    paths_line: gpd.GeoDataFrame,
    clip_aoi: shapely.MultiPolygon,
    resources: ComputationResources,
    cmap_name: str = 'RdYlBu_r',
) -> _Artifact:
    paths_line = paths_line.clip(clip_aoi, keep_geom_type=True)

    paths_line['color'] = paths_line.smoothness.apply(get_qualitative_color, cmap_name=cmap_name)

    return create_geojson_artifact(
        features=paths_line.geometry,
        layer_name='Path Smoothness',
        caption=Path('resources/info/path_smoothness/caption.md').read_text(),
        description=Path('resources/info/path_smoothness/description.md').read_text(),
        label=paths_line.smoothness.apply(lambda r: r.name).to_list(),
        color=paths_line.color.to_list(),
        legend_data={
            category.value: get_qualitative_color(category, cmap_name) for category in SmoothnessCategory.get_visible()
        },
        resources=resources,
        filename='cycling_infrastructure_path_smoothness',
    )


def build_surface_types_artifact(
    paths_line: gpd.GeoDataFrame,
    clip_aoi: shapely.MultiPolygon,
    resources: ComputationResources,
    cmap_name: str = 'Spectral_r',
) -> _Artifact:
    paths_line = paths_line.clip(clip_aoi, keep_geom_type=True)
    paths_line['color'] = paths_line.surface_type.apply(get_qualitative_color, cmap_name=cmap_name)
    return create_geojson_artifact(
        features=paths_line.geometry,
        layer_name='Surface Types',
        caption=Path('resources/info/surface_types/caption.md').read_text(),
        description=Path('resources/info/surface_types/description.md').read_text(),
        label=paths_line.surface_type.apply(lambda r: r.name).to_list(),
        color=paths_line.color.to_list(),
        legend_data={
            surface_type.value: get_qualitative_color(surface_type, cmap_name)
            for surface_type in SurfaceType.get_visible()
        },
        resources=resources,
        filename='surface_types',
    )


def build_dooring_artifact(
    paths_line: gpd.GeoDataFrame,
    clip_aoi: shapely.MultiPolygon,
    resources: ComputationResources,
) -> _Artifact:
    paths_line = paths_line.clip(clip_aoi, keep_geom_type=True)
    legend = {
        DooringRiskCategory.DOORING_SAFE.value: Color('#313695'),
        DooringRiskCategory.DOORING_RISK.value: Color('#f00000'),
        DooringRiskCategory.UNKNOWN.value: Color('grey'),
    }

    def get_dooring_colors(category: DooringRiskCategory, legend: dict[str:SmoothnessCategory]) -> Color:
        return legend[category.value]

    paths_line['color'] = paths_line.dooring_category.apply(get_dooring_colors, legend=legend)

    return create_geojson_artifact(
        features=paths_line.geometry,
        layer_name='Dooring Risk',
        caption=Path('resources/info/dooring_risk/caption.md').read_text(),
        description=Path('resources/info/dooring_risk/description.md').read_text(),
        label=paths_line.dooring_category.apply(lambda r: r.name).to_list(),
        color=paths_line.color.to_list(),
        legend_data=legend,
        resources=resources,
        filename='cycling_infrastructure_dooring_risk',
    )
