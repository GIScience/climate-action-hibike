import logging
from datetime import timedelta
from pathlib import Path

import geopandas as gpd
import pandas as pd
import shapely
from climatoology.base.baseoperator import AoiProperties, Artifact, BaseOperator, ComputationResources
from climatoology.base.plugin_info import Concern, CustomAOI, PluginAuthor, PluginInfo, generate_plugin_info
from climatoology.utility.naturalness import NaturalnessIndex, NaturalnessUtility
from mobility_tools.ors_settings import ORSSettings
from ohsome import OhsomeClient
from pydantic.networks import HttpUrl
from shapely import make_valid

from bikeability.components.detour_factors.detour_analysis import (
    detour_factor_analysis,
)
from bikeability.components.dooring_risk.dooring_artifacts import build_dooring_artifact
from bikeability.components.dooring_risk.dooring_risk import get_dooring_risk, parallel_parking_filter
from bikeability.components.naturalness import (
    build_naturalness_artifact,
    build_naturalness_summary_bar_artifact,
    get_naturalness,
    summarise_naturalness,
)
from bikeability.components.path_categories.path_categories import (
    categorize_paths,
    recategorise_zebra_crossings,
    zebra_crossings_filter,
)
from bikeability.components.path_categories.path_category_artifacts import build_path_categories_artifact
from bikeability.components.path_categories.path_summaries import (
    build_aoi_summary_category_stacked_bar_artifact,
    summarise_aoi,
)
from bikeability.components.smoothness.smoothness import get_smoothness
from bikeability.components.smoothness.smoothness_artifacts import build_smoothness_artifact
from bikeability.components.surface_types.surface_types import get_surface_types
from bikeability.components.surface_types.surface_types_artifacts import build_surface_types_artifact
from bikeability.components.utils.utils import (
    check_paths_count_limit,
    fetch_osm_data,
    get_buffered_aoi,
    get_utm_zone,
    ohsome_filter,
)
from bikeability.core.input import BikeabilityIndicators, ComputeInputBikeability

log = logging.getLogger(__name__)


