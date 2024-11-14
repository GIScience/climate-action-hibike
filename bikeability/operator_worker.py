import logging
from pathlib import Path
from typing import List, Tuple

import geopandas as gpd
import shapely
from climatoology.base.operator import ComputationResources, Concern, Info, Operator, PluginAuthor, _Artifact
from ohsome import OhsomeClient
from semver import Version

from bikeability.artifact import (
    build_path_categories_artifact,
    build_smoothness_artifact,
    build_surface_types_artifact,
)
from bikeability.indicators import categorize_paths, get_surface_types, get_smoothness
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

        return [path_categories_artifact, smoothness_artifact, surface_types_artifact]

    def get_paths(self, aoi: shapely.MultiPolygon) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
        log.debug('Extracting paths')

        paths_line = fetch_osm_data(aoi, ohsome_filter('line'), self.ohsome)
        paths_polygon = fetch_osm_data(aoi, ohsome_filter('polygon'), self.ohsome)

        return paths_line, paths_polygon
