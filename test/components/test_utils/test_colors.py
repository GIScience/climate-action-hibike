from pydantic_extra_types import Color

from bikeability.components.utils.colors import ColorCategories


class TestCategories(ColorCategories):
    VALUE = 'value'
    UNKNOWN = 'unknown'


def test_get_qualitative_colors():
    received = TestCategories.get_qualitative_colors(colormap='coolwarm')

    assert received['unknown'] == Color('#808080')