class OperatorBikeability(BaseOperator[ComputeInputBikeability]):
    def __init__(self, naturalness_utility: NaturalnessUtility, ors_settings: ORSSettings):
        super().__init__()
        self.ohsome = OhsomeClient(user_agent='CA Plugin Bikeability')
        self.ors_settings = ors_settings
        log.debug('Initialised bikeability operator with ohsome client')

        self.naturalness_utility = naturalness_utility
        log.debug('Initialised bikeability operator with naturalness client')

    def info(self) -> PluginInfo:
        info = generate_plugin_info(
            name='hiBike',
            icon=Path('resources/info/bike-lane.jpeg'),
            authors=[
                PluginAuthor(
                    name='Climate Action Team',
                    affiliation='HeiGIT gGmbH',
                    website=HttpUrl('https://heigit.org/heigit-team/'),
                ),
            ],
            concerns={Concern.MOBILITY_CYCLING},
            purpose=Path('resources/info/purpose.md'),
            teaser='Assess the safety, comfort, and attractiveness of cycling infrastructure in an area of interest.',
            methodology=Path('resources/info/methodology.md'),
            sources_library=Path('resources/literature.bib'),
            computation_shelf_life=timedelta(weeks=24),
            # TODO replace this  aoi
            demo_input_parameters=ComputeInputBikeability(),
            demo_aoi=CustomAOI(
                name='Demo',
                path=Path('resources/Heidelberg_AOI.geojson'),
            ),
        )
        log.info(f'Return info {info.model_dump()}')
        return info

    def compute(  # dead: disable # type: ignore
        self,
        resources: ComputationResources,
        aoi: shapely.MultiPolygon,
        aoi_properties: AoiProperties,
        params: ComputeInputBikeability,
    ) -> list[Artifact]:
        log.info(f'Handling compute request: {params.model_dump()} in context: {resources}')

        buffered_aoi = get_buffered_aoi(aoi)

        log.debug('Get the number of the paths (lines & polygons) which will return.')
        check_paths_count_limit(aoi, self.ohsome, 500000)

        paths = self.get_paths(aoi)

        paths = categorize_paths(paths)

        zebra_crossing_nodes = self.get_zebra_crossing_nodes(aoi)
        paths = recategorise_zebra_crossings(paths, zebra_crossing_nodes)

        path_categories_artifact = build_path_categories_artifact(paths, resources)

        smoothness_paths = get_smoothness(paths)
        smoothness_artifact = build_smoothness_artifact(smoothness_paths, resources)

        surface_type_paths = get_surface_types(paths)
        surface_types_artifact = build_surface_types_artifact(surface_type_paths, resources)

        parallel_car_parking = self.get_parallel_parking(buffered_aoi)
        dooring_risk_paths = get_dooring_risk(paths, parallel_car_parking)
        dooring_risk_artifact = build_dooring_artifact(dooring_risk_paths, resources)

        aoi_summary_category_stacked_bar = summarise_aoi(paths, get_utm_zone(aoi))
        aoi_summary_category_stacked_bar_artifact = build_aoi_summary_category_stacked_bar_artifact(
            aoi_summary_category_stacked_bar, resources
        )

        artifacts = [
            path_categories_artifact,
            smoothness_artifact,
            surface_types_artifact,
            dooring_risk_artifact,
            aoi_summary_category_stacked_bar_artifact,
        ]

        # naturalness
        if BikeabilityIndicators.NATURALNESS in params.optional_indicators:
            with self.catch_exceptions(indicator_name='Greenness', resources=resources):
                naturalness_paths = get_naturalness(paths, self.naturalness_utility, NaturalnessIndex.NDVI)
                naturalness_artifacts = build_naturalness_artifact(naturalness_paths, resources)
                artifacts.append(naturalness_artifacts)
                naturalness_summary_bar = summarise_naturalness(
                    paths=naturalness_paths, projected_crs=get_utm_zone(aoi)
                )
                naturalness_summary_bar_artifact = build_naturalness_summary_bar_artifact(
                    aoi_aggregate=naturalness_summary_bar, resources=resources
                )
                artifacts.append(naturalness_summary_bar_artifact)

        if BikeabilityIndicators.DETOUR_FACTORS in params.optional_indicators:
            with self.catch_exceptions(indicator_name=BikeabilityIndicators.DETOUR_FACTORS.value, resources=resources):
                detour_artifacts = detour_factor_analysis(
                    aoi, paths, ors_settings=self.ors_settings, resources=resources
                )
                artifacts.extend(detour_artifacts)

        return artifacts

    def get_paths(self, aoi: shapely.MultiPolygon) -> gpd.GeoDataFrame:
        log.debug('Extracting paths')

        line_paths = fetch_osm_data(aoi, ohsome_filter('line'), self.ohsome)
        polygon_paths = fetch_osm_data(aoi, ohsome_filter('polygon'), self.ohsome)

        invalid_line = ~line_paths.is_valid
        line_paths.loc[invalid_line, 'geometry'] = line_paths.loc[invalid_line, 'geometry'].apply(make_valid)
        invalid_polygon = ~polygon_paths.is_valid
        polygon_paths.loc[invalid_polygon, 'geometry'] = polygon_paths.loc[invalid_polygon, 'geometry'].apply(
            make_valid
        )

        paths = pd.concat(
            [
                line_paths[~line_paths.geom_type.isin(['Point', 'MultiPoint'])],
                polygon_paths[~polygon_paths.geom_type.isin(['Point', 'MultiPoint'])],
            ],
            ignore_index=True,
        )

        return paths  # type: ignore

    def get_parallel_parking(self, aoi: shapely.MultiPolygon) -> gpd.GeoDataFrame:
        log.debug('Extracting parallel car parking')
        parking_paths = fetch_osm_data(aoi, parallel_parking_filter('line'), self.ohsome)
        parking_polygons = fetch_osm_data(aoi, parallel_parking_filter('polygon'), self.ohsome)

        return pd.concat([parking_paths, parking_polygons])  # type: ignore

    def get_zebra_crossing_nodes(self, aoi: shapely.MultiPolygon) -> gpd.GeoDataFrame:
        log.debug('Getting crossing nodes')
        nodes = fetch_osm_data(aoi, zebra_crossings_filter(), self.ohsome)

        return nodes
