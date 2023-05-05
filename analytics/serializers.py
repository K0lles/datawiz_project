from typing import Optional

from django.utils.translation import gettext_lazy as _
from pydantic import BaseModel, root_validator, validator

from analytics.models import DimensionEnum


class DimensionBaseModel(BaseModel):
    name: str
    filtering: Optional[dict[str, list[str]]]

    @root_validator(pre=True)
    def redefine_fields_keys(cls, values: dict) -> dict:
        """
        Parses from request's 'dimensions' and return respective model. Gathers filtering fields
        by adding to the name of fields '__in' and returning the dict with keys 'name' and 'filtering'
        :param values:
        :return:
        """
        print(values)
        try:
            # getting from Enum class record if it exists
            enum_element = DimensionEnum[values.get('name')]
            model = enum_element.value[1]

            values['filtering'] = {}

            # deleting from values key with name if order to further defining of filtering keys
            values.pop('name')
            for key, item in values.items():
                if key in enum_element.value[2]:
                    values['filtering'][f'{key}__in'] = values.get(key)

            # setting proper model to key 'name'
            values['name'] = model
            return {'name': values.get('model'), 'filtering': values.get('filtering')}
        except KeyError:
            raise ValueError(_('Введіть коректне значення для "name".'))

    @validator('name')
    def name_validator(cls, v):
        """
        Getting from Enum respective Model of dimension
        """
        try:
            return DimensionEnum[v].value[1]
        except KeyError:
            raise ValueError(_('Введіть коректне значення.'))

    # @validator('id', each_item=True)
    # def id_validator(cls, v: str):
    #     """
    #     Checking, whether list of id contains only numeric strings
    #     """
    #     assert v.isnumeric(), _('\"id\" повинне бути номером.')
    #     return v


class DateRangeBaseModel(BaseModel):
    date__lte: Optional[str]
    date__gte: Optional[str]

    previous: Optional[bool] = False

    @root_validator
    def validate_date(cls, values: dict):
        if all([value is None for value in values.values()]):
            raise ValueError(_('Принаймані один із параметрів повинен бути присутнім.'))
        return values
