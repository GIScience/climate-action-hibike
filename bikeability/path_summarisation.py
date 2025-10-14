import logging

import geopandas as gpd
import pandas as pd
import plotly.graph_objects as go
from pyproj import CRS

from bikeability.indicators.path_categories import PathCategory
from bikeability.utils import get_continuous_colors, get_qualitative_color

log = logging.getLogger(__name__)


def summarise_aoi(
    paths: gpd.GeoDataFrame,
    projected_crs: CRS,
    length_resolution_m: int = 1000,
) -> go.Figure:
    log.info('Summarising Walkable Path Categories')

    stats = calculate_length(length_resolution_m, paths, projected_crs)

    # Path category stacked bar chart
    summary = stats.groupby('category', dropna=False, sort=False, as_index=False)['length'].sum()
    category_order = list(PathCategory.get_visible())
    summary['category'] = pd.Categorical(summary['category'], categories=category_order, ordered=True)
    summary_sorted = summary.sort_values('category')

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


def calculate_length(length_resolution_m, paths, projected_crs):
    stats = paths.copy()
    stats = stats.loc[stats.geometry.geom_type.isin(('MultiLineString', 'LineString'))]
    stats = stats.to_crs(projected_crs)
    stats['length'] = stats.length / length_resolution_m
    stats['length'] = round(stats['length'], 2)
    return stats
