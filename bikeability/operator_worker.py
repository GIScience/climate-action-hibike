import logging
from pathlib import Path
from typing import List, Tuple

import geopandas as gpd
import shapely
from climatoology.base.operator import ComputationResources, Concern, Info, Operator, PluginAuthor, _Artifact
from ohsome import OhsomeClient
from semver import Version

from bikeability.artifact import (
    build_paths_artifact,
)
from bikeability.indicators.path_categories import categorize_paths
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
        paths_artifact = build_paths_artifact(
            line_paths, polygon_paths, params.path_rating, params.get_aoi_geom(), resources
        )

        return [paths_artifact]

    def get_paths(self, aoi: shapely.MultiPolygon) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
        log.debug('Extracting paths')

        paths_line = fetch_osm_data(aoi, ohsome_filter('line'), self.ohsome)
        paths_polygon = fetch_osm_data(aoi, ohsome_filter('polygon'), self.ohsome)

        return paths_line, paths_polygon
