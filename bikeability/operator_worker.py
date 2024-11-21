import logging
from pathlib import Path
from typing import List, Tuple

import pandas as pd
import geopandas as gpd
import shapely
from climatoology.base.operator import ComputationResources, Concern, Info, Operator, PluginAuthor, _Artifact
from ohsome import OhsomeClient
from semver import Version

from bikeability.artifact import (
    build_dooring_artifact,
    build_path_categories_artifact,
    build_smoothness_artifact,
    build_surface_types_artifact,
)
from bikeability.indicators.path_categories import categorize_paths
from bikeability.indicators.surface_types import get_surface_types
from bikeability.indicators.smoothness import get_smoothness
from bikeability.indicators.dooring_risk import get_dooring_risk, parking_filter

from bikeability.input import ComputeInputBikeability
from bikeability.utils import (
    fetch_osm_data,
    ohsome_filter,
)

log = logging.getLogger(__name__)


class OperatorBikeability(Operator[ComputeInputBikeability]):
    def __init__(self):
        self.ohsome = OhsomeClient(user_agent='CA Plugin Bikeability')
        log.debug('Initialised bikeability operator with ohsome client')

    def info(self) -> Info:
        info = Info(
            name='Bikeability',
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
            version=str(Version(0, 0, 1)),
            concerns=[Concern.MOBILITY_CYCLING],
            purpose=Path('resources/info/purpose.md').read_text(),
            methodology=Path('resources/info/methodology.md').read_text(),
            sources=Path('resources/literature.bib'),
        )
        log.info(f'Return info {info.model_dump()}')

        return info

    def compute(self, resources: ComputationResources, params: ComputeInputBikeability) -> List[_Artifact]:
        log.info(f'Handling compute request: {params.model_dump()} in context: {resources}')

        line_paths, polygon_paths = self.get_paths(params.get_buffered_aoi())
        line_paths, polygon_paths = categorize_paths(line_paths, polygon_paths, params.get_path_rating_mapping())
        path_categories_artifact = build_path_categories_artifact(
            line_paths, polygon_paths, params.path_rating, params.get_aoi_geom(), resources
        )

        path_smoothness = get_smoothness(line_paths, params.get_path_smoothness_mapping())
        smoothness_artifact = build_smoothness_artifact(
            path_smoothness, params.smoothness_rating, params.get_aoi_geom(), resources
        )

        line_paths = get_surface_types(line_paths)
        surface_types_artifact = build_surface_types_artifact(line_paths, params.get_aoi_geom(), resources)

        parallel_car_parking = self.get_parallel_parking(params.get_buffered_aoi())
        path_dooring_risk = get_dooring_risk(line_paths, parallel_car_parking, params.get_path_dooring_mapping())
        dooring_risk_artifact = build_dooring_artifact(
            path_dooring_risk, params.dooring_risk_rating, params.get_aoi_geom(), resources
        )
        return [path_categories_artifact, smoothness_artifact, surface_types_artifact, dooring_risk_artifact]

    def get_paths(self, aoi: shapely.MultiPolygon) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
        log.debug('Extracting paths')

        paths_line = fetch_osm_data(aoi, ohsome_filter('line'), self.ohsome)
        paths_polygon = fetch_osm_data(aoi, ohsome_filter('polygon'), self.ohsome)

        return paths_line, paths_polygon

    def get_parallel_parking(self, aoi: shapely.MultiPolygon) -> gpd.GeoDataFrame:
        log.debug('Extracting parallel car parking')
        parking_paths = fetch_osm_data(aoi, parking_filter('line'), self.ohsome)
        parking_polygons = fetch_osm_data(aoi, parking_filter('polygon'), self.ohsome)

        return pd.concat([parking_paths, parking_polygons])
