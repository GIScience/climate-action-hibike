import importlib
import logging
from pathlib import Path
from typing import List, Tuple

import geopandas as gpd
import pandas as pd
import shapely
from climatoology.base.baseoperator import BaseOperator, _Artifact, AoiProperties, ComputationResources
from climatoology.base.info import Concern, _Info, PluginAuthor, generate_plugin_info
from climatoology.utility.exception import ClimatoologyUserError
from ohsome import OhsomeClient
from semver import Version

from bikeability.artifact import (
    build_dooring_artifact,
    build_path_categories_artifact,
    build_smoothness_artifact,
    build_surface_types_artifact,
)
from bikeability.indicators.dooring_risk import get_dooring_risk
from bikeability.indicators.path_categories import (
    categorize_paths,
    recategorise_zebra_crossings,
)
from bikeability.indicators.smoothness import get_smoothness
from bikeability.indicators.surface_types import get_surface_types
from bikeability.input import ComputeInputBikeability
from bikeability.utils import (
    fetch_osm_data,
    get_buffered_aoi,
    ohsome_filter,
    zebra_crossings_filter,
    parallel_parking_filter,
)

log = logging.getLogger(__name__)


class OperatorBikeability(BaseOperator[ComputeInputBikeability]):
    def __init__(self):
        super().__init__()
        self.ohsome = OhsomeClient(user_agent='CA Plugin Bikeability')
        log.debug('Initialised bikeability operator with ohsome client')

    def info(self) -> _Info:
        info = generate_plugin_info(
            name='hiBike',
            icon=Path('resources/info/icon.jpeg'),
            authors=[
                PluginAuthor(
                    name='Jonas Kemmer',
                    affiliation='HeiGIT gGmbH',
                    website='https://heigit.org/heigit-team/',
                ),
                PluginAuthor(
                    name='Moritz Schott',
                    affiliation='HeiGIT gGmbH',
                    website='https://heigit.org/heigit-team/',
                ),
            ],
            version=Version.parse(importlib.metadata.version('Bikeability')),
            concerns={Concern.MOBILITY_CYCLING},
            purpose=Path('resources/info/purpose.md'),
            methodology=Path('resources/info/methodology.md'),
            sources=Path('resources/literature.bib'),
            demo_input_parameters=ComputeInputBikeability(),
        )
        log.info(f'Return info {info.model_dump()}')
        return info

    def compute(
        self,
        resources: ComputationResources,
        aoi: shapely.MultiPolygon,
        aoi_properties: AoiProperties,
        params: ComputeInputBikeability,
    ) -> List[_Artifact]:
        log.info(f'Handling compute request: {params.model_dump()} in context: {resources}')

        line_paths, polygon_paths = self.get_paths(get_buffered_aoi(aoi))

        number_of_paths = len(line_paths)
        if number_of_paths > 500000:
            raise ClimatoologyUserError(
                f'There are too many path segments in the selected area: {number_of_paths} path segments. Currently, only areas with a maximum of 500,000 path segments are allowed. Please select a smaller area or a sub-region of your selected area.'
            )

        line_paths, polygon_paths = categorize_paths(line_paths, polygon_paths)

        zebra_crossing_nodes = self.get_zebra_crossing_nodes(get_buffered_aoi(aoi))
        line_paths = recategorise_zebra_crossings(line_paths, zebra_crossing_nodes)

        path_categories_artifact = build_path_categories_artifact(line_paths, polygon_paths, aoi, resources)

        path_smoothness = get_smoothness(line_paths)
        smoothness_artifact = build_smoothness_artifact(path_smoothness, aoi, resources)

        line_paths = get_surface_types(line_paths)
        surface_types_artifact = build_surface_types_artifact(line_paths, aoi, resources)

        parallel_car_parking = self.get_parallel_parking(get_buffered_aoi(aoi))
        path_dooring_risk = get_dooring_risk(line_paths, parallel_car_parking)
        dooring_risk_artifact = build_dooring_artifact(path_dooring_risk, aoi, resources)
        return [path_categories_artifact, smoothness_artifact, surface_types_artifact, dooring_risk_artifact]

    def get_paths(self, aoi: shapely.MultiPolygon) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
        log.debug('Extracting paths')

        paths_line = fetch_osm_data(aoi, ohsome_filter('line'), self.ohsome)
        paths_polygon = fetch_osm_data(aoi, ohsome_filter('polygon'), self.ohsome)

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
