import pandas as pd
from ohsome_filter_to_sql.main import validate_filter

from bikeability.components.path_categories.path_categories import (
    PathCategory,
    apply_path_category_filters,
    zebra_crossings_filter,
)

EXCLUSIVE_DF = pd.DataFrame(
    {
        '@osmId': ['way/246387137', 'way/118975501'],
        '@other_tags': [{'highway': 'cycleway', 'foot': 'no'}, {'highway': 'path', 'foot': 'yes', 'segregated': 'yes'}],
        'expected_category': [PathCategory.EXCLUSIVE, PathCategory.EXCLUSIVE],
    }
)

SHARED_WITH_PEDESTRIANS_DF = pd.DataFrame(
    {
        '@osmId': ['way/587937936', 'way/27620739', 'way/406929620', 'way/208162626', 'way/156194371'],
        '@other_tags': [
            {'highway': 'path'},
            {'highway': 'path', 'bicycle': 'designated', 'foot': 'designated', 'segregated': 'no'},
            {'highway': 'footway', 'bicycle': 'yes'},
            {'highway': 'track'},
            {'highway': 'footway', 'bicycle': 'yes'},
        ],
        'expected_category': [
            PathCategory.SHARED_WITH_PEDESTRIANS,
            PathCategory.SHARED_WITH_PEDESTRIANS,
            PathCategory.SHARED_WITH_PEDESTRIANS,
            PathCategory.SHARED_WITH_PEDESTRIANS,
            PathCategory.SHARED_WITH_PEDESTRIANS,
        ],
    }
)


SHARED_WITH_MOTORISED_TRAFFIC_WALKING_SPEED_DF = pd.DataFrame(
    {
        '@osmId': [
            'way/34386123',
            'way/27342468',
            'way/715905252',
            'way/35978590',
            'way/274709010',
            'way/440466305',
            'way/83188869',
            'way/191212309',
        ],
        '@other_tags': [
            {'highway': 'living_street', 'bicycle': 'yes'},
            {'highway': 'living_street', 'cycleway:both': 'no'},
            {'highway': 'service', 'bicycle': 'yes'},
            {'highway': 'service'},
            {'highway': 'residential', 'maxspeed': '10', 'cycleway:both': 'no'},
            {'highway': 'living_street', 'maxspeed': 'walk'},
            {'highway': 'residential', 'maxspeed': '15', 'cycleway:both': 'no'},
            {'highway': 'residential', 'bicycle': 'designated', 'maxspeed': '15', 'motorvehicle': 'destination'},
        ],
        'expected_category': [
            PathCategory.SHARED_WITH_MOTORISED_TRAFFIC_WALKING_SPEED,
            PathCategory.SHARED_WITH_MOTORISED_TRAFFIC_WALKING_SPEED,
            PathCategory.SHARED_WITH_MOTORISED_TRAFFIC_WALKING_SPEED,
            PathCategory.SHARED_WITH_MOTORISED_TRAFFIC_WALKING_SPEED,
            PathCategory.SHARED_WITH_MOTORISED_TRAFFIC_WALKING_SPEED,
            PathCategory.SHARED_WITH_MOTORISED_TRAFFIC_WALKING_SPEED,
            PathCategory.SHARED_WITH_MOTORISED_TRAFFIC_WALKING_SPEED,
            PathCategory.SHARED_WITH_MOTORISED_TRAFFIC_WALKING_SPEED,
        ],
    }
)


