from pathlib import Path

import geopandas as gpd
from climatoology.base.artifact import _Artifact, create_geojson_artifact
from climatoology.base.computation import ComputationResources
from pydantic_extra_types.color import Color

from bikeability.components.dooring_risk.dooring_risk import DooringRiskCategory
from bikeability.components.smoothness.smoothness import SmoothnessCategory
from bikeability.components.utils.utils import Topics


def build_dooring_artifact(
    dooring_risk_paths: gpd.GeoDataFrame,
    resources: ComputationResources,
) -> _Artifact:
    legend = {
        DooringRiskCategory.DOORING_SAFE.value: Color('#313695'),
        DooringRiskCategory.DOORING_RISK.value: Color('#f00000'),
        DooringRiskCategory.UNKNOWN.value: Color('grey'),
    }

    def get_dooring_colors(category: DooringRiskCategory, legend: dict[str:SmoothnessCategory]) -> Color:
        return legend[category.value]

    dooring_risk_paths['color'] = dooring_risk_paths.dooring_category.apply(get_dooring_colors, legend=legend)

    return create_geojson_artifact(
        features=dooring_risk_paths.geometry,
        layer_name='Dooring Risk',
        caption=Path('resources/info/dooring_risk/caption.md').read_text(),
        description=Path('resources/info/dooring_risk/description.md').read_text(),
        label=dooring_risk_paths.dooring_category.apply(lambda r: r.name).to_list(),
        color=dooring_risk_paths.color.to_list(),
        legend_data=legend,
        resources=resources,
        filename='cycling_infrastructure_dooring_risk',
        tags={Topics.TRAFFIC, Topics.SAFETY},
    )
