from typing import Literal, Optional, Type

from django.db.models import Model
from django.utils.translation import gettext_lazy as _
from pydantic import BaseModel, Field, root_validator, validator
from pydantic.datetime_parse import date

from analytics.constants import (CONDITION_OPTIONS, DIFF, METRIC_NAME_OPTIONS,
                                 PERCENT, STRING_CONDITIONS)
from analytics.models import DimensionEnum, IntervalEnum


class BaseFilteringBaseModel(BaseModel):
    """
    Validates each field in options in dimension object
    """
    field: str
    value: str
    option: Literal[STRING_CONDITIONS]


class FilteringBaseModel(BaseModel):
    """
    Parses options of dimension objects to
    relevant for querying structure
    """
    model: type[Model]
    field: str
    value: str
    option: Literal[STRING_CONDITIONS]

    @root_validator
    @classmethod
    def check_name_consistency(cls, values: dict) -> dict:
        field_name = values.get('field', None)
        admissible_fields = DimensionEnum.get_fields_by_model(model=values.get('model', None))

        if field_name not in admissible_fields:
            raise ValueError(_('"field" повинне містити поле із моделі.'))

        return values

    @root_validator
    @classmethod
    def adapt_filtering_fields(cls, values: dict) -> dict:
        field: str = values.get('field')
        value: str = values.get('value')
        option: str = values.get('option')
        return {
            'filtering': {
                f'{field}__{option}': value
            }
        }


class DimensionBaseModel(BaseModel):
    name: str
    filtering: Optional[list[BaseFilteringBaseModel]] = []

    @validator('name')
    @classmethod
    def validate_name(cls, value: str) -> str:
        if value not in DimensionEnum.get_all_names():
            raise ValueError(_('Введіть коректне значення.'))
        return value

    @root_validator
    @classmethod
    def validate_filtering(cls, values: dict) -> dict:
        filtering_conditions: dict[str, str] = {}
        model: Type[Model] = values.get('name', None)
        if values.get('filtering') is not None:
            for dct in values.get('filtering', None):
                filtering_conditions.update(FilteringBaseModel(model=model,
                                                               **dct.dict()).dict()['filtering'])
        values['filtering'] = filtering_conditions
        return values

    @validator('name')
    @classmethod
    def set_model(cls, value: str) -> Type[Model]:
        return DimensionEnum.get_model_by_name(value)

    @root_validator
    @classmethod
    def assign_auxiliary_fields(cls, values: dict) -> dict:
        """
        Checks whether chosen model is auxiliary. If yes, adds
        auxiliary name for correct further filtering
        """
        model: Type[Model] = values.get('name')
        values['name'] = model.__name__
        values['pre_values'] = list(DimensionEnum.get_fields_by_model(model))

        return values


class DimensionQualifierBaseModel(BaseModel):
    name: str

    @validator('name')
    @classmethod
    def validate_name_base_model(cls, v: str) -> Type[BaseModel]:
        if v in list(IntervalEnum.get_applicable_fields()):
            return IntervalBaseModel
        elif v in list(DimensionEnum.__members__):
            return DimensionBaseModel

        raise ValueError(_('Оберіть правильний "name".'))


class IntervalBaseModel(BaseModel):
    name: str

    @root_validator
    @classmethod
    def assign_fields_for_search(cls, v) -> dict:
        name = v.get('name')

        v['pre_values'] = [name]
        v['pre_annotation'] = {name: IntervalEnum.get_trunc_by_name(name)}
        return v


class MetricOptionBaseModel(BaseModel):
    option: Literal[CONDITION_OPTIONS]
    value: int