SHARED_WITH_MOTORISED_TRAFFIC_LOW_SPEED_DF = pd.DataFrame(
    {
        '@osmId': ['way/37685272', 'way/244287984', 'way/258562283', 'way/28891216', 'way/932097064', 'way/277455037'],
        '@other_tags': [
            {
                'highway': 'residential',
                'bicycle': 'designated',
                'bicycle_road': 'yes',
                'maxspeed': '30',
                'motor_vehicle': 'yes',
            },
            {'highway': 'residential', 'cycleway:both': 'no', 'maxspeed': '20'},
            {'highway': 'tertiary', 'cycleway:left': 'no', 'cycleway:right': 'lane', 'maxspeed': '30'},
            {'highway': 'primary', 'cycleway:both': 'lane', 'maxspeed': '30'},
            {'highway': 'residential', 'maxspeed': '30', 'cycleway:both': 'no'},
            {'highway': 'tertiary', 'zone:maxspeed': 'DE:30', 'cycleway:right': 'no'},
        ],
        'expected_category': [
            PathCategory.SHARED_WITH_MOTORISED_TRAFFIC_LOW_SPEED,
            PathCategory.SHARED_WITH_MOTORISED_TRAFFIC_LOW_SPEED,
            PathCategory.SHARED_WITH_MOTORISED_TRAFFIC_LOW_SPEED,
            PathCategory.SHARED_WITH_MOTORISED_TRAFFIC_LOW_SPEED,
            PathCategory.SHARED_WITH_MOTORISED_TRAFFIC_LOW_SPEED,
            PathCategory.SHARED_WITH_MOTORISED_TRAFFIC_LOW_SPEED,
        ],
    }
)


SHARED_WITH_MOTORISED_TRAFFIC_MEDIUM_SPEED_DF = pd.DataFrame(
    {
        '@osmId': ['way/254010814', 'way/596760204', 'way/26816187'],
        '@other_tags': [
            {'highway': 'residential', 'cycleway:both': 'lane', 'maxspeed': '50'},
            {'highway': 'tertiary', 'cycleway:both': 'no', 'maxspeed': '50'},
            {'highway': 'residential', 'maxspeed:type': 'DE:urban'},
        ],
        'expected_category': [
            PathCategory.SHARED_WITH_MOTORISED_TRAFFIC_MEDIUM_SPEED,
            PathCategory.SHARED_WITH_MOTORISED_TRAFFIC_MEDIUM_SPEED,
            PathCategory.SHARED_WITH_MOTORISED_TRAFFIC_MEDIUM_SPEED,
        ],
    }
)
# 'way/152645928', highway=residential # Lagos testcase commented out for speed reasons


SHARED_WITH_MOTORISED_TRAFFIC_HIGH_SPEED_DF = pd.DataFrame(
    {
        '@osmId': ['way/372602113', 'way/189054375', 'way/155281272'],
        '@other_tags': [
            {'highway': 'tertiary', 'maxspeed': '70', 'cycleway:both': 'no'},
            {'highway': 'unclassified', 'maxspeed:type': 'DE:rural'},
            {'highway': 'secondary', 'maxspeed': '70', 'cycleway:left': 'no', 'cycleway:right': 'separate'},
        ],
        'expected_category': [
            PathCategory.SHARED_WITH_MOTORISED_TRAFFIC_HIGH_SPEED,
            PathCategory.SHARED_WITH_MOTORISED_TRAFFIC_HIGH_SPEED,
            PathCategory.SHARED_WITH_MOTORISED_TRAFFIC_HIGH_SPEED,
        ],
    }
)


SHARED_WITH_MOTORISED_TRAFFIC_UNKNOWN_SPEED_DF = pd.DataFrame(
    {
        '@osmId': ['way/25108534', 'way/276155445', 'way/31146043'],
        '@other_tags': [
            {'highway': 'primary_link', 'cycleway:both': 'no'},
            {'highway': 'tertiary'},
            {'highway': 'tertiary', 'cycleway': 'no'},
        ],
        'expected_category': [
            PathCategory.SHARED_WITH_MOTORISED_TRAFFIC_UNKNOWN_SPEED,
            PathCategory.SHARED_WITH_MOTORISED_TRAFFIC_UNKNOWN_SPEED,
            PathCategory.SHARED_WITH_MOTORISED_TRAFFIC_UNKNOWN_SPEED,
        ],
    }
)


