import geopandas as gpd
import matplotlib.colors as mcolors
import pandas as pd
from plotly import graph_objects as go
from pyproj import CRS

from bikeability.components.dooring_risk.dooring_risk import DooringRiskCategory, log
from bikeability.components.utils.colors import get_qualitative_color
from bikeability.components.utils.utils import calculate_length


def summarise_dooring_risk(paths: gpd.GeoDataFrame, projected_crs: CRS, length_resolution_m: int = 1000) -> go.Figure:
    """
    Creates a stacked bar chart summarizing dooring risk by length.
    """
    log.info('Summarising Dooring Risk Categories')

    line_paths = paths[
        paths.geom_type.isin(['LineString', 'MultiLineString'])
    ]  # summarizing only makes sense by length, if we include polygons we need a different metric
    stats = calculate_length(length_resolution_m, line_paths, projected_crs)

    summary = stats.groupby('dooring_category', sort=False, as_index=False)[
        'length'
    ].sum()  # Do not sort because dooring_category cannot be sorted
    category_order = DooringRiskCategory.get_visible()
    summary['dooring_category'] = pd.Categorical(summary['dooring_category'], categories=category_order, ordered=True)
    summary_sorted = summary.sort_values('dooring_category')

    total_length = summary_sorted['length'].sum()
    summary_sorted['percent'] = summary_sorted['length'] / total_length * 100

    dooring_color_map = mcolors.LinearSegmentedColormap.from_list('dooring_color_map', ['#617CCC', '#FF675C', 'grey'])
    dooring_color_map.set_under('#808080')
    stacked_bar_colors = summary_sorted.dooring_category.apply(get_qualitative_color, cmap=dooring_color_map)
    stacked_bar_colors = [c.as_hex() for c in stacked_bar_colors]
    summary_sorted['dooring_category'] = summary_sorted['dooring_category'].apply(lambda x: x.value)

    dooring_risk_fig_stacked_bar = go.Figure()

    for i, row in summary_sorted.reset_index(drop=True).iterrows():
        dooring_risk_fig_stacked_bar.add_trace(
            go.Bar(
                x=[row['percent']],
                name=row['dooring_category'].replace('_', ' ').capitalize(),
                orientation='h',
                marker_color=stacked_bar_colors[i],
                hovertemplate=f'{row["dooring_category"]}: {row["length"]:.2f} km ({row["percent"]:.1f}%)<extra></extra>'.replace(
                    '_', ' '
                ).capitalize(),
                legendrank=len(summary_sorted) - i,
                showlegend=True,
            )
        )

    dooring_risk_fig_stacked_bar.update_layout(
        barmode='stack',
        height=300,
        margin=dict(t=30, b=80, l=30, r=30),
        xaxis_title=f'Percentage of the {round(sum(summary["length"]), 2)} km of paths in each category',
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

    return dooring_risk_fig_stacked_bar
