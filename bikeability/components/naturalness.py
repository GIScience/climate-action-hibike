import datetime as dt
import logging
from pathlib import Path

import geopandas as gpd
import pandas as pd
import plotly.graph_objects as go
import shapely
from climatoology.base.artifact import Artifact, ArtifactMetadata, ContinuousLegendData, Legend
from climatoology.base.artifact_creators import (
    create_plotly_chart_artifact,
    create_vector_artifact,
)
from climatoology.base.computation import ComputationResources
from climatoology.base.exception import ClimatoologyUserError
from climatoology.utility.api import TimeRange
from climatoology.utility.naturalness import NaturalnessIndex, NaturalnessUtility
from plotly.graph_objs import Figure
from pyproj import CRS

from bikeability.components.utils.colors import get_continuous_colors
from bikeability.components.utils.utils import Topics, calculate_length

log = logging.getLogger(__name__)


def _add_buffer_offset(path_line: shapely.LineString, is_0x: bool) -> shapely.LineString:
    buffer_offset = 0.000009  # ~1 m

    coords = list(path_line.coords)
    last_coords = coords[-1]
    if is_0x:
        new_coords = coords[:-1] + [(last_coords[0] + buffer_offset, last_coords[1])]
    else:
        new_coords = coords[:-1] + [(last_coords[0], last_coords[1] + buffer_offset)]

    return shapely.LineString(new_coords)


