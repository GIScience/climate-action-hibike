import geopandas as gpd
from plotly.graph_objects import Figure
from pyproj import CRS

from bikeability.indicators.path_categories import PathCategory
from bikeability.path_summarisation import summarise_aoi, summarise_naturalness


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


def test_summarise_naturalness(default_path_geometry, default_polygon_geometry):
    input_paths = gpd.GeoDataFrame(
        data={
            'naturalness': [0.4, 0.6],
            'geometry': [default_path_geometry] + [default_polygon_geometry],
        },
        crs='EPSG:4326',
    )
    bar_chart = summarise_naturalness(paths=input_paths, projected_crs=CRS.from_user_input(32632))

    assert isinstance(bar_chart, Figure)
    assert bar_chart['data'][0]['x'] == ('Medium (0.3 to 0.6)',)
    assert bar_chart['data'][0]['y'] == (0.12,)
