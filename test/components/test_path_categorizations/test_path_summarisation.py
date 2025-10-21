import geopandas as gpd
from plotly.graph_objects import Figure
from pyproj import CRS

from bikeability.components.path_categories.path_categories import PathCategory
from bikeability.components.path_categories.path_summaries import summarise_aoi


def test_summarise_aoi(default_path_geometry, default_polygon_geometry):
    input_paths = gpd.GeoDataFrame(
        data={
            'category': 2 * [PathCategory.EXCLUSIVE],
            'geometry': [default_path_geometry] + [default_polygon_geometry],
        },
        crs='EPSG:4326',
    )
    category_stacked_bar_chart = summarise_aoi(paths=input_paths, projected_crs=CRS.from_user_input(32632))

    assert isinstance(category_stacked_bar_chart, Figure)
    assert category_stacked_bar_chart['data'][0]['y'] == ('Path Types',)
    assert category_stacked_bar_chart['data'][0]['x'] == (100,)
