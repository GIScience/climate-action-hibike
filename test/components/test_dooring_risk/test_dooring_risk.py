import geopandas as gpd
import pandas as pd
import pytest
import shapely
from geopandas.testing import assert_geodataframe_equal
from ohsome_filter_to_sql.main import validate_filter
from pandas.testing import assert_series_equal
from plotly.graph_objects import Figure
from pyproj import CRS

from bikeability.components.dooring_risk.dooring_risk import (
    DooringRiskCategory,
    apply_dooring_filters,
    find_nearest_parking,
    get_dooring_risk,
    parallel_parking_filter,
)
from bikeability.components.dooring_risk.dooring_risk_summary import summarise_dooring_risk
from bikeability.components.path_sharing.path_sharing import PathSharing
from bikeability.components.utils.utils import (
    fetch_osm_data,
)

expected_parking_line = gpd.GeoDataFrame(
    data={
        'osm_id': ['1205391562'],
        'osm_type': ['way'],
        'osm_tags': [{'amenity': 'parking', 'orientation': 'parallel', 'parking': 'street_side'}],
    },
    geometry=[
        shapely.LineString([(12.3, 48.22), (12.3, 48.2205), (12.3005, 48.22)]),
    ],
    crs=4326,
)


expected_parking_polygon = gpd.GeoDataFrame(
    data={
        'osm_id': ['1205391562'],
        'osm_type': ['way'],
        'osm_tags': [{'amenity': 'parking', 'orientation': 'parallel', 'parking': 'street_side'}],
    },
    geometry=[
        shapely.from_wkt(
            'POLYGON ((8.45979 49.4326487, 8.4597687 49.4326603, 8.4597353 49.4326784, 8.4594568 49.4324616, 8.4594874 49.432445, 8.4595115 49.4324319, 8.4597393 49.4326092, 8.45979 49.4326487))'
        ),
    ],
    crs=4326,
)


@pytest.fixture
def dooring_risk():
    tags = [
        {'parking:both:orientation': 'parallel'},
        {'parking:right:orientation': 'parallel'},
        {'parking:left:orientation': 'parallel'},
        {'parking:lane:both': 'parallel'},
        {'parking:lane:left': 'parallel'},
        {'parking:lane:right': 'parallel'},
        {'parking:both': 'separate'},
    ]

    parking = [False for _ in tags]
    parking[-1] = True
    dooring_risk_tags = pd.DataFrame(
        data={
            'osm_tags': tags,
            'expected_dooring_risk': [DooringRiskCategory.DOORING_RISK for _ in tags],
            'parking': parking,
            'path_sharing': [PathSharing.SHARED_WITH_MOTORISED_TRAFFIC_MEDIUM_SPEED for _ in tags],
        }
    )

    return dooring_risk_tags


@pytest.fixture
def dooring_safe():
    tags = [
        {'parking:lane:both': 'no'},
        {'parking:both:orientation': 'perpendicular'},
        {'parking:right:orientation': 'perpendicular', 'parking:left:orientation': 'perpendicular'},
        {'parking:left:orientation': 'perpendicular', 'parking:right': 'no'},
        {'parking:both:orientation': 'diagonal'},
        {'parking:left:orientation': 'diagonal', 'parking:right': 'no'},
        {'parking:right:orientation': 'diagonal', 'parking:left': 'no'},
        {'parking:both:orientation': 'parallel'},
    ]

    category = [PathSharing.SHARED_WITH_MOTORISED_TRAFFIC_MEDIUM_SPEED for _ in tags]
    category[-1] = PathSharing.EXCLUSIVE

    dooring_risk_tags = pd.DataFrame(
        data={
            'osm_tags': tags,
            'expected_dooring_risk': [DooringRiskCategory.DOORING_SAFE for _ in tags],
            'parking': [False for _ in tags],
            'path_sharing': category,
        }
    )

    return dooring_risk_tags


@pytest.fixture
def dooring_unknown():
    return pd.DataFrame(
        data={
            'osm_tags': [{}],
            'expected_dooring_risk': [DooringRiskCategory.UNKNOWN],
            'path_sharing': [PathSharing.SHARED_WITH_MOTORISED_TRAFFIC_LOW_SPEED],
            'parking': [False],
        }
    )


@pytest.fixture
def dooring_test_cases(dooring_risk, dooring_safe, dooring_unknown):
    return pd.concat([dooring_risk, dooring_safe, dooring_unknown])