class MetricBaseModel(BaseModel):
    name: Literal[METRIC_NAME_OPTIONS]
    options: Optional[list[MetricOptionBaseModel]] = []

    @validator('options', pre=True)
    @classmethod
    def main(cls, value: list) -> list:
        print(f'value in values is : {value}')
        return value

    @root_validator
    @classmethod
    def define_pre_post_metric(cls, values: dict) -> dict[str, dict]:
        """
        Defines whether conditions of metrics must be executed in DataFrame
        filtering or in query. Form dictionaries with relevant data
        """
        name: str = values.get('name')
        post_filtering: dict = {}
        dataframe_filtering: dict = {}

        options: list[dict | None] = []

        for option in values.get('options', []):
            option_dict: dict = option.dict()
            options.append(option_dict)

        if DIFF in name or PERCENT in name:
            dataframe_filtering['name']: str = name
            if options:
                dataframe_filtering['options']: list[dict | None] = options
        else:
            post_filtering['name']: str = name
            if options:
                post_filtering['options']: list[dict | None] = options

        return {'dataframe_filtering': dataframe_filtering, 'post_filtering': post_filtering}


class MetricsOverallBaseModel(BaseModel):
    metrics: list[MetricBaseModel]

    @root_validator
    @classmethod
    def define_post_dataframe_metrics(cls, values: dict) -> dict:
        post_filtering = []
        dataframe_filtering = []
        for metric in values.get('metrics', []):
            metric_dict = metric.dict()

            if metric_dict.get('post_filtering', None):
                post_filtering.append(metric_dict['post_filtering'])

            if metric_dict.get('dataframe_filtering', None):
                dataframe_filtering.append(metric_dict['dataframe_filtering'])

        return {
            'post_filtering': post_filtering,
            'dataframe_filtering': dataframe_filtering,
            'required_date_ranges': bool(dataframe_filtering)
        }

    @root_validator
    @classmethod
    def check_post_filtering_completeness(cls, values: dict) -> dict:
        """
        Checks whether fields, that will be counted in DataFrames are present in
        'post_filtering', if not - it adds them
        """
        dataframe_metrics: list[str] = [dct['name'] for dct in values.get('dataframe_filtering', [])]
        post_filtering: list[str] = [dct['name'] for dct in values.get('post_filtering', [])]

        for key in dataframe_metrics:
            annotation_key = key.replace(DIFF, '').replace(PERCENT, '')
            if annotation_key not in post_filtering:
                values['post_filtering'].append({'name': annotation_key})
        return values


class DateRangeBaseModel(BaseModel):
    date_range: list[date, date] = Field(max_items=2, min_items=2)
    prev_date_range: Optional[list[date, date]] = Field(max_items=2, min_items=2)

    previous: bool = False

    @validator('date_range', 'prev_date_range')
    @classmethod
    def check_date_difference(cls, values: list[str, str]) -> list[str, str]:
        if values[0] > values[1]:
            raise ValueError(_('Початкова дата повинна бути меншою за кінцеву.'))

        return values

    @root_validator
    @classmethod
    def check_prev_date_range_consistency(cls, values: dict) -> dict:
        if values.get('previous', None) and not values.get('prev_date_range', None):
            raise ValueError(_('Укажіть попередній проміжок.'))

        return values

    @root_validator
    @classmethod
    def parse_dates_to_filtering_conditions(cls, values: dict) -> dict:
        answer = {'previous': values.get('previous', False)}

        if values.get('previous', None):
            answer['previous'] = True

            answer['previous_pre_filtering'] = {}
            date_range: list = values.get('prev_date_range', None)

            answer['previous_pre_filtering']['date__date__gte'] = date_range[0].strftime('%Y-%m-%d')
            answer['previous_pre_filtering']['date__date__lte'] = date_range[1].strftime('%Y-%m-%d')

        answer['pre_filtering'] = {}

        date_range: list = values.get('date_range')
        answer['pre_filtering']['date__date__gte'] = date_range[0].strftime('%Y-%m-%d')
        answer['pre_filtering']['date__date__lte'] = date_range[1].strftime('%Y-%m-%d')

        return answer


class RequestDimensionParser(BaseModel):
    dimensions: list[DimensionBaseModel]
