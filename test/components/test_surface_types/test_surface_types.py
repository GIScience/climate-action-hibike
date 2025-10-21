import pytest

from bikeability.components.surface_types.surface_types import SurfaceType, get_surface_types


@pytest.mark.parametrize(
    'input_surface,expected_output',
    [
        (None, SurfaceType.UNKNOWN),
        ('asphalt', SurfaceType.ASPHALT),
        ('concrete', SurfaceType.CONCRETE),
        ('concrete:lanes', SurfaceType.CONCRETE),
        ('paving_stones', SurfaceType.PAVING_STONES),
        ('paving_stones:lanes', SurfaceType.PAVING_STONES),
        ('cobblestones', SurfaceType.COBBLESTONE),
        ('paved', SurfaceType.PAVED),
        ('chipseal', SurfaceType.OTHER_PAVED),
        ('compacted', SurfaceType.COMPACTED),
        ('fine_gravel', SurfaceType.FINE_GRAVEL),
        ('gravel', SurfaceType.GRAVEL),
        ('unpaved', SurfaceType.UNPAVED),
        ('shells', SurfaceType.OTHER_UNPAVED),
        ('unknown', SurfaceType.UNKNOWN),
    ],
)
def test_get_surface_types(test_line, input_surface, expected_output):
    test_line.loc[1, '@other_tags'].update({'surface': input_surface})
    computed_line = get_surface_types(test_line).reset_index(drop=True)

    assert computed_line.loc[0, 'surface_type'] == expected_output
