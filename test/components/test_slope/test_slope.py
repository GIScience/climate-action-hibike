import geopandas as gpd
import numpy as np
import plotly.graph_objects as go
import pytest
import shapely
from climatoology.base.artifact import Artifact
from climatoology.base.exception import ClimatoologyUserError
from geopandas.testing import assert_geodataframe_equal, assert_geoseries_equal
from pandas.testing import assert_frame_equal

from bikeability.components.slope.slope_analysis import compute_slope_analysis, merge_similar_slopes, summarise_slope


def test_compute_slope_analysis(default_paths, compute_resources, slopes_mock, default_s3_settings):
    artifacts = compute_slope_analysis(paths=default_paths, s3settings=default_s3_settings, resources=compute_resources)

    for artifact in artifacts:
        assert isinstance(artifact, Artifact)


def test_compute_slope_fail_without_s3settings(default_paths, compute_resources):
    with pytest.raises(ClimatoologyUserError):
        compute_slope_analysis(paths=default_paths, resources=compute_resources, s3settings=None)


def test_merge_similar_slopes_similar():
    input_slope_paths = gpd.GeoDataFrame(
        data={'@osmId': ['a', 'a', 'a', 'b'], 'slope': [0.012, 0.013, 0.011, 0.2]},
        geometry=[
            shapely.LineString([(0, 0), (0, 1)]),
            shapely.LineString([(0, 1), (1, 1)]),
            shapely.LineString([(1, 1), (1, 0)]),
            shapely.LineString([(0, 0), (0, 1)]),
        ],
        crs=4326,
    )

    expected = gpd.GeoDataFrame(
        data={'@osmId': ['a', 'b'], 'slope': [0.012, 0.2]},
        geometry=[shapely.LineString([(0, 0), (0, 1), (1, 1), (1, 0)]), shapely.LineString([(0, 0), (0, 1)])],
        crs=4326,
    )

    received = merge_similar_slopes(input_slope_paths, merging_tolerance=0.05)

    assert_geoseries_equal(received.geometry, expected.geometry)
    assert_frame_equal(received[['@osmId', 'slope']], expected[['@osmId', 'slope']], atol=0.01)


def test_no_merge_similar_slopes_with_outlier():
    input_slope_paths = gpd.GeoDataFrame(
        data={'@osmId': ['a', 'a', 'a'], 'slope': [0.012, 0.013, 0.2]},
        geometry=[
            shapely.LineString([(0, 0), (0, 1)]),
            shapely.LineString([(0, 1), (1, 1)]),
            shapely.LineString([(1, 1), (1, 0)]),
        ],
        crs=4326,
    )

    received = merge_similar_slopes(input_slope_paths, merging_tolerance=0.05)

    assert_geodataframe_equal(received, input_slope_paths)


def test_summarise_slope(default_slopes_gdf):
    histogram_chart = summarise_slope(path_slopes_data=default_slopes_gdf)

    assert isinstance(histogram_chart, go.Figure)
    np.testing.assert_array_equal(histogram_chart.data[0].x, [1, 2, 3, 6.9])
