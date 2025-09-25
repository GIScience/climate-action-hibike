import pytest

import bikeability.indicators.path_category_filters as filters
from bikeability.indicators.path_category_filters import SpeedLimitCategory

speed_tags = {
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


@pytest.mark.parametrize('tag', speed_tags)
def test_maxspeed_parsing(tag: str):
    tags = {'maxspeed': tag}
    result = filters.parse_maxspeed_tag(tags)
    assert speed_tags[tag] == result


@pytest.mark.parametrize('tag', speed_tags)
def test_maxspeed_forward(tag: str):
    tags = {'maxspeed:forward': tag}
    result = filters.parse_maxspeed_tag(tags)
    assert speed_tags[tag] == result