def _preprocess_path_lines(path_lines: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    log.debug("Pre-process lingstring (path_line) to avoid the case 'width/height = 0'")
    path_lines_bounds = path_lines.geometry.bounds
    path_lines_width = path_lines_bounds['maxx'] - path_lines_bounds['minx']
    path_lines_height = path_lines_bounds['maxy'] - path_lines_bounds['miny']

    # fix width = 0
    path_lines.loc[(path_lines_width == 0), 'geometry'] = path_lines.loc[(path_lines_width == 0), 'geometry'].apply(
        lambda row: _add_buffer_offset(row, True)
    )

    # fix height = 0 (when width != 0)
    path_lines.loc[(path_lines_width != 0) & (path_lines_height == 0), 'geometry'] = path_lines.loc[
        (path_lines_width != 0) & (path_lines_height == 0), 'geometry'
    ].apply(lambda row: _add_buffer_offset(row, False))

    return path_lines


def fetch_naturalness_by_vector(
    nature_utility: NaturalnessUtility,
    time_range: TimeRange,
    vectors: list[gpd.GeoSeries],
    index: NaturalnessIndex,
    agg_stats: list[str],
    resolution: int = 30,
) -> gpd.GeoDataFrame:
    naturalness_gdf = nature_utility.compute_vector(
        index=index,
        aggregation_stats=agg_stats,
        vectors=vectors,
        time_range=time_range,
        resolution=resolution,
    )

    naturalness_gdf = naturalness_gdf.rename(columns={'median': 'naturalness'})
    return naturalness_gdf


def get_naturalness(
    paths: gpd.GeoDataFrame,
    nature_utility: NaturalnessUtility,
    nature_index: NaturalnessIndex,
    agg_stats: list[str] = ['median'],
) -> gpd.GeoDataFrame:
    """
    Get naturalness/NDVI along street within the AOI.
    """
    log.info('Naturalness calculation starts...')

    path_lines = paths[paths.geom_type.isin(['LineString', 'MultiLinesString'])]
    path_polygons = paths[paths.geom_type.isin(['Polygon', 'MultiPolygon'])]

    lines_valid = _preprocess_path_lines(path_lines.copy())

    naturalness_paths = []
    if not lines_valid.empty:
        log.debug('compute naturalness by sentinelhub... (path_lines)')
        lines_ndvi = fetch_naturalness_by_vector(
            nature_utility=nature_utility,
            time_range=TimeRange(end_date=dt.datetime.now().replace(day=1).date()),
            vectors=[lines_valid.geometry],
            index=nature_index,
            agg_stats=agg_stats,
        )

        log.debug('Post-process: reset path_line geometry which is not pre-processed')
        lines_ndvi.geometry = path_lines.geometry
        naturalness_paths.append(lines_ndvi)

    if not path_polygons.empty:
        log.debug('compute naturalness by sentinelhub... (path_polygons)')
        polygons_ndvi = fetch_naturalness_by_vector(
            nature_utility=nature_utility,
            time_range=TimeRange(end_date=dt.datetime.now().replace(day=1).date()),
            vectors=[path_polygons.geometry],
            index=nature_index,
            agg_stats=agg_stats,
        )
        naturalness_paths.append(polygons_ndvi)

    # merge path_lines and path_polygons result here and return one dataframe
    paths_all_ndvi = pd.concat(naturalness_paths, ignore_index=True)

    log.info('Naturalness calculation completed.')

    return paths_all_ndvi


def build_naturalness_artifact(
    paths_all: gpd.GeoDataFrame,
    resources: ComputationResources,
    cmap_name: str = 'YlGn',
) -> Artifact:
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

    legend = Legend(
        legend_data=ContinuousLegendData(
            cmap_name=cmap_name,
            ticks={'Low (0)': 0.0, 'High (1)': 1.0},
        )
    )

    paths_all['color'] = get_continuous_colors(paths_all['naturalness'], cmap_name)

    metadata = ArtifactMetadata(
        name='Path Greenness',
        summary=Path('resources/info/naturalness/summary.md').read_text(),
        description=Path('resources/info/naturalness/description.md').read_text(),
        filename='cycling_infrastructure_path_greenness',
        tags={Topics.GREENNESS},
    )

    return create_vector_artifact(
        data=paths_all, metadata=metadata, resources=resources, label='naturalness', legend=legend
    )


def build_naturalness_summary_bar_artifact(aoi_aggregate: Figure, resources: ComputationResources) -> Artifact:
    metadata = ArtifactMetadata(
        name='Distribution of Greenness',
        summary='What length of paths has low, mid, and high NDVI? A high NDVI signifies abundant healthy vegetation, and a low NDVI signifies a lack of vegetation.',
        filename='aggregation_aoi_naturalness_bar',
        tags={Topics.SUMMARY, Topics.GREENNESS},
    )

    return create_plotly_chart_artifact(
        figure=aoi_aggregate,
        metadata=metadata,
        resources=resources,
    )


def summarise_naturalness(
    paths: gpd.GeoDataFrame,
    projected_crs: CRS,
    length_resolution_m: int = 1000,
) -> go.Figure:
    log.info('Summarising naturalness stats')
    stats = calculate_length(length_resolution_m, paths, projected_crs)

    stats['naturalness_rating'] = stats['naturalness'].apply(lambda x: 0 if x < 0.3 else (0.5 if x < 0.6 else 1))

    naturalness_map = {
        0: 'Low (< 0.3) ',
        0.5: 'Medium (0.3 to 0.6)',
        1: 'High (> 0.6)',
        -999: 'Unknown greenness',
    }
    stats['naturalness_category'] = stats['naturalness_rating'].map(naturalness_map)

    stats = stats.sort_values(
        by=['naturalness_rating'],
        ascending=False,
    )
    summary = stats.groupby(['naturalness_rating', 'naturalness_category'], sort=True)['length'].sum().reset_index()

    bar_colors = get_continuous_colors(summary.naturalness_rating, 'YlGn')

    bar_fig = go.Figure(
        data=go.Bar(
            x=summary['naturalness_category'],
            y=summary['length'],
            marker_color=[c.as_hex() for c in bar_colors],
            hovertemplate='%{x}: %{y} km <extra></extra>',
        )
    )
    bar_fig.update_layout(
        title=dict(
            subtitle=dict(text='Length (km)', font=dict(size=14)),
        ),
        xaxis_title='Length of paths with different greenness levels',
        yaxis_title=None,
        margin=dict(t=30, b=60, l=80, r=30),
    )
    return bar_fig
