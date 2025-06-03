from functools import partial

import geopandas as gpd
import pandas as pd
import pytest
import shapely
from ohsome import OhsomeClient, OhsomeResponse
from urllib3 import Retry

from bikeability.indicators.path_categories import (
    PathCategory,
    apply_path_category_filters,
    recategorise_zebra_crossings,
)
from bikeability.utils import ohsome_filter, zebra_crossings_filter


@pytest.fixture(scope='module')
def bpolys():
    """Small bounding boxes."""
    bpolys = gpd.GeoSeries(
        data=[
            # large box around Heidelberg:
            shapely.box(8.65354, 49.37019, 8.7836, 49.4447),
            # Lagos: (small box for way/152645928, commented out for speed reasons)
            # shapely.box(3.354680, 6.444900, 3.369928, 6.455165),
            # Ford:
            shapely.box(8.786665, 49.370061, 8.786965, 49.370305),
            # Motorroad:
            shapely.box(8.491960, 49.476107, 8.496047, 49.477822),
        ],
        crs='EPSG:4326',
    )
    return bpolys


@pytest.fixture(scope='module')
def request_ohsome(bpolys):
    return partial(
        OhsomeClient(
            user_agent='HeiGIT Climate Action Bikeability Tester', retry=Retry(total=1)
        ).elements.geometry.post,
        bpolys=bpolys,
        properties='tags',
        time='2024-01-01',
        timeout=60,
    )


validation_objects = {
    PathCategory.EXCLUSIVE: {'way/246387137', 'way/118975501'},
    # https://www.openstreetmap.org/way/246387137 highway=cycleway and foot=no
    # https://www.openstreetmap.org/way/118975501 highway=path and foot=yes and segregated=yes
    PathCategory.SHARED_WITH_PEDESTRIANS: {
        'way/587937936',
        'way/27620739',
        'way/406929620',
        'way/208162626',
        'way/156194371',
    },
    # https://www.openstreetmap.org/way/156194371 highway=path and nothing else (except surface tags)
    # https://www.openstreetmap.org/way/587937936 highway=path and bicycle=designated and foot=designated and segregated=no
    # https://www.openstreetmap.org/way/27620739 highway=footway and bicycle=yes but no foot tag
    # https://www.openstreetmap.org/way/406929620 highway=track
    # https://www.openstreetmap.org/way/208162626 highway=footway and bicycle yes, overlaps with crossing -> part not recategorised
    PathCategory.SHARED_WITH_MOTORISED_TRAFFIC_WALKING_SPEED: {
        'way/34386123',
        'way/27342468',
        'way/715905252',
        'way/35978590',
        'way/274709010',
        'way/440466305',
        'way/83188869',
        'way/191212309',
    },
    # https://www.openstreetmap.org/way/34386123 highway=living_street and bicycle=yes
    # https://www.openstreetmap.org/way/27342468 highway=living_street cycleway:both=no
    # https://www.openstreetmap.org/way/715905252 highway=service and bicycle=yes
    # https://www.openstreetmap.org/way/35978590 highway=service and no bicycle tag
    # https://www.openstreetmap.org/way/274709010 highway=residential and maxspeed=10 and cycleway:both=no
    # https://www.openstreetmap.org/way/440466305 highway=living_street and maxspeed=walk
    # https://www.openstreetmap.org/way/83188869 highway=residential and maxspeed=15 and cycleway:both=no
    # https://www.openstreetmap.org/way/191212309 highway=residential and bicylce=designated ("Fahrradstraße") and maxspeed=15 and motorvehicle=destination
    PathCategory.SHARED_WITH_MOTORISED_TRAFFIC_LOW_SPEED: {
        'way/37685272',
        'way/244287984',
        'way/258562283',
        'way/28891216',
        'way/932097064',
        'way/277455037',
    },
    # https://www.openstreetmap.org/way/37685272 highway=residential and bicycle=designated and bicycle_road=yes ('Fahrradstraße') and maxspeed=30 and motor_vehicle=yes
    # https://www.openstreetmap.org/way/244287984 highway=residential and cycleway:both=no and maxspeed=20
    # https://www.openstreetmap.org/way/258562283 highway=tertiary and cycleway:left=no and cycleway:right=lane and maxspeed=30
    # https://www.openstreetmap.org/way/28891216 highway=primary cycleway:both=lane and maxspeed=30
    # https://www.openstreetmap.org/way/932097064 highway=residential and maxspeed=30 and cycleway:both=no
    # https://www.openstreetmap.org/way/277455037 highway=tertiary and zone:maxspeed=DE:30 and cycleway:right=no
    PathCategory.SHARED_WITH_MOTORISED_TRAFFIC_MEDIUM_SPEED: {
        'way/254010814',
        'way/596760204',
        'way/26816187',
        # 'way/152645928', # Lagos testcase commented out for speed reasons
    },
    # https://www.openstreetmap.org/way/254010814 highway=residential and cycleway:both=lane and maxspeed=50
    # https://www.openstreetmap.org/way/596760204 highway=tertiary and cycleway:both=no and maxspeed=50
    # https://www.openstreetmap.org/way/26816187 highway=residential and maxspeed:type=DE:urban
    # https://www.openstreetmap.org/way/152645928 highway=residential (commented out for speed reasons)
    PathCategory.SHARED_WITH_MOTORISED_TRAFFIC_HIGH_SPEED: {'way/372602113', 'way/189054375', 'way/155281272'},
    # https://www.openstreetmap.org/way/372602113 highway=tertiary and mayspeed=70 and cycleway:both=no
    # https://www.openstreetmap.org/way/189054375 highway=unclassified and maxspeed:type=DE:rural
    # https://www.openstreetmap.org/way/155281272 highway=secondary and maxspeed=70 and cycleway:left=no and cyclewayright=separate
    PathCategory.REQUIRES_DISMOUNTING: {
        'way/810025053',
        'way/131478149',
        'way/24968605',
        'way/27797958',
        'way/87956068',
        'way/208162626',
    },
    # https://www.openstreetmap.org/way/810025053 highway=footway and bicycle=dismount
    # https://www.openstreetmap.org/way/131478149 highway=steps and ramp:bicycle=yes
    # https://www.openstreetmap.org/way/24968605 highway=steps and ramp=yes and ramp:stroller=yes
    # https://www.openstreetmap.org/way/27797958 railway=platform
    # https://www.openstreetmap.org/way/87956068 highway=track and ford=yes
    # https://www.openstreetmap.org/way/208162626 highway=footway and bicycle yes, overlaps with crossing -> recategorised
    PathCategory.PEDESTRIAN_EXCLUSIVE: {
        'way/694458151',
        'way/26028197',
        'way/870757384',
    },
    # https://www.openstreetmap.org/way/694458151 highway=footway and footway=sidewalk (EXCLUSIVE PEDESTRIAN)
    # https://www.openstreetmap.org/way/26028197 highway=footway and bicycle=no (EXCLUSIVE PEDESTRIAN)
    # https://www.openstreetmap.org/way/870757384 highway=pedestrian and bicycle=no (EXCLUSIVE PEDESTRIAN)
    PathCategory.NO_ACCESS: {
        'way/320034117',
        'way/849049867',
        'way/25805786',
        'way/4084008',
        'way/24635973',
        'way/343029968',
    },
    # https://www.openstreetmap.org/way/4084008 highway=trunk
    # https://www.openstreetmap.org/way/24635973 highway=secondary and bicycle=no
    # https://www.openstreetmap.org/way/343029968 highway=primary and motorroad=yes
    # https://www.openstreetmap.org/way/849049867 highway=service and access=no and bus=yes (RESTRICTED ACCESS)
    # https://www.openstreetmap.org/way/25805786 highway=service and access=private (RESTRICTED ACCESS)
    # https://www.openstreetmap.org/way/320034117 highway=footway and access=private (RESTRICTED ACCESS)
    PathCategory.UNKNOWN: set(),
}


