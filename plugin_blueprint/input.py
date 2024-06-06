import datetime
import uuid
from enum import Enum
from typing import List, Optional

import geojson_pydantic
import shapely
from pydantic import BaseModel, Field, condate, field_validator


class Option(Enum):
    # This enumeration predefines options for the user to choose from (see below).
    # One should favour using strings for enum values.

    OPT1 = 'Option 1'
    OPT2 = 'Option 2'


class AoiProperties(BaseModel):
    name: str = Field(
        title='Name',
        description='The name of the area of interest i.e. a human readable description.',
        examples=['Heidelberg'],
    )
    id: str = Field(
        title='ID',
        description='A unique identifier of the area of interest.',
        examples=[uuid.uuid4()],
    )


class ComputeInput(BaseModel):
    # This class defines all the input parameters of your plugin.
    # It uses pydantic to announce the parameters and validate them from the user realm (i.e. the front-end).
    # These parameters will later be available in the computation method.
    # Make sure you document them well using pydantic Fields.
    # The title, description and example parameters as well as marking them as optional (if applicable) are required!
    # If you mark a field as optional, be sure to set the default value as well.
    # Additional constraints can be set.
    # Examples for the different data types are given below.
    # In case you need custom data types (e.g. a list of numbers), please contact the CA team.

    bool_blueprint: bool = Field(
        title='Boolean Input',
        description='A required boolean parameter.',
        examples=[True],
    )

    int_blueprint: Optional[int] = Field(
        title='Integer Input',
        description='An optional integer parameter.',
        examples=[3],
        default=3,
        gt=0,
        lt=100,
    )

    float_blueprint: Optional[float] = Field(
        title='Float Input',
        description='An optional floating point parameter.',
        examples=[2.1],
        default=2.1,
        ge=0.5,
        le=4,
    )

    string_blueprint: Optional[str] = Field(
        title='String Input',
        description='An optional string parameter.',
        examples=['John Doe'],
        default='John Doe',
    )

    # In case you need a date-range, we suggest you simply use two date fields, one for the start, one for the end date
    date_blueprint: Optional[condate(ge=datetime.date(2005, 1, 1), le=datetime.date.today())] = Field(
        title='Date Input',
        description='An optional date parameter.',
        examples=[datetime.date(2020, 1, 1)],
        default=datetime.date(2020, 1, 1),
    )

    # Here are two examples for custom input types
    select_blueprint: Optional[Option] = Field(
        title='Selection Input',
        description='An optional selection parameter. The user can choose one of the available options.',
        examples=[Option.OPT2],
        default=Option.OPT2,
    )

    select_multi_blueprint: Optional[List[Option]] = Field(
        title='Multi-Selection Input',
        description='An optional selection parameter. The user can choose multiple of the available options.',
        examples=[[Option.OPT2]],
        default=[Option.OPT2],
    )

    # Last is the geographical area of interest.
    # This parameter is mandatory for all plugins.
    # Unfortunately it is a bit cumbersome.
    # We use geojson as input type and MultiPolygons as geometry type.
    # All plugins should be able to work on arbitrary polygonal areas.
    # Yet, you don't have to bother about the input type here.
    # Simply use the convenience methods .get_aoi_geom below that will provide a shapely geometry.
    # See the methods further down for an example.
    # IMPORTANT: Do not change the name of the variable, it adheres to a contract with the front-end!
    # You may though adapt the title or description to your liking.
    aoi: geojson_pydantic.Feature[geojson_pydantic.MultiPolygon, AoiProperties] = Field(
        title='Area of Interest',
        description="The geographic area of interest for this plugin's indicator computation.",
        validate_default=True,
        examples=[
            {
                'type': 'Feature',
                'properties': {'name': 'Heidelberg', 'id': 'Q12345'},
                'geometry': {
                    'type': 'MultiPolygon',
                    'coordinates': [
                        [
                            [
                                [12.3, 48.22],
                                [12.3, 48.34],
                                [12.48, 48.34],
                                [12.48, 48.22],
                                [12.3, 48.22],
                            ]
                        ]
                    ],
                },
            }
        ],
    )

    @field_validator('aoi')
    def assert_aoi_properties_not_null(cls, aoi: geojson_pydantic.Feature) -> geojson_pydantic.Feature:
        assert aoi.properties, 'AOI properties are required.'
        return aoi

    def get_aoi_geom(self) -> shapely.MultiPolygon:
        """Convert the input geojson geometry to a shapely geometry.

        :return: A shapely.MultiPolygon representing the area of interest defined by the user.
        """
        return shapely.geometry.shape(self.aoi.geometry)

    def get_aoi_properties(self) -> AoiProperties:
        """Return the properties of the aoi.

        :return:
        """
        return self.aoi.properties
