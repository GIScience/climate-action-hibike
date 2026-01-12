import logging

import geopandas as gpd
import pandas as pd
import plotly.graph_objects as go
from climatoology.base.artifact import Artifact, ArtifactMetadata
from climatoology.base.artifact_creators import create_plotly_chart_artifact
from climatoology.base.computation import ComputationResources
from plotly.graph_objs import Figure
from pyproj import CRS

from bikeability.components.path_categories.path_categories import PathCategory
from bikeability.components.utils.colors import get_qualitative_color
from bikeability.components.utils.utils import Topics, calculate_length

log = logging.getLogger(__name__)


def summarise_aoi(
    paths: gpd.GeoDataFrame,
    projected_crs: CRS,
    length_resolution_m: int = 1000,
) -> go.Figure:
    log.info('Summarising Walkable Path Categories')

    line_paths = paths[
        paths.geom_type.isin(['LineString', 'MultiLineString'])
    ]  # summarizing only makes sense by length, if we include polygons we need a different metric
    stats = calculate_length(length_resolution_m, line_paths, projected_crs)

    # Path category stacked bar chart
    summary = stats.groupby('category', dropna=False, sort=False, as_index=False)['length'].sum()
    category_order = PathCategory.get_visible()
    summary['category'] = pd.Categorical(summary['category'], categories=category_order, ordered=True)
    summary_sorted = summary.sort_values('category').dropna()

    total_length = summary_sorted['length'].sum()
    summary_sorted['percent'] = summary_sorted['length'] / total_length * 100

    stacked_bar_colors = summary_sorted.category.apply(get_qualitative_color, cmap_name='coolwarm')
    stacked_bar_colors = [c.as_hex() for c in stacked_bar_colors]
    summary_sorted['category'] = summary_sorted.category.apply(lambda cat: cat.value)

    category_fig_stacked_bar = go.Figure()

    for i, row in summary_sorted.reset_index(drop=True).iterrows():
        category_fig_stacked_bar.add_trace(
            go.Bar(
                y=['Path Types'],
                x=[row['percent']],
                name=row['category'].replace('_', ' ').capitalize(),
                orientation='h',
                marker_color=stacked_bar_colors[i],
                hovertemplate=f'{row["category"]}: {row["length"]:.2f} km ({row["percent"]:.1f}%)<extra></extra>'.replace(
                    '_', ' '
                ).capitalize(),
                showlegend=True,
            )
        )

    category_fig_stacked_bar.update_layout(
        barmode='stack',
        height=300,
        margin=dict(t=30, b=80, l=30, r=30),
        xaxis_title=f'Percentage of the {round(sum(summary_sorted["length"]), 2)} km of paths in each category',
        yaxis=dict(showticklabels=False),
        legend=dict(
            orientation='h',
            yanchor='top',
            y=-1,
            xanchor='center',
            x=0.5,
            font=dict(size=12),
        ),
    )

    return category_fig_stacked_bar


def build_aoi_summary_category_stacked_bar_artifact(aoi_aggregate: Figure, resources: ComputationResources) -> Artifact:
    metadata = ArtifactMetadata(
        name='Distribution of Path Categories',
        summary='How is the total length of paths distributed across the path categories?',
        tags={Topics.TRAFFIC, Topics.SUMMARY},
    )

    return create_plotly_chart_artifact(
        figure=aoi_aggregate,
        metadata=metadata,
        resources=resources,
    )
