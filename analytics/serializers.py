from typing import Dict, List, Literal, Optional, Type

from django.db.models import Model
from django.utils.translation import gettext_lazy as _
from pydantic import BaseModel, root_validator, validator

from analytics.models import DimensionEnum, IntervalEnum
from receipts.models import Receipt

CONDITION_OPTIONS: Type[str] = Literal['lte', 'gte', 'lt', 'gt']


class DimensionBaseModel(BaseModel):
    name: str
    filtering: Optional[dict]

    @validator('name')
    @classmethod
    def name_validator(cls, v) -> Type[Model]:
        """
        Getting from Enum respective Model of dimension
        """
        try:
            return DimensionEnum.get_model_by_name(v)
        except KeyError:
            raise ValueError(_('Введіть коректне значення.'))

    @validator('filtering')
    @classmethod
    def filtering_includes_option(cls, v: dict) -> dict:
        """
        Checks whether 'filtering' contains 'option' key.
        """
        if not v:
            return v

        include_option: dict = v.get('option', None)
        if not include_option:
            raise ValueError(_("'fitering' повинне містити 'option'."))

        return v

    @root_validator
    @classmethod
    def validating_filtering_fields(cls, v: dict) -> dict:
        """
        Iterates through fields of 'filtering' key and validates it.
        """
        filtering: dict = v.pop('filtering', None)
        if not filtering:
            return v

        option = filtering.pop('option', None)
        model = v.get('name')
        admissible_fields = DimensionEnum.get_fields_by_model(model)
        v['filtering'] = {}

        # checking whether every key of filtering dict is in admissible fields of model
        # and adding to each key option for further querying
        for key, item in filtering.items():
            if key not in admissible_fields:
                raise ValueError(_(f"{key} не є припустимим полем."))
            v['filtering'][f'{key}__{option}'] = item

        return v


class IntervalBaseModel(BaseModel):
    name: str

    @root_validator
    @classmethod
    def assign_fields_for_search(cls, v) -> dict:
        name = v.get('name')

        v['annotating'] = {'interval': IntervalEnum.get_trunc_by_name(name)}
        v['name'] = Receipt
        return v


class MetricOptionBaseModel(BaseModel):
    option: Literal[CONDITION_OPTIONS]
    value: int


class MetricsBaseModel(BaseModel):
    metrics: List[Dict[str: str, str: dict]]

    @validator('metrics')
    @classmethod
    def check_name_existence(cls, v: List[Dict[str: str, str: dict]]) -> List[Dict[str: str, str: dict]]:
        for metric in v:
            if not metric.get('name'):
                raise ValueError(_('У кожному "metric" повинен бути "name".'))

        return v

    @validator('metrics', each_item=True)
    @classmethod
    def validate_options(cls, v: List[Dict[str: str, str: dict]]) -> List[Dict[str: str, str: dict]]:
        """
        Validates whether each option is applicable in queries
        """
        for metric in v:
            option = metric.get('option', None)
            if option:
                MetricOptionBaseModel(**option)

        return v

    # @root_validator
    # @classmethod
    # def define_pre_post_conditions(cls, v: List[Dict[str: str, str: dict]]) -> List[Dict[str: str, str: dict]]:
    #     pre_filtering = []
    #     for metric in v:
    #


class DateRangeBaseModel(BaseModel):
    date__lte: Optional[str]
    date__gte: Optional[str]

    previous: Optional[bool] = False

    @root_validator
    @classmethod
    def validate_date(cls, values: dict):
        if all([value is None for value in values.values()]):
            raise ValueError(_('Принаймані один із параметрів повинен бути присутнім.'))
        return values
