from pathlib import Path

import geopandas as gpd
import shapely
from climatoology.base.artifact import _Artifact, create_geojson_artifact
from climatoology.base.computation import ComputationResources
from pydantic_extra_types.color import Color

from bikeability.components.dooring_risk.dooring_risk import DooringRiskCategory
from bikeability.components.smoothness.smoothness import SmoothnessCategory
from bikeability.components.utils.utils import Topics


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
