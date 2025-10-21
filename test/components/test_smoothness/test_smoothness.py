import pandas as pd
import pandas.testing as test

from bikeability.components.smoothness.smoothness import SmoothnessCategory, apply_path_smoothness_filters

VALIDATION_PATHS = pd.DataFrame(
    data={
        '@other_tags': [
            {'smoothness': 'excellent'},
            {'smoothness': 'good'},
            {'smoothness': 'intermediate'},
            {'smoothness': 'bad'},
            {'smoothness': 'impassable'},
            {'smoothness': 'very_horrible'},
            {'smoothness': 'horrible'},
            {'smoothness': 'very_bad'},
            dict(),
        ],
        'expected_smoothness': [
            SmoothnessCategory.EXCELLENT,
            SmoothnessCategory.GOOD,
            SmoothnessCategory.INTERMEDIATE,
            SmoothnessCategory.BAD,
            SmoothnessCategory.TOO_BUMPY_TO_RIDE,
            SmoothnessCategory.TOO_BUMPY_TO_RIDE,
            SmoothnessCategory.TOO_BUMPY_TO_RIDE,
            SmoothnessCategory.TOO_BUMPY_TO_RIDE,
            SmoothnessCategory.UNKNOWN,
        ],
    }
)


def test_construct_smoothness_validate():
    result = VALIDATION_PATHS.apply(apply_path_smoothness_filters, axis=1)
    test.assert_series_equal(result, VALIDATION_PATHS['expected_smoothness'], check_index=False, check_names=False)
