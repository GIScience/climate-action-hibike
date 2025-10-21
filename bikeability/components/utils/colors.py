from typing import Union

import matplotlib
import pandas as pd
from matplotlib.colors import Normalize, to_hex
from pydantic_extra_types.color import Color

from bikeability.components.dooring_risk.dooring_risk import DooringRiskCategory
from bikeability.components.path_categories.path_categories import PathCategory
from bikeability.components.smoothness.smoothness import SmoothnessCategory
from bikeability.components.surface_types.surface_types import SurfaceType


def get_qualitative_color(
    category: Union[PathCategory, SmoothnessCategory, SurfaceType, DooringRiskCategory], cmap_name: str
) -> Color:
    norm = Normalize(0, 1)
    cmap = matplotlib.cm.ScalarMappable(norm=norm, cmap=cmap_name).get_cmap()
    cmap.set_under('#808080')

    category_norm = {name: idx / (len(category.get_visible()) - 1) for idx, name in enumerate(category.get_visible())}

    if category.value == 'unknown':
        return Color(to_hex(cmap(-9999)))
    else:
        return Color(to_hex(cmap(category_norm[category])))


def get_continuous_colors(category: pd.Series, cmap_name: str) -> list[Color]:
    norm = matplotlib.colors.Normalize(vmin=0, vmax=1)
    cmap = matplotlib.colormaps.get(cmap_name)
    cmap.set_bad('#808080')
    mapped_colors = [Color(matplotlib.colors.to_hex(col)) for col in cmap(norm(category))]
    return mapped_colors
