from pathlib import Path

import geopandas as gpd
import pandas as pd
import shapely
from climatoology.base.artifact import (
    ContinuousLegendData,
    _Artifact,
    create_geojson_artifact,
    create_plotly_chart_artifact,
)
from climatoology.base.computation import ComputationResources
from climatoology.utility.exception import ClimatoologyUserError
from plotly.graph_objects import Figure
from pydantic_extra_types.color import Color

from bikeability.indicators.dooring_risk import DooringRiskCategory
from bikeability.indicators.path_categories import PathCategory
from bikeability.indicators.smoothness import SmoothnessCategory
from bikeability.indicators.surface_types import SurfaceType
from bikeability.utils import Topics, get_continuous_colors, get_qualitative_color


def build_path_categories_artifact(
    paths_line: gpd.GeoDataFrame,
    paths_polygon: gpd.GeoDataFrame,
    clip_aoi: shapely.MultiPolygon,
    resources: ComputationResources,
    cmap_name: str = 'coolwarm',
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


def build_smoothness_artifact(
    paths_line: gpd.GeoDataFrame,
    clip_aoi: shapely.MultiPolygon,
    resources: ComputationResources,
    cmap_name: str = 'coolwarm',
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
        tags={Topics.SURFACE},
    )


def build_surface_types_artifact(
    paths_line: gpd.GeoDataFrame,
    clip_aoi: shapely.MultiPolygon,
    resources: ComputationResources,
    cmap_name: str = 'tab20',
) -> _Artifact:
    paths_line = paths_line.clip(clip_aoi, keep_geom_type=True)

    # Define color and legend
    legend = {}
    for surface_type in SurfaceType.get_visible():
        legend_color = get_qualitative_color(surface_type, cmap_name)
        legend[surface_type.value] = legend_color if legend_color != Color('#7f7f7f') else Color('#3c3c3c')
    color = paths_line.surface_type.apply(lambda path_surface_type: legend[path_surface_type.value])

    return create_geojson_artifact(
        features=paths_line.geometry,
        layer_name='Surface Types',
        caption=Path('resources/info/surface_types/caption.md').read_text(),
        description=Path('resources/info/surface_types/description.md').read_text(),
        label=paths_line.surface_type.apply(lambda r: r.name).to_list(),
        color=color,
        legend_data=legend,
        resources=resources,
        filename='surface_types',
        tags={Topics.SURFACE},
    )


def build_aoi_summary_category_stacked_bar_artifact(
    aoi_aggregate: Figure, resources: ComputationResources
) -> _Artifact:
    return create_plotly_chart_artifact(
        figure=aoi_aggregate,
        title='Distribution of Path Categories',
        caption='How is the total length of paths distributed across the path categories?',
        resources=resources,
        filename='aggregation_aoi_category_stacked_bar',
        tags={Topics.TRAFFIC, Topics.SUMMARY},
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
        tags={Topics.TRAFFIC, Topics.SAFETY},
    )


def build_naturalness_artifact(
    paths_all: gpd.GeoDataFrame,
    clip_aoi: shapely.MultiPolygon,
    resources: ComputationResources,
    cmap_name: str = 'YlGn',
) -> list[_Artifact]:
    for path_geom_type in paths_all.geom_type.unique():
        paths_all[paths_all.geom_type == path_geom_type] = paths_all[paths_all.geom_type == path_geom_type].clip(
            clip_aoi, keep_geom_type=True
        )

    # If no good data is returned (e.g. due to an error), return a text artifact with a simple message
    if paths_all['naturalness'].isna().all():
        raise ClimatoologyUserError(
            'here was an error calculating greenness in this computation. '
            'The returned greenness is empty. '
            'Contact the developers for more information.'
        )

    # Set negative values (e.g. water) to 0, and set nan's to -999 to colour grey for unknown
    paths_all.loc[paths_all['naturalness'] < 0, 'naturalness'] = 0.0

    # Clean data for labels
    paths_all['naturalness'] = paths_all['naturalness'].round(2)

    # Define colors and legend
    color = get_continuous_colors(paths_all['naturalness'], cmap_name)
    legend = ContinuousLegendData(
        cmap_name=cmap_name,
        ticks={'Low (0)': 0.0, 'High (1)': 1.0},
    )

    # Build artifact
    map_artifact = create_geojson_artifact(
        features=paths_all.geometry,
        layer_name='Path Greenness',
        caption=Path('resources/info/naturalness/caption.md').read_text(),
        description=Path('resources/info/naturalness/description.md').read_text(),
        label=paths_all.naturalness.to_list(),
        color=color,
        legend_data=legend,
        resources=resources,
        filename='cycling_infrastructure_path_greenness',
        tags={Topics.GREENNESS},
    )

    return [map_artifact]


def build_naturalness_summary_bar_artifact(aoi_aggregate: Figure, resources: ComputationResources) -> list[_Artifact]:
    chart_artifact = create_plotly_chart_artifact(
        figure=aoi_aggregate,
        title='Distribution of Greenness',
        caption='What length of paths has low, mid, and high NDVI?',
        resources=resources,
        filename='aggregation_aoi_naturalness_bar',
        tags={Topics.SUMMARY, Topics.GREENNESS},
    )

    return [chart_artifact]