REQUIRES_DISMOUNTING_DF = pd.DataFrame(
    {
        '@osmId': ['way/810025053', 'way/131478149', 'way/24968605', 'way/27797958', 'way/87956068'],
        '@other_tags': [
            {'highway': 'footway', 'bicycle': 'dismount'},
            {'highway': 'steps', 'ramp:bicycle': 'yes'},
            {'highway': 'steps', 'ramp': 'yes', 'ramp:stroller': 'yes'},
            {'railway': 'platform'},
            {'highway': 'track', 'ford': 'yes'},
        ],
        'expected_category': [
            PathCategory.REQUIRES_DISMOUNTING,
            PathCategory.REQUIRES_DISMOUNTING,
            PathCategory.REQUIRES_DISMOUNTING,
            PathCategory.REQUIRES_DISMOUNTING,
            PathCategory.REQUIRES_DISMOUNTING,
        ],
    }
)
# 'way/208162626', 'highway': 'footway', 'bicycle': 'yes' overlaps with crossing --> recategorized?


PEDESTRIAN_EXCLUSIVE_DF = pd.DataFrame(
    {
        '@osmId': ['way/694458151', 'way/26028197', 'way/870757384'],
        '@other_tags': [
            {'highway': 'footway', 'footway': 'sidewalk'},
            {'highway': 'footway', 'bicycle': 'no'},
            {'highway': 'pedestrian', 'bicycle': 'no'},
        ],
        'expected_category': [
            PathCategory.PEDESTRIAN_EXCLUSIVE,
            PathCategory.PEDESTRIAN_EXCLUSIVE,
            PathCategory.PEDESTRIAN_EXCLUSIVE,
        ],
    }
)


NO_ACCESS_DF = pd.DataFrame(
    {
        '@osmId': ['way/320034117', 'way/849049867', 'way/25805786', 'way/4084008', 'way/24635973', 'way/343029968'],
        '@other_tags': [
            {'highway': 'trunk'},
            {'highway': 'secondary', 'bicycle': 'no'},
            {'highway': 'primary', 'motorroad': 'yes'},
            {'highway': 'service', 'access': 'no', 'bus': 'yes'},
            {'highway': 'service', 'access': 'private'},
            {'highway': 'footway', 'access': 'private'},
        ],
        'expected_category': [
            PathCategory.NO_ACCESS,
            PathCategory.NO_ACCESS,
            PathCategory.NO_ACCESS,
            PathCategory.NO_ACCESS,
            PathCategory.NO_ACCESS,
            PathCategory.NO_ACCESS,
        ],
    }
)


FILTER_VALIDATION_OBJECTS = pd.concat(
    [
        EXCLUSIVE_DF,
        SHARED_WITH_PEDESTRIANS_DF,
        SHARED_WITH_MOTORISED_TRAFFIC_WALKING_SPEED_DF,
        SHARED_WITH_MOTORISED_TRAFFIC_LOW_SPEED_DF,
        SHARED_WITH_MOTORISED_TRAFFIC_MEDIUM_SPEED_DF,
        SHARED_WITH_MOTORISED_TRAFFIC_HIGH_SPEED_DF,
        SHARED_WITH_MOTORISED_TRAFFIC_UNKNOWN_SPEED_DF,
        REQUIRES_DISMOUNTING_DF,
        PEDESTRIAN_EXCLUSIVE_DF,
        NO_ACCESS_DF,
    ]
)


def test_construct_filter_validate():
    FILTER_VALIDATION_OBJECTS['received_category'] = FILTER_VALIDATION_OBJECTS.apply(
        apply_path_category_filters, axis=1
    )

    pd.testing.assert_series_equal(
        FILTER_VALIDATION_OBJECTS['received_category'],
        FILTER_VALIDATION_OBJECTS['expected_category'],
        check_names=False,
    )


def test_crossings_filter():
    validate_filter(zebra_crossings_filter())
