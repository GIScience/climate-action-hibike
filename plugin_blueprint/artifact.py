from typing import Tuple, Dict

import geopandas as gpd
import pandas as pd
from PIL.Image import Image
from climatoology.base.artifact import (
    create_markdown_artifact,
    create_table_artifact,
    create_image_artifact,
    create_chart_artifact,
    Chart2dData,
    _Artifact,
    create_geojson_artifact,
    create_geotiff_artifact,
    RasterInfo,
    ContinuousLegendData,
)
from climatoology.base.computation import ComputationResources
from climatoology.utility.api import LabelDescriptor
from pydantic_extra_types.color import Color


def build_markdown_artifact(text: str, resources: ComputationResources) -> _Artifact:
    return create_markdown_artifact(
        text=text,
        name='A Text',
        tl_dr='A JSON-block of the input parameters',
        resources=resources,
        filename='markdown_blueprint',
    )


def build_table_artifact(table: pd.DataFrame, resources: ComputationResources) -> _Artifact:
    return create_table_artifact(
        data=table,
        title='Character Count',
        caption='The table lists the number of occurrences for each character in the input parameters.',
        description='A table with two columns.',
        resources=resources,
        filename='table_blueprint',
    )


def build_image_artifact(image: Image, resources: ComputationResources) -> _Artifact:
    return create_image_artifact(
        image=image,
        title='Image',
        caption='A nice image.',
        description='The image is under CC0 license taken from [pexels]'
        '(https://www.pexels.com/photo/person-holding-a-green-'
        'plant-1072824/).',
        resources=resources,
        filename='image_blueprint',
    )


def build_chart_artifacts(
    bar_chart_data: Chart2dData,
    line_chart_data: Chart2dData,
    pie_chart_data: Chart2dData,
    scatter_chart_data: Chart2dData,
    resources: ComputationResources,
) -> Tuple[_Artifact, _Artifact, _Artifact, _Artifact]:
    scatter_chart = create_chart_artifact(
        data=scatter_chart_data,
        title='The Points',
        caption='A simple scatter plot.',
        description='Beautiful points.',
        resources=resources,
        filename='scatter_chart_blueprint',
    )
    line_chart = create_chart_artifact(
        data=line_chart_data,
        title='The Line',
        caption='A simple line of negative incline.',
        resources=resources,
        filename='line_chart_blueprint',
        primary=False,
    )
    bar_chart = create_chart_artifact(
        data=bar_chart_data,
        title='The Bars',
        caption='A simple bar chart.',
        resources=resources,
        filename='bar_chart_blueprint',
        primary=False,
    )
    pie_chart = create_chart_artifact(
        data=pie_chart_data,
        title='The Pie',
        caption='A simple pie.',
        resources=resources,
        filename='pie_chart_blueprint',
        primary=False,
    )
    return scatter_chart, line_chart, bar_chart, pie_chart


def build_vector_artifacts(
    lines: gpd.GeoDataFrame,
    points: gpd.GeoDataFrame,
    polygons: gpd.GeoDataFrame,
    resources: ComputationResources,
) -> Tuple[_Artifact, _Artifact, _Artifact]:
    point_artifact = create_geojson_artifact(
        features=points.geometry,
        layer_name='Points',
        caption='Schools in the area of interest including a dummy school in the center.',
        description='The schools are taken from OSM at the date given in the input form.',
        color=points.color.to_list(),
        label=points.label.to_list(),
        resources=resources,
        filename='points_blueprint',
    )
    line_artifact = create_geojson_artifact(
        features=lines.geometry,
        layer_name='Lines',
        caption='Buffers around schools in the area of interest including a dummy school in the center.',
        description='The schools are taken from OSM at the date given in the input form.',
        color=lines.color.to_list(),
        label=lines.label.to_list(),
        resources=resources,
        filename='lines_blueprint',
        primary=False,
    )
    polygon_artifact = create_geojson_artifact(
        features=polygons.geometry,
        layer_name='Polygons',
        caption='Schools in the area of interest including a dummy school in the center, buffered by ca. 100m.',
        description='The schools are taken from OSM at the date given in the input form.',
        color=polygons.color.to_list(),
        label=polygons.label.to_list(),
        resources=resources,
        filename='polygons_blueprint',
        primary=False,
        legend_data=ContinuousLegendData(cmap_name='seismic', ticks={'Good School': 0, 'Bad School': 1}),
    )
    return point_artifact, line_artifact, polygon_artifact


def build_raster_artifact(
    raster_info: RasterInfo,
    labels: Dict[str, LabelDescriptor],
    resources: ComputationResources,
) -> _Artifact:
    return create_geotiff_artifact(
        raster_info=raster_info,
        layer_name='LULC Classification',
        caption='A land-use and land-cover classification of a user defined area.',
        description='The classification is created using a deep learning model.',
        legend_data={v.name: Color(v.color) for _, v in labels.items()},
        resources=resources,
        filename='raster_blueprint',
    )
