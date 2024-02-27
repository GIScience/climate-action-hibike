# You may ask yourself why this file has such a strange name.
# Well ... python imports: https://discuss.python.org/t/warning-when-importing-a-local-module-with-the-same-name-as-a-2nd-or-3rd-party-module/27799

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

import geopandas as gpd
import pandas as pd
import shapely
from PIL import Image
from climatoology.base.artifact import (
    Chart2dData,
    ChartType,
    RasterInfo,
)
from climatoology.base.operator import ComputationResources, Concern, Info, Operator, PluginAuthor, _Artifact
from climatoology.utility.api import LulcUtility, LulcWorkUnit
from ohsome import OhsomeClient
from pandas import DataFrame
from pydantic_extra_types.color import Color
from semver import Version

from plugin_blueprint.artifact import (
    build_markdown_artifact,
    build_table_artifact,
    build_image_artifact,
    build_chart_artifacts,
    build_vector_artifacts,
    build_raster_artifact,
)
from plugin_blueprint.input import ComputeInput

log = logging.getLogger(__name__)


class OperatorBlueprint(Operator[ComputeInput]):
    # This is your working-class hero.
    # See all the details below.

    def __init__(self, lulc_utility: LulcUtility):
        # Create a base connection for the LULC classification utility.
        # Remove it, if you don't plan on using that utility.
        self.lulc_utility = lulc_utility

        # Here is an example for another Utility you can use
        self.ohsome = OhsomeClient(user_agent='CA Plugin Blueprint')

        log.debug(f'Initialised operator with lulc_generator {lulc_utility.base_url} and ohsome client')

    def info(self) -> Info:
        info = Info(
            name='Plugin Blueprint',
            icon=Path('resources/info/icon.jpeg'),
            authors=[
                PluginAuthor(
                    name='Moritz Schott',
                    affiliation='HeiGIT gGmbH',
                    website='https://heigit.org/heigit-team/',
                ),
                PluginAuthor(
                    name='Maciej Adamiak',
                    affiliation='Consultant at HeiGIT gGmbH',
                    website='https://heigit.org/heigit-team/',
                ),
            ],
            version=str(Version(0, 0, 1)),
            concerns=[Concern.CLIMATE_ACTION__GHG_EMISSION],
            purpose=Path('resources/info/purpose.md').read_text(),
            methodology=Path('resources/info/methodology.md').read_text(),
            sources=Path('resources/info/sources.bib'),
        )
        log.info(f'Return info {info.model_dump()}')

        return info

    def compute(self, resources: ComputationResources, params: ComputeInput) -> List[_Artifact]:
        log.info(f'Handling compute request: {params.model_dump()} in context: {resources}')

        # The code is split into several functions from here.
        # Each one describes the functionality of a specific artifact type or utility.
        # Feel free to copy, adapt and delete them at will.

        # ## _Artifact types ##
        # This function creates an example Markdown artifact
        markdown_artifact = OperatorBlueprint.markdown_artifact(params, resources)

        # This function creates an example table artifact
        table_artifact = OperatorBlueprint.table_artifact(params, resources)

        # This function creates an example image artifact
        image_artifact = OperatorBlueprint.image_artifact(resources)

        # This function creates example chart artifacts
        chart_artifacts = OperatorBlueprint.chart_artifacts(params.float_blueprint, resources)

        # Further we have the geographic output types of raster and vector data.
        # We kill two birds with one stone and use the land-use and land-cover utility to demonstrate them.

        # ## Utilities ##

        # ### Ohsome ###
        # This function provides an example for the ohsome usage to create a vector artifact.
        vector_artifacts = self.vector_artifact_and_ohsome_usage(
            params.get_geom(),
            params.date_blueprint,
            resources,
        )

        # ### LULC ###
        # This function provides an example for the LULC utility usage to create a raster artifact.
        raster_artifact = self.raster_artifact_and_lulc_utility_usage(
            params.get_geom(),
            params.date_blueprint,
            resources,
        )
        artifacts = [
            markdown_artifact,
            table_artifact,
            image_artifact,
            *chart_artifacts,
            *vector_artifacts,
            raster_artifact,
        ]
        log.debug(f'Returning {len(artifacts)} artifacts.')

        return artifacts

    @staticmethod
    def markdown_artifact(params: ComputeInput, resources: ComputationResources) -> _Artifact:
        """This method creates a simple Markdown artifact.

        :param params: The input parameters.
        :param resources: The plugin computation resources.
        :return: A Markdown artifact.
        """
        log.debug('Creating dummy markdown artifact.')
        text = OperatorBlueprint.get_md_text(params)

        return build_markdown_artifact(text, resources)

    @staticmethod
    def table_artifact(params: ComputeInput, resources: ComputationResources) -> _Artifact:
        """This method creates a simple table artifact.

        :param params: The input parameters.
        :param resources: The plugin computation resources
        :return: A table artifact.
        """
        table = OperatorBlueprint.get_table(params.string_blueprint)

        return build_table_artifact(table, resources)

    @staticmethod
    def image_artifact(resources: ComputationResources) -> _Artifact:
        """This method creates a simple image artifact.

        :param resources: The plugin computation resources.
        :return: An image artifact.
        """
        log.debug('Creating dummy image artifact.')
        with Image.open('resources/cc0_image.jpg') as image:
            return build_image_artifact(image, resources)

    @staticmethod
    def chart_artifacts(
        incline: float, resources: ComputationResources
    ) -> Tuple[_Artifact, _Artifact, _Artifact, _Artifact]:
        """This method creates four simple chart artifacts.

        :param incline: Some linear incline of the data to make it more interactive.
        :param resources: The plugin computation resources.
        :return: Four graph artifacts.
        """
        scatter_chart_data, line_chart_data, bar_chart_data, pie_chart_data = OperatorBlueprint.get_chart_data(incline)

        return build_chart_artifacts(bar_chart_data, line_chart_data, pie_chart_data, scatter_chart_data, resources)

    def vector_artifact_and_ohsome_usage(
        self,
        aoi: shapely.MultiPolygon,
        target_date: datetime.date,
        resources: ComputationResources,
    ) -> Tuple[_Artifact, _Artifact, _Artifact]:
        """Ohsome example usage for vector artifact creation.

        :param aoi: The area of interest
        :param target_date: The date for which the OSM data will be requested
        :param resources: The plugin computation resources.
        :return: Three vector artifacts.
        """
        points, lines, polygons = self.get_vector_data(aoi, target_date)

        return build_vector_artifacts(lines, points, polygons, resources)

    def raster_artifact_and_lulc_utility_usage(
        self,
        aoi: shapely.MultiPolygon,
        target_date: datetime.date,
        resources: ComputationResources,
    ) -> _Artifact:
        """LULC Utility example usage for raster artifact creation.

        This is a very simplified example of usage for the LULC utility.
        It requests a user-defined area from the services for a fixed date and returns the result.

        :param aoi: The area of interest
        :param target_date: The date for which the classification will be requested
        :param resources: The plugin computation resources.
        :return: A raster artifact.
        """
        log.debug('Creating dummy raster artifact.')
        # Be aware that there are more parameters to the LULCWorkUnit which affect the configuration of the service.
        # These can be handed to the user for adaption via the input parameters.
        aoi = LulcWorkUnit(area_coords=aoi.bounds, end_date=target_date.isoformat())

        with self.lulc_utility.compute_raster([aoi]) as lulc_classification:
            raster_info = RasterInfo(
                data=lulc_classification.read(),
                crs=lulc_classification.crs,
                transformation=lulc_classification.transform,
                colormap=lulc_classification.colormap(1),
            )

            return build_raster_artifact(raster_info, resources)

    @staticmethod
    def get_md_text(params: ComputeInput) -> str:
        """Transform the input parameters to Markdown text with json blocks."""
        return f"""# Input Parameters

The Plugin Blueprint was run with the following parameters.
You can check if your input was received in the correct manner.
Be aware that if you did not specify a value, some of the optional parameters may use defaults.

```json
{params.model_dump_json(indent=4, exclude={'aoi_blueprint'})}
```

In addition the following area of interest was sent:

```json
{params.aoi_blueprint.model_dump_json(indent=4)}
```
"""

    @staticmethod
    def get_table(text: str) -> pd.DataFrame:
        """Counts the number of occurrences of each character in a string."""
        log.debug('Creating dummy table artifact.')
        data = [{'character': e, 'count': text.lower().count(e)} for e in set(text.lower())]
        table = DataFrame.from_records(data, index='character')
        table = table.sort_values(by=['count', 'character'], ascending=[False, True])
        return table

    @staticmethod
    def get_chart_data(incline: float) -> Tuple[Chart2dData, Chart2dData, Chart2dData, Chart2dData]:
        """Creates a scatter plot, a line chart, a bar chart and a pie chart."""
        log.debug('Creating dummy chart artifacts.')

        x = list(range(0, 100, 10))
        y = [val * -abs(incline) for val in x]

        scatter_chart_data = Chart2dData(x=x, y=y, chart_type=ChartType.SCATTER)

        line_chart_data = Chart2dData(x=x, y=y, chart_type=ChartType.LINE)

        bar_chart_data = Chart2dData(x=[str(val) for val in x], y=y, chart_type=ChartType.BAR)

        y = [abs(int(val)) for val in y]
        pie_chart_data = Chart2dData(
            x=x,
            y=y,
            color=[
                Color('#a6cee3'),
                Color('#1f78b4'),
                Color('#b2df8a'),
                Color('#33a02c'),
                Color('#fb9a99'),
                Color('#e31a1c'),
                Color('#fdbf6f'),
                Color('#ff7f00'),
                Color('#cab2d6'),
                Color('#6a3d9a'),
            ],
            chart_type=ChartType.PIE,
        )

        return scatter_chart_data, line_chart_data, bar_chart_data, pie_chart_data

    def get_vector_data(
        self, aoi: shapely.MultiPolygon, target_date: datetime.date
    ) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, gpd.GeoDataFrame]:
        """Schools from OSM.

        First schools are requested as points from OSM. Then these points, a buffer and the buffer outline are
        returned as point, line and polygon GeoDataFrame."""
        log.debug('Creating dummy vector artifact.')
        ohsome_response = self.ohsome.elements.centroid.post(bpolys=aoi, time=target_date, filter='amenity=school')
        elements = ohsome_response.as_dataframe()
        elements['color'] = Color('blue')

        # We add a default element in case the output is empty
        waldo = gpd.GeoDataFrame({'color': [Color('red')], 'geometry': [aoi.centroid]}, crs='EPSG:4326')

        points = gpd.GeoDataFrame(pd.concat([elements, waldo]))
        points = points.reset_index(drop=True)[['color', 'geometry']]

        polygons = points.to_crs('ESRI:54012')
        polygons.geometry = polygons.buffer(100, resolution=2, cap_style=3)
        polygons = polygons.to_crs(4326)

        lines = polygons.copy()
        lines.geometry = lines.boundary

        return points, lines, polygons
