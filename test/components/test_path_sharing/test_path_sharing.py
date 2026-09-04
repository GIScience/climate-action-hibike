import pandas as pd
import pytest

from bikeability.components.path_sharing.path_sharing import (
    PathSharing,
    apply_path_sharing_filters,
)

EXCLUSIVE_DF = pd.DataFrame(
    {
        'osm_tags': [{'highway': 'cycleway', 'foot': 'no'}, {'highway': 'path', 'foot': 'yes', 'segregated': 'yes'}],
        'expected_category': [PathSharing.EXCLUSIVE, PathSharing.EXCLUSIVE],
    }
)

SHARED_WITH_PEDESTRIANS_DF = pd.DataFrame(
    {
        'osm_tags': [
            {'highway': 'path'},
            {'highway': 'path', 'bicycle': 'designated', 'foot': 'designated', 'segregated': 'no'},
            {'highway': 'footway', 'bicycle': 'yes'},
            {'highway': 'track'},
            {'highway': 'footway', 'bicycle': 'yes'},
        ],
        'expected_category': [
            PathSharing.SHARED_WITH_PEDESTRIANS,
            PathSharing.SHARED_WITH_PEDESTRIANS,
            PathSharing.SHARED_WITH_PEDESTRIANS,
            PathSharing.SHARED_WITH_PEDESTRIANS,
            PathSharing.SHARED_WITH_PEDESTRIANS,
        ],
    }
)


SHARED_WITH_MOTORISED_TRAFFIC_WALKING_SPEED_DF = pd.DataFrame(
    {
        'osm_tags': [
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
            PathSharing.SHARED_WITH_MOTORISED_TRAFFIC_WALKING_SPEED,
            PathSharing.SHARED_WITH_MOTORISED_TRAFFIC_WALKING_SPEED,
            PathSharing.SHARED_WITH_MOTORISED_TRAFFIC_WALKING_SPEED,
            PathSharing.SHARED_WITH_MOTORISED_TRAFFIC_WALKING_SPEED,
            PathSharing.SHARED_WITH_MOTORISED_TRAFFIC_WALKING_SPEED,
            PathSharing.SHARED_WITH_MOTORISED_TRAFFIC_WALKING_SPEED,
            PathSharing.SHARED_WITH_MOTORISED_TRAFFIC_WALKING_SPEED,
            PathSharing.SHARED_WITH_MOTORISED_TRAFFIC_WALKING_SPEED,
        ],
    }
)


SHARED_WITH_MOTORISED_TRAFFIC_LOW_SPEED_DF = pd.DataFrame(
    {
        'osm_tags': [
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
            PathSharing.SHARED_WITH_MOTORISED_TRAFFIC_LOW_SPEED,
            PathSharing.SHARED_WITH_MOTORISED_TRAFFIC_LOW_SPEED,
            PathSharing.SHARED_WITH_MOTORISED_TRAFFIC_LOW_SPEED,
            PathSharing.SHARED_WITH_MOTORISED_TRAFFIC_LOW_SPEED,
            PathSharing.SHARED_WITH_MOTORISED_TRAFFIC_LOW_SPEED,
            PathSharing.SHARED_WITH_MOTORISED_TRAFFIC_LOW_SPEED,
        ],
    }
)


SHARED_WITH_MOTORISED_TRAFFIC_MEDIUM_SPEED_DF = pd.DataFrame(
    {
        'osm_tags': [
            {'highway': 'residential', 'cycleway:both': 'lane', 'maxspeed': '50'},
            {'highway': 'tertiary', 'cycleway:both': 'no', 'maxspeed': '50'},
            {'highway': 'residential', 'maxspeed:type': 'DE:urban'},
        ],
        'expected_category': [
            PathSharing.SHARED_WITH_MOTORISED_TRAFFIC_MEDIUM_SPEED,
            PathSharing.SHARED_WITH_MOTORISED_TRAFFIC_MEDIUM_SPEED,
            PathSharing.SHARED_WITH_MOTORISED_TRAFFIC_MEDIUM_SPEED,
        ],
    }
)
# 'way/152645928', highway=residential # Lagos testcase commented out for speed reasons


