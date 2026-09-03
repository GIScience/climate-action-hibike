from importlib.resources import read_text

import geopandas as gpd
import plotly.graph_objects as go
from climatoology.base.artifact import Artifact, ArtifactMetadata, Legend
from climatoology.base.artifact_creators import create_plotly_chart_artifact, create_vector_artifact
from climatoology.base.computation import ComputationResources
from pydantic_extra_types.color import Color

from bikeability.components.dooring_risk.dooring_risk import DooringRiskCategory
from bikeability.components.utils.utils import Topics


def build_dooring_artifact(
    dooring_risk_paths: gpd.GeoDataFrame,
    resources: ComputationResources,
) -> Artifact:
    legend = Legend(
        legend_data={
            DooringRiskCategory.DOORING_SAFE.value: Color('#617CCC'),
            DooringRiskCategory.DOORING_RISK.value: Color('#FF675C'),
            DooringRiskCategory.UNKNOWN.value: Color('grey'),
        },
    )

    dooring_risk_paths['color'] = dooring_risk_paths.dooring_category.apply(get_colors_from_dict_legend, legend=legend)

    metadata = ArtifactMetadata(
        name='Dooring Risk',
        primary=True,
        tags={Topics.TRAFFIC, Topics.SAFETY},
        filename='cycling_infrastructure_dooring_risk',
        summary=read_text('bikeability.resources.info.dooring_risk', 'summary.md'),
        description=read_text('bikeability.resources.info.dooring_risk', 'description.md'),
    )

    dooring_risk_paths['label'] = dooring_risk_paths['dooring_category'].apply(lambda x: x.value)

    return create_vector_artifact(
        data=dooring_risk_paths[['@osmId', 'color', 'label', 'geometry']],
        metadata=metadata,
        resources=resources,
        legend=legend,
    )


def get_colors_from_dict_legend(category: DooringRiskCategory, legend: Legend) -> Color:
    assert isinstance(getattr(legend, 'legend_data'), dict), 'Legend data must be a dict'
    return legend.legend_data[category.value]


def build_dooring_risk_stacked_bar_artifact(aoi_aggregate: go.Figure, resources: ComputationResources) -> Artifact:
    metadata = ArtifactMetadata(
        name='Distribution of Dooring Risk',
        summary='How is the total length of paths distributed across the dooring risk categories?',
        tags={Topics.TRAFFIC, Topics.SAFETY},
    )

    return create_plotly_chart_artifact(
        figure=aoi_aggregate,
        metadata=metadata,
        resources=resources,
    )
