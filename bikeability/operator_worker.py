import importlib
import logging
from datetime import timedelta
from pathlib import Path
from typing import List, Tuple

import geopandas as gpd
import pandas as pd
import shapely
from climatoology.base.baseoperator import AoiProperties, BaseOperator, ComputationResources, _Artifact
from climatoology.base.info import Concern, PluginAuthor, _Info, generate_plugin_info
from climatoology.utility.Naturalness import NaturalnessIndex, NaturalnessUtility
from ohsome import OhsomeClient
from semver import Version
from shapely import make_valid

from bikeability.artifact import (
    build_dooring_artifact,
    build_naturalness_artifact,
    build_path_categories_artifact,
    build_smoothness_artifact,
    build_surface_types_artifact,
)
from bikeability.indicators.dooring_risk import get_dooring_risk
from bikeability.indicators.naturalness import get_naturalness
from bikeability.indicators.path_categories import (
    categorize_paths,
    recategorise_zebra_crossings,
)
from bikeability.indicators.smoothness import get_smoothness
from bikeability.indicators.surface_types import get_surface_types
from bikeability.input import BikeabilityIndicators, ComputeInputBikeability
from bikeability.utils import (
    check_paths_count_limit,
    fetch_osm_data,
    get_buffered_aoi,
    ohsome_filter,
    parallel_parking_filter,
    zebra_crossings_filter,
)

log = logging.getLogger(__name__)


class OperatorBikeability(BaseOperator[ComputeInputBikeability]):
    def __init__(self, naturalness_utility: NaturalnessUtility):
        super().__init__()
        self.ohsome = OhsomeClient(user_agent='CA Plugin Bikeability')
        log.debug('Initialised bikeability operator with ohsome client')

        self.naturalness_utility = naturalness_utility
        log.debug('Initialised bikeability operator with naturalness client')

    def info(self) -> _Info:
        info = generate_plugin_info(
            name='hiBike',
            icon=Path('resources/info/bike-lane.jpeg'),
            authors=[
                PluginAuthor(
                    name='Climate Action Team',
                    affiliation='HeiGIT gGmbH',
                    website='https://heigit.org/heigit-team/',
                ),
            ],
            version=Version.parse(importlib.metadata.version('Bikeability')),
            concerns={Concern.MOBILITY_CYCLING},
            purpose=Path('resources/info/purpose.md'),
            teaser='Assess the safety, comfort, and attractiveness of cycling infrastructure in an area of interest.',
            methodology=Path('resources/info/methodology.md'),
            sources=Path('resources/literature.bib'),
            demo_input_parameters=ComputeInputBikeability(),
            computation_shelf_life=timedelta(weeks=24),
        )
        log.info(f'Return info {info.model_dump()}')
        return info

    def compute(  # dead: disable
        self,
        resources: ComputationResources,
        aoi: shapely.MultiPolygon,
        aoi_properties: AoiProperties,
        params: ComputeInputBikeability,
    ) -> List[_Artifact]:
        log.info(f'Handling compute request: {params.model_dump()} in context: {resources}')

        buffered_aoi = get_buffered_aoi(aoi)

        log.debug('Get the number of the paths (lines & polygons) which will return.')
        check_paths_count_limit(buffered_aoi, self.ohsome, 500000)

        line_paths, polygon_paths = self.get_paths(buffered_aoi)

        line_paths, polygon_paths = categorize_paths(line_paths, polygon_paths)

        zebra_crossing_nodes = self.get_zebra_crossing_nodes(buffered_aoi)
        line_paths = recategorise_zebra_crossings(line_paths, zebra_crossing_nodes)

        path_categories_artifact = build_path_categories_artifact(line_paths, polygon_paths, aoi, resources)

        path_smoothness = get_smoothness(line_paths)
        smoothness_artifact = build_smoothness_artifact(path_smoothness, aoi, resources)

        line_paths = get_surface_types(line_paths)
        surface_types_artifact = build_surface_types_artifact(line_paths, aoi, resources)

        parallel_car_parking = self.get_parallel_parking(buffered_aoi)
        path_dooring_risk = get_dooring_risk(line_paths, parallel_car_parking)
        dooring_risk_artifact = build_dooring_artifact(path_dooring_risk, aoi, resources)

        return_artifacts = [
            path_categories_artifact,
            smoothness_artifact,
            surface_types_artifact,
            dooring_risk_artifact,
        ]

        # naturalness
        if BikeabilityIndicators.NATURALNESS in params.optional_indicators:
            with self.catch_exceptions(indicator_name='Greenness', resources=resources):
                paths_nature = get_naturalness(
                    line_paths, polygon_paths, self.naturalness_utility, NaturalnessIndex.NDVI
                )
                naturalness_artifact = build_naturalness_artifact(paths_nature, aoi, resources)
                return_artifacts.extend(naturalness_artifact)

        return return_artifacts

    def get_paths(self, aoi: shapely.MultiPolygon) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
        log.debug('Extracting paths')

        paths_line = fetch_osm_data(aoi, ohsome_filter('line'), self.ohsome)
        paths_polygon = fetch_osm_data(aoi, ohsome_filter('polygon'), self.ohsome)

        invalid_line = ~paths_line.is_valid
        paths_line.loc[invalid_line, 'geometry'] = paths_line.loc[invalid_line, 'geometry'].apply(make_valid)
        invalid_polygon = ~paths_polygon.is_valid
        paths_polygon.loc[invalid_polygon, 'geometry'] = paths_polygon.loc[invalid_polygon, 'geometry'].apply(
            make_valid
        )

        return paths_line, paths_polygon

    def get_parallel_parking(self, aoi: shapely.MultiPolygon) -> gpd.GeoDataFrame:
        log.debug('Extracting parallel car parking')
        parking_paths = fetch_osm_data(aoi, parallel_parking_filter('line'), self.ohsome)
        parking_polygons = fetch_osm_data(aoi, parallel_parking_filter('polygon'), self.ohsome)

        return pd.concat([parking_paths, parking_polygons])

    def get_zebra_crossing_nodes(self, aoi: shapely.MultiPolygon) -> gpd.GeoDataFrame:
        log.debug('Getting crossing nodes')
        nodes = fetch_osm_data(aoi, zebra_crossings_filter(), self.ohsome)

        return nodes