SHARED_WITH_MOTORISED_TRAFFIC_HIGH_SPEED_DF = pd.DataFrame(
    {
        'osm_tags': [
            {'highway': 'tertiary', 'maxspeed': '70', 'cycleway:both': 'no'},
            {'highway': 'unclassified', 'maxspeed:type': 'DE:rural'},
            {'highway': 'secondary', 'maxspeed': '70', 'cycleway:left': 'no', 'cycleway:right': 'separate'},
        ],
        'expected_category': [
            PathSharing.SHARED_WITH_MOTORISED_TRAFFIC_HIGH_SPEED,
            PathSharing.SHARED_WITH_MOTORISED_TRAFFIC_HIGH_SPEED,
            PathSharing.SHARED_WITH_MOTORISED_TRAFFIC_HIGH_SPEED,
        ],
    }
)


SHARED_WITH_MOTORISED_TRAFFIC_UNKNOWN_SPEED_DF = pd.DataFrame(
    {
        'osm_tags': [
            {'highway': 'primary_link', 'cycleway:both': 'no'},
            {'highway': 'tertiary'},
            {'highway': 'tertiary', 'cycleway': 'no'},
        ],
        'expected_category': [
            PathSharing.SHARED_WITH_MOTORISED_TRAFFIC_UNKNOWN_SPEED,
            PathSharing.SHARED_WITH_MOTORISED_TRAFFIC_UNKNOWN_SPEED,
            PathSharing.SHARED_WITH_MOTORISED_TRAFFIC_UNKNOWN_SPEED,
        ],
    }
)


REQUIRES_DISMOUNTING_DF = pd.DataFrame(
    {
        'osm_tags': [
            {'highway': 'steps', 'ramp:bicycle': 'yes'},
            {'highway': 'steps', 'ramp': 'yes', 'ramp:stroller': 'yes'},
            {'highway': 'track', 'ford': 'yes'},
        ],
        'expected_category': [
            PathSharing.REQUIRES_DISMOUNTING,
            PathSharing.REQUIRES_DISMOUNTING,
            PathSharing.REQUIRES_DISMOUNTING,
        ],
    }
)


PEDESTRIAN_EXCLUSIVE_DF = pd.DataFrame(
    {
        'osm_tags': [
            {'highway': 'footway', 'footway': 'sidewalk'},
            {'highway': 'footway', 'bicycle': 'no'},
            {'highway': 'pedestrian', 'bicycle': 'no'},
            {'railway': 'platform'},
            {'highway': 'platform'},
            {'highway': 'footway', 'bicycle': 'dismount'},
        ],
        'expected_category': [
            PathSharing.PEDESTRIAN_EXCLUSIVE,
            PathSharing.PEDESTRIAN_EXCLUSIVE,
            PathSharing.PEDESTRIAN_EXCLUSIVE,
            PathSharing.PEDESTRIAN_EXCLUSIVE,
            PathSharing.PEDESTRIAN_EXCLUSIVE,
            PathSharing.PEDESTRIAN_EXCLUSIVE,
        ],
    }
)


NO_ACCESS_DF = pd.DataFrame(
    {
        'osm_tags': [
            {'highway': 'trunk'},
            {'highway': 'secondary', 'bicycle': 'no'},
            {'highway': 'primary', 'motorroad': 'yes'},
            {'highway': 'service', 'access': 'no', 'bus': 'yes'},
            {'highway': 'service', 'access': 'private'},
            {'highway': 'footway', 'access': 'private'},
            {'highway': 'steps', 'access': 'private'},
        ],
        'expected_category': [
            PathSharing.NO_ACCESS,
            PathSharing.NO_ACCESS,
            PathSharing.NO_ACCESS,
            PathSharing.NO_ACCESS,
            PathSharing.NO_ACCESS,
            PathSharing.NO_ACCESS,
            PathSharing.NO_ACCESS,
        ],
    }
)


FILTER_VALIDATION_OBJECTS = [
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


@pytest.mark.parametrize(
    argnames='category',
    argvalues=FILTER_VALIDATION_OBJECTS,
    ids=[
        filter_validation_object.loc[0, 'expected_category'] for filter_validation_object in FILTER_VALIDATION_OBJECTS
    ],  # type: ignore
)
def test_construct_filter_validate(category):
    category['received_category'] = category.apply(apply_path_sharing_filters, axis=1)

    pd.testing.assert_series_equal(
        category['received_category'],
        category['expected_category'],
        check_names=False,
    )