def test_find_nearest_parking():
    line_paths = gpd.GeoDataFrame(
        data={
            'osm_id': ['1', '2'],
            'osm_type': ['way'] * 2,
            'osm_tags': [{'amenity': 'parking', 'orientation': 'parallel'}] * 2,
            'path_sharing': [None] * 2,
        },
        geometry=[
            shapely.LineString([[0, 0], [0, 1], [2, 1], [2, 2]]),  # have nearest parking
            shapely.LineString([[20, 0], [20, 1], [22, 1], [22, 2]]),  # do not have nearest parking
        ],
        crs=32632,
    ).to_crs(4326)
    parking_polygons = gpd.GeoDataFrame(
        data={
            'osm_id': ['10', '20'],
            'osm_type': ['relation', 'relation'],
            'osm_tags': [{'amenity': 'parking', 'orientation': 'parallel'}] * 2,
        },
        geometry=[
            shapely.box(2.1, 0, 3, 4),
            shapely.MultiPolygon(
                polygons=[
                    shapely.box(-2, 2, -0.1, 4),
                    shapely.box(-2, 1, -1.1, 1.99),
                ]
            ),
        ],
        crs=32632,
    ).to_crs(4326)

    line_paths_with_parking = find_nearest_parking(line_paths, parking_polygons)

    assert isinstance(line_paths_with_parking, gpd.GeoDataFrame)
    assert not line_paths_with_parking.empty
    assert all(line_paths_with_parking['parking'].values == [True, False])
    assert all(
        [
            col in line_paths_with_parking
            for col in ['osm_id', 'osm_type', 'osm_tags', 'geometry', 'parking', 'path_sharing']
        ]
    )


@pytest.mark.vcr
def test_parking_filter(parametrized_ohsome_client, default_aoi):
    fetch_parking_data = fetch_osm_data(
        aoi=default_aoi, osm_filter=parallel_parking_filter('polygon'), ohsome=parametrized_ohsome_client
    )

    assert isinstance(fetch_parking_data, gpd.GeoDataFrame)
    assert not fetch_parking_data.empty
    assert all([col in fetch_parking_data for col in ['osm_id', 'osm_type', 'osm_tags', 'geometry']])
    assert all(fetch_parking_data.geom_type == 'Polygon')
    assert all(
        fetch_parking_data['osm_tags'].apply(
            lambda x: x.get('amenity') == 'parking' and x.get('orientation') == 'parallel'
        )
    )


@pytest.mark.parametrize('geometry_type', ['line', 'polygon'])
def test_parking_filter_syntax(geometry_type):
    validate_filter(parallel_parking_filter(geometry_type))


def test_dooring_filter(dooring_test_cases):
    result = dooring_test_cases.apply(apply_dooring_filters, axis=1)

    assert_series_equal(result, dooring_test_cases['expected_dooring_risk'], check_names=False)


def test_get_dooring_risk(default_paths, expected_parking_polygon):
    result = get_dooring_risk(default_paths, expected_parking_polygon)

    expected_result = gpd.GeoDataFrame(default_paths.iloc[1:2].reset_index(drop=True))
    expected_result['dooring_category'] = DooringRiskCategory.DOORING_SAFE
    assert_geodataframe_equal(
        result,
        expected_result[['osm_id', 'osm_type', 'geometry', 'dooring_category']],
        check_less_precise=True,
    )


def test_get_dooring_risk_missing_geometry_types(test_line, test_polygon, expected_parking_polygon):
    dooring_risk_polygon_paths = get_dooring_risk(test_polygon, expected_parking_polygon)
    dooring_risk_line_paths = get_dooring_risk(test_line, expected_parking_polygon)

    result = pd.concat([dooring_risk_line_paths, dooring_risk_polygon_paths], ignore_index=True)

    expected_result = gpd.GeoDataFrame(test_line.iloc[1:2].reset_index(drop=True))
    expected_result['dooring_category'] = DooringRiskCategory.DOORING_SAFE
    assert_geodataframe_equal(
        result,
        expected_result[['osm_id', 'osm_type', 'geometry', 'dooring_category']],
        check_less_precise=True,
    )


def test_summarise_dooring_risk(default_path_geometry, default_polygon_geometry):
    input_paths = gpd.GeoDataFrame(
        data={
            'dooring_category': [DooringRiskCategory.DOORING_RISK, None] + 3 * [DooringRiskCategory.DOORING_SAFE],
            'geometry': 4 * [default_path_geometry] + [default_polygon_geometry],
        },
        crs='EPSG:4326',
    )
    category_stacked_bar_chart = summarise_dooring_risk(paths=input_paths, projected_crs=CRS.from_user_input(32632))

    assert isinstance(category_stacked_bar_chart, Figure)
    assert category_stacked_bar_chart['data'][0]['x'] == pytest.approx((66.67,), abs=0.01)
