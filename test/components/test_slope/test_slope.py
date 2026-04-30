import numpy as np
import plotly.graph_objects as go
import pytest
from climatoology.base.artifact import Artifact
from climatoology.base.exception import ClimatoologyUserError

from bikeability.components.slope.slope_analysis import compute_slope_analysis, summarise_slope


def test_compute_slope_analysis(default_paths, compute_resources, slopes_mock, default_s3_settings):
    artifacts = compute_slope_analysis(paths=default_paths, s3settings=default_s3_settings, resources=compute_resources)

    for artifact in artifacts:
        assert isinstance(artifact, Artifact)


def test_compute_slope_fail_without_s3settings(default_paths, compute_resources):
    with pytest.raises(ClimatoologyUserError):
        compute_slope_analysis(paths=default_paths, resources=compute_resources, s3settings=None)


def test_summarise_slope(default_slopes_gdf):
    histogram_chart = summarise_slope(path_slopes_data=default_slopes_gdf)

    assert isinstance(histogram_chart, go.Figure)
    np.testing.assert_array_equal(histogram_chart.data[0].x, [1, 2, 3, 6.9])
