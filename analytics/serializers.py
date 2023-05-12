from datetime import datetime
from typing import Any, List, Literal, Optional, Type

from django.db.models import Model
from django.utils.translation import gettext_lazy as _
from pydantic import BaseModel, root_validator, validator

from analytics.functions import validate_date_string
from analytics.models import DimensionEnum, IntervalEnum, MetricNameEnum
from receipts.models import CartItem

CONDITION_OPTIONS: Type[str] = Literal['lte', 'gte', 'lt', 'gt', 'exact']


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

        v['pre_values'] = []

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

        v['pre_annotating'] = {}
        return v


class IntervalBaseModel(BaseModel):
    name: str

    @root_validator
    @classmethod
    def assign_fields_for_search(cls, v) -> dict:
        name = v.get('name')

        v['pre_values'] = [name]
        v['pre_annotating'] = {'interval': IntervalEnum.get_trunc_by_name(name)}
        v['name'] = CartItem
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
            if metric_name not in MetricNameEnum.get_values():
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
    def define_pre_post_metrics(cls, values: dict) -> dict[str, list[Any] | bool]:
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

        return {'post_filtering': post_filtering, 'dataframe_filtering': dataframe_filtering,
                'required_date_ranges': True if dataframe_filtering else False}

    @root_validator
    @classmethod
    def adapt_post_filtering(cls, values: dict) -> dict[str, list[Any] | bool]:
        """
        If 'dataframe_filtering' is present, checks whether basic field by
        which difference will be defined presents
        """
        if values.get('required_date_ranges', None):
            v = values.get('dataframe_filtering', None)

            # getting names of post_filtering and dataframe_filtering which presents in lists currently
            post_filtering_names: list[str] = [d['name'] for d in values.get('post_filtering')]
            dataframe_filtering_names: list[str] = [d['name'] for d in v]

            # checking whether difference base field presents in post_filtering lists, if not we add it
            for df_name in dataframe_filtering_names:
                post_name = df_name.replace('_diff', '').replace('_percent', '')
                if post_name not in post_filtering_names:
                    values['post_filtering'].append({'name': post_name})

        return values


class DateRangeBaseModel(BaseModel):
    date_range: list[str, str]  # change to date
    prev_date_range: Optional[list[str, str]]

    previous: bool = False

    @validator('date_range')
    @classmethod
    def validate_date_range(cls, v: list[str, str]) -> list[str, str]:
        if not validate_date_string(v[0]) or not validate_date_string(v[1]):
            raise ValueError(_('Введіть коректні дати.'))
        return v

    @root_validator
    @classmethod
    def validate_prev_existence(cls, v: dict) -> dict:
        if v.get('previous', None):
            if not v.get('prev_date_range', None):
                raise ValueError(_('Ви повинні указати попередні дати для вибірки.'))
            if not validate_date_string(v.get('prev_date_range')[0]) \
                    or not validate_date_string(v.get('prev_date_range')[1]):
                raise ValueError(_('Введіть коректні дати.'))
        return v

    @validator('date_range')
    @classmethod
    def check_date_difference(cls, v: list[str, str]) -> list[str, str]:
        lower_date = datetime.strptime(v[0], '%Y-%m-%d')
        higher_date = datetime.strptime(v[1], '%Y-%m-%d')

        if lower_date >= higher_date:
            raise ValueError(_('Дати повинні різнитися та початкова дата повинна бути меншою за кінцеву.'))

        return v

    @validator('prev_date_range')
    @classmethod
    def check_prev_date_difference(cls, v: list[str, str]) -> list[str, str]:
        lower_date = datetime.strptime(v[0], '%Y-%m-%d')
        higher_date = datetime.strptime(v[1], '%Y-%m-%d')

        if lower_date >= higher_date:
            raise ValueError(_('Дати повинні різнитися та початкова дата повинна бути меншою за кінцеву.'))

        return v

    @root_validator
    @classmethod
    def parse_dates_to_filtering_conditions(cls, v: dict) -> dict:
        answer = {'previous': v.get('previous', False)}

        if v.get('previous', None):
            answer['previous'] = True

            answer['previous_pre_filtering'] = {}
            date_range: list = v.get('prev_date_range', None)

            answer['previous_pre_filtering']['date__gte'] = date_range[0]
            answer['previous_pre_filtering']['date__lte'] = date_range[1]

        answer['pre_filtering'] = {}

        date_range: list = v.get('date_range')
        answer['pre_filtering']['date__gte'] = date_range[0]
        answer['pre_filtering']['date__lte'] = date_range[1]

        return answer
