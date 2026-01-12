from pathlib import Path

import geopandas as gpd
from climatoology.base.artifact import Artifact, ArtifactMetadata, Legend
from climatoology.base.artifact_creators import create_vector_artifact
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
            DooringRiskCategory.DOORING_SAFE.value: Color('#313695'),
            DooringRiskCategory.DOORING_RISK.value: Color('#f00000'),
            DooringRiskCategory.UNKNOWN.value: Color('grey'),
        },
    )

    dooring_risk_paths['color'] = dooring_risk_paths.dooring_category.apply(get_colors_from_dict_legend, legend=legend)

    metadata = ArtifactMetadata(
        name='Dooring Risk',
        primary=True,
        tags={Topics.TRAFFIC, Topics.SAFETY},
        filename='cycling_infrastructure_dooring_risk',
        summary=Path('resources/info/dooring_risk/summary.md').read_text(),
        description=Path('resources/info/dooring_risk/description.md').read_text(),
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
