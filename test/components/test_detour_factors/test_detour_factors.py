from unittest.mock import patch

import geopandas as gpd
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytest
from climatoology.base.artifact import _Artifact
from climatoology.utility.exception import ClimatoologyUserError
from mobility_tools.utils.exceptions import SizeLimitExceededError
from pydantic_extra_types.color import Color

from bikeability.components.detour_factors.detour_analysis import (
    DetourCategory,
    apply_color_and_label,
    build_detour_factor_artifact,
    detour_factor_analysis,
    summarise_detour,
)


def test_build_detour_factor_artifact(default_polygon_geometry, compute_resources):
    test_detour_df = gpd.GeoDataFrame(
        {'detour_factor': [1.0, 2.5, 3.5, np.nan]},
        geometry=[
            default_polygon_geometry,
            default_polygon_geometry,
            default_polygon_geometry,
            default_polygon_geometry,
        ],
        crs='EPSG:4326',
    )

    artifact = build_detour_factor_artifact(test_detour_df, compute_resources)

    assert isinstance(artifact, _Artifact)


def test_detour_factors(default_aoi, test_line, default_ors_settings, compute_resources, detour_factor_mock):
    artifacts = detour_factor_analysis(default_aoi, test_line, default_ors_settings, compute_resources)

    for artifact in artifacts:
        assert isinstance(artifact, _Artifact)


@pytest.fixture
def detour_factor_mock_fail(expected_detour_factors):
    with patch('bikeability.components.detour_factors.detour_analysis.get_detour_factors') as get_detour_factors:
        get_detour_factors.side_effect = SizeLimitExceededError()
        yield get_detour_factors


def test_detour_factors_fail(default_aoi, test_line, default_ors_settings, compute_resources, detour_factor_mock_fail):
    with pytest.raises(ClimatoologyUserError):
        detour_factor_analysis(default_aoi, test_line, default_ors_settings, compute_resources)


def test_apply_detour_color_and_label(default_polygon_geometry):
    test_detour_df = gpd.GeoDataFrame(
        {'detour_factor': [1.0, 2.5, 3.5, np.nan]}, geometry=[default_polygon_geometry] * 4, crs='EPSG:4326'
    )

    expected_detour_df = gpd.GeoDataFrame(
        {
            'detour_factor': [2.5, 3.5, np.nan],
            'detour_category': [DetourCategory.MEDIUM_DETOUR, DetourCategory.HIGH_DETOUR, DetourCategory.UNREACHABLE],
            'color': [Color('#eea321'), Color('#e75a13'), Color('#990404')],
            'label': ['Medium Detour', 'High Detour', 'Unreachable'],
        },
        geometry=[default_polygon_geometry] * 3,
        crs='EPSG:4326',
    )

    received_detour_df = apply_color_and_label(test_detour_df)
    pd.testing.assert_frame_equal(received_detour_df.reset_index(drop=True), expected_detour_df, check_like=True)


def test_summarise_detour(default_polygon_geometry):
    input_hexgrid = gpd.GeoDataFrame(
        data={
            'detour_factor': [0, 3, 6, 10],
            'geometry': 4 * [default_polygon_geometry],
        },
        crs='EPSG:4326',
    )
    chart = summarise_detour(hexgrid=input_hexgrid)

    assert isinstance(chart, go.Figure)
    np.testing.assert_array_equal(chart['data'][0]['x'], ([0, 3, 6, 10]))


def test_summarise_detour_inf(default_polygon_geometry):
    input_hexgrid = gpd.GeoDataFrame(
        data={
            'detour_factor': [0, 3, 6, np.inf],
            'geometry': 4 * [default_polygon_geometry],
        },
        crs='EPSG:4326',
    )
    chart = summarise_detour(hexgrid=input_hexgrid)

    assert isinstance(chart, go.Figure)
    np.testing.assert_array_equal(chart['data'][0]['x'], ([0, 3, 6, np.inf]))
