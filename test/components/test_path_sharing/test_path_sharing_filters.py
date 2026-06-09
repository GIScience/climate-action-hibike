import pytest

import bikeability.components.path_sharing.path_sharing_filters as filters
from bikeability.components.path_sharing.path_sharing_filters import SpeedLimitCategory

SPEED_TAGS = {
    'walk': SpeedLimitCategory.WALKING_SPEED,
    '15': SpeedLimitCategory.WALKING_SPEED,
    '7 mph': SpeedLimitCategory.WALKING_SPEED,
    '20': SpeedLimitCategory.LOW,
    '15 mph': SpeedLimitCategory.LOW,
    '30': SpeedLimitCategory.LOW,
    '20 mph': SpeedLimitCategory.MEDIUM,
    '40': SpeedLimitCategory.MEDIUM,
    '50 mph': SpeedLimitCategory.HIGH,
    '80': SpeedLimitCategory.HIGH,
    'none': SpeedLimitCategory.HIGH,
    'abc mph': SpeedLimitCategory.UNKNOWN,
    'abcmph': SpeedLimitCategory.UNKNOWN,
    'DE:rural': SpeedLimitCategory.HIGH,
    'AT:urban': SpeedLimitCategory.MEDIUM,
}


@pytest.mark.parametrize('tag', SPEED_TAGS)
def test_maxspeed_parsing(tag: str):
    tags = {'maxspeed': tag}
    result = filters.parse_maxspeed_tag(tags)
    assert SPEED_TAGS[tag] == result


@pytest.mark.parametrize('tag', SPEED_TAGS)
def test_maxspeed_forward(tag: str):
    tags = {'maxspeed:forward': tag}
    result = filters.parse_maxspeed_tag(tags)
    assert SPEED_TAGS[tag] == result
