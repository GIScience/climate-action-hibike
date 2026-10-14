from enum import Enum
from typing import Self

import matplotlib
import pandas as pd
from matplotlib.colors import Colormap, Normalize, to_hex
from pydantic_extra_types.color import Color


class ColorCategories(Enum):
    """
    This is a base class for categorical data that we want to assign colour values for.
    You should use it in place of an Enum where you want to assign categorical colurs.
    Override methods as necessary for tweaks to visible colours or colour mapping.
    """

    pass

    @classmethod
    def get_visible(cls) -> list[Self]:
        """
        Returns a list of visible categories from the Enum.
        Override this to drop certaint categories from your colour maps.
        """
        return list(cls)

    @classmethod
    def get_qualitative_colors(cls, colormap: str | Colormap) -> dict[str, Color]:
        """
        Returns a legend dictionary for your categories based on even spacing.
        :param: `colormap` provides the colour map either as a matplotlib `Colormap` or by its name as a str.
        :return: dict based on enum value and `pydantic_extra_types.Color`
        """
        norm = Normalize(0, 1)
        if isinstance(colormap, str):
            colormap: Colormap = matplotlib.cm.ScalarMappable(norm=norm, cmap=colormap).get_cmap()

        category_norm = {
            name.value: Color(to_hex(colormap(idx / (len(cls.get_visible()) - 1))))
            for idx, name in enumerate(cls.get_visible())
        }

        category_norm.update({'unknown': Color('#808080')})

        return category_norm


def get_continuous_colors(category: pd.Series, cmap_name: str, vmin: float = 0, vmax: float = 1) -> list[Color]:
    norm = matplotlib.colors.Normalize(vmin=vmin, vmax=vmax)
    cmap: Colormap = matplotlib.colormaps.get(cmap_name)
    cmap.with_extremes(bad='#808080')
    mapped_colors = [Color(matplotlib.colors.to_hex(col)) for col in cmap(norm(category))]
    return mapped_colors
