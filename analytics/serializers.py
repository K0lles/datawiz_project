from typing import Dict, List, Literal, Optional, Type

from django.db.models import Model
from django.utils.translation import gettext_lazy as _
from pydantic import BaseModel, root_validator, validator

from analytics.functions import validate_date_string
from analytics.models import DimensionEnum, IntervalEnum
from receipts.models import Receipt

CONDITION_OPTIONS: Type[str] = Literal['lte', 'gte', 'lt', 'gt', 'exact']

METRIC_OPTIONS: list = ['turnover', 'turnover_diff', 'turnover_diff_percent',
                        'average_price', 'average_price_diff', 'average_price_diff_percent',
                        'income', 'income_diff', 'income__diff_percent',
                        'sold_product_amount', 'sold_product_amount_diff', 'sold_product_amount_diff_percent',
                        'receipt_amount', 'receipt_amount_diff', 'receipt_amount_diff_percent']


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

    @root_validator
    @classmethod
    def assign_auxiliary_fields(cls, v: dict) -> dict:
        """
        Checks whether chosen model is auxiliary. If yes, adds
        auxiliary name for correct further filtering
        """
        model: Type[Model] = v.get('name')
        filtering_conditions: dict = v.get('filtering', None)

        # if is not auxiliary or have no filters returns dict
        if not getattr(model, 'is_auxiliary', None) or not filtering_conditions:
            return v

        # creates new dict and modifies all key names
        new_filter_conditions: dict = {}
        for key, value in filtering_conditions.items():
            new_filter_conditions[f'{getattr(model, "get_auxiliary_name")}{key}'] = value

        v['filtering'] = new_filter_conditions
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
    metrics: List[dict]

    @validator('metrics')
    @classmethod
    def check_name_existence(cls, v: list[dict]) -> list[dict]:
        """
        Checks whether each dict of metrics contains 'name' field
        """
        for metric in v:
            metric_name: str = metric.get('name', None)
            if not metric_name:
                raise ValueError(_('У кожному "metric" повинен бути "name".'))

            # checks whether metric_name is valid
            if metric_name not in METRIC_OPTIONS:
                raise ValueError(_('Введіть правильний варіант "name".'))

        return v

    @validator('metrics')
    @classmethod
    def validate_options(cls, v: list[dict]) -> list[dict]:
        """
        Validates whether each option is applicable in queries
        """
        for metric in v:
            if metric.get('options', None):
                for condition in metric.get('options'):
                    if condition:
                        MetricOptionBaseModel(**condition)
        return v

    @validator('metrics')
    @classmethod
    def clear_metrics(cls, v: list[dict]) -> list[dict]:
        """
        Clean dictionaries except of 'name' and 'options' keys
        """
        for metric in v:
            for key, value in metric.items():
                if key not in ['name', 'options']:
                    raise ValueError(_(f'Параметр "{key}" не передбачений.'))

        return v

    @root_validator
    @classmethod
    def define_pre_post_metrics(cls, values: dict) -> Dict[str, list]:
        """
        Sorts metrics by sequence of their execution. Metrics, that must be executed in
        dataframes will be populated into 'dataframe_filtering', others - in
        'post_filtering' that will be executed after annotations
        """
        v = values.get('metrics')
        post_filtering = []
        dataframe_filtering = []
        for metric in v:
            metric_name: str = metric.get('name')
            if '_diff' in metric_name or '_diff_percent' in metric_name:
                dataframe_filtering.append(metric)
            else:
                post_filtering.append(metric)

        return {'post_filtering': post_filtering, 'dataframe_filtering': dataframe_filtering}


class DateRangeBaseModel(BaseModel):
    date__lte: Optional[str]
    date__gte: Optional[str]

    previous: Optional[bool] = False

    @root_validator
    @classmethod
    def validate_date(cls, values: dict):
        if all([value is None for value in values.values()]):
            raise ValueError(_('Принаймані один із параметрів повинен бути присутнім.'))

        if not validate_date_string(values.get('date__lte')) or validate_date_string(values.get('date__gte')):
            raise ValueError(_('Укажіть правильно дату.'))

        return values