# I would prefer to make this fixture return different filters depending on a parameter
@pytest.fixture(scope='module')
def id_filter() -> str:
    """Optimization to make the ohsome API request time faster."""
    full_ids = set().union(*validation_objects.values())
    return f'id:({",".join(full_ids)})'


@pytest.fixture(scope='module')
def osm_return_data(request_ohsome: partial[OhsomeResponse], id_filter: str) -> pd.DataFrame:
    osm_line_data = request_ohsome(filter=f'({ohsome_filter("line")})  and ({id_filter})').as_dataframe(
        multi_index=False
    )
    osm_line_data['category'] = osm_line_data.apply(apply_path_category_filters, axis=1)

    osm_zebra_crossing_data = request_ohsome(filter=zebra_crossings_filter()).as_dataframe(multi_index=False)
    osm_line_data = recategorise_zebra_crossings(osm_line_data, osm_zebra_crossing_data)

    osm_polygon_data = request_ohsome(filter=f'({ohsome_filter("polygon")})  and ({id_filter})').as_dataframe(
        multi_index=False
    )
    osm_polygon_data['category'] = osm_polygon_data.apply(apply_path_category_filters, axis=1)

    return pd.concat([osm_line_data, osm_polygon_data])


@pytest.mark.parametrize('category', validation_objects)
def test_construct_filter_validate(osm_return_data: pd.DataFrame, category: PathCategory):
    osm_return_data = osm_return_data[osm_return_data['category'] == category]

    assert set(osm_return_data['@osmId']) == validation_objects[category]
