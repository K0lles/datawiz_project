import datetime
import hashlib
import json
import operator
from datetime import timedelta
from enum import Enum
from typing import Type

import pandas as pd
from django.core.cache import cache
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import (OpenApiParameter, extend_schema,
                                   inline_serializer)
from pydantic import BaseModel
from rest_framework.fields import CharField
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response

from analytics import dimensions
from analytics.metrics import (CartItemMetric,
                               FullCategoryProductMaterializedViewMetric,
                               FullShopGroupShopMaterializedViewMetric,
                               ModelMetric, ProducerMetric, ProductMetric,
                               ShopMetric, SupplierMetric, TerminalMetric)
from analytics.models import IntervalEnum
from analytics.serializers import (DateRangeBaseModel,
                                   DimensionQualifierBaseModel,
                                   MetricsBaseModel)
from datawiz_project.paginators import CustomNumberPaginator
from receipts.models import CartItem


class MetricModelsEnum(Enum):
    fullshopgroupshopmaterializedview = ('FullShopGroupShopMaterializedView', FullShopGroupShopMaterializedViewMetric)
    shop = ('Shop', ShopMetric)
    terminal = ('Terminal', TerminalMetric)
    fullcategoryproductmaterializedview = ('FullCategoryProductMaterializedView',
                                           FullCategoryProductMaterializedViewMetric)
    product = ('Product', ProductMetric)
    supplier = ('Supplier', SupplierMetric)
    producer = ('Producer', ProducerMetric)
    cartitem = ('CartItem', CartItemMetric)

    @classmethod
    def get_metric_model_by_name(cls, name: str) -> Type[ModelMetric]:
        for item in cls:
            if item.value[0] == name:
                return item.value[1]
        raise ValueError(_("Введіть коректне значення 'name'."))


class AnalyticsRetrieveAPIView(CreateAPIView):
    serializer_class = None
    pagination_class = CustomNumberPaginator
    model = CartItem
    metric_field_assign_model = 'FieldAssignment'
    interval_base_models = ['IntervalBaseModel']
    comparison_functions = {
        'exact': operator.eq,
        'exclude': operator.ne,
        'lt': operator.lt,
        'lte': operator.le,
        'gt': operator.gt,
        'gte': operator.ge,
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.has_intervals = False

        self.dimension_data: dict = {}
        self.metrics_data: list = []
        self.date_ranges: dict = {}

        self.model_name = CartItem
        self.model_dimension = None
        self.model_metric = None

        self.select_related: list = []
        self.prefetch_related: list = []

        self.pre_filtering: dict = {}
        self.pre_values: list = []
        self.pre_annotation: dict = {}

        self.main_annotation: dict = {}
        self.adapted_annotation: dict = {}
        self.post_filtering: dict = {}
        self.adapted_post_filtering: dict = {}

        self.dataframe_filtering = {}

        self.date_pre_filtering = {}
        self.date_previous_pre_filtering = {}

        self.parsing_fields = {}

    def get_interval_class(self) -> Type[IntervalEnum]:
        return IntervalEnum

    def form_cache_key(self, date_range_filtering: dict) -> str:
        cache_data = {
            'model_name': self.model_name.__name__,
            'pre_filtering': self.pre_filtering,
            'pre_values': self.pre_values,
            'pre_annotation': str(self.pre_annotation),
            'main_annotation': str(self.main_annotation),
            'post_filtering': self.post_filtering,
            'date_range_filtering': date_range_filtering
        }
        cache_key = hashlib.sha256(json.dumps(cache_data, sort_keys=True).encode()).hexdigest()
        return cache_key

    def get_queryset(self, date_range_filtering: dict, use_adapting: bool = False) -> list:
        if use_adapting:
            main_annotations = self.adapted_annotation
            post_filtering = self.adapted_post_filtering
        else:
            main_annotations = self.main_annotation
            post_filtering = self.post_filtering
        print()
        print(f'self.model_name: {self.model_name}')
        print(f'self.select_related: {self.select_related}')
        print(f'self.prefetch_related: {self.prefetch_related}')
        print(f'self.pre_annotation: {self.pre_annotation}')
        print(f'self.pre_values: {self.pre_values}')
        print(f'self.pre_filtering: {self.pre_filtering}')
        print(f'self.main_annotation: {main_annotations}')
        print(f'self.post_filtering: {post_filtering}')
        print(f'date_range_filtering: {date_range_filtering}')

        print(f'self.parsing_fields: {self.parsing_fields}')

        print(f'dataframe_filtering: {self.dataframe_filtering}')

        print(
            f'{self.model_name.__name__}.objects.annotate({self.pre_annotation}).values({self.pre_values})'
            f'.filter({self.pre_filtering}, {date_range_filtering}).annotate({main_annotations})'
            f'.filter({post_filtering})')
        queryset = cache.get(self.form_cache_key(date_range_filtering))

        print()
        if queryset:
            return queryset

        queryset = self.model_name.objects \
            .select_related(*self.select_related) \
            .prefetch_related(*self.prefetch_related) \
            .annotate(**self.pre_annotation) \
            .values(*self.pre_values) \
            .filter(**self.pre_filtering, **date_range_filtering) \
            .annotate(**main_annotations) \
            .filter(**post_filtering)
        cache.set(self.form_cache_key(date_range_filtering), queryset, 60 * 15)
        return queryset

    def get_data_from_request(self) -> None:
        """
        Gets data from request and populate it in variables
        """
        self.dimension_data = self.request.data.get('dimensions')
        self.metrics_data = self.request.data.get('metrics')
        self.date_ranges = {'date_range': self.request.data.get('date_range', None)}

        if self.request.data.get('prev_date_range', None):
            self.date_ranges['prev_date_range'] = self.request.data.get('prev_date_range', None)
            self.date_ranges['previous'] = True

    def get_dimension_base_model(self, dimension_name: str) -> None:
        """
        Returns Dimension base model for validation dimension's input data
        """
        self.model_dimension: Type[BaseModel] = \
            DimensionQualifierBaseModel(name=dimension_name).dict()['name']
        self.has_intervals = True if self.model_dimension.__name__ == 'IntervalBaseModel' else self.has_intervals

    def validate_dimensions(self) -> None:
        """
        Validates data from dimension dictionary.
        """
        for unit_date in self.dimension_data:
            self.get_dimension_base_model(unit_date.get('name', 'null'))
            dimension_answer: dict = self.model_dimension(**unit_date).dict()
            self.set_dimension_answers(dimension_answer)

    def set_dimension_answers(self, dimension_answer: dict) -> None:
        if self.model_dimension.__name__ not in self.interval_base_models:
            dimension_class: Type[dimensions.DimensionFieldAssignment] = \
                getattr(dimensions, f'{dimension_answer.get("name")}FieldAssignment')

            answer = dimension_class(**dimension_answer).response()
        else:
            answer = dimension_answer

        self.pre_annotation.update(answer.get('pre_annotation', {}))
        self.pre_filtering.update(answer.get('pre_filtering', {}))
        self.pre_values.extend(answer.get('pre_values', []))
        self.parsing_fields.update(answer.get('parsed_field_names', {}))

    def set_metric_validation_model(self) -> None:
        self.model_metric: Type[ModelMetric] = MetricModelsEnum.get_metric_model_by_name(self.model_name.__name__)

    def validate_metric_answers(self) -> None:
        metric_answer: dict = MetricsBaseModel(metrics=self.metrics_data).dict()

        self.date_ranges['previous'] = metric_answer.get('required_date_ranges', False)

        self.dataframe_filtering = metric_answer.get('dataframe_filtering', {})

        for metric in metric_answer.get('post_filtering', []):
            parsed_metric_answers = self.model_metric(**metric).response()
            self.main_annotation.update(parsed_metric_answers.get('annotation', {}))
            self.post_filtering.update(parsed_metric_answers.get('post_filtering', {}))

        self.select_related = set(self.select_related)
        self.prefetch_related = set(self.prefetch_related)

        if self.dataframe_filtering:
            self.adapt_annotations_and_filtering()

    def validate_date_ranges(self) -> None:
        date_range_answer: dict = DateRangeBaseModel(**self.date_ranges).dict()
        self.date_pre_filtering = date_range_answer.get('pre_filtering')
        self.date_previous_pre_filtering = date_range_answer.get('previous_pre_filtering', {})

    def adapt_annotations_and_filtering(self) -> None:
        """
        Adapts post_filtering and main_annotation in order to make less
        queries in prev_daterange when there is no conditions to seek diff
        or diff_percent in several metrics
        """
        dataframe_names = []
        for element in self.dataframe_filtering:
            dataframe_names.append(element['name'].replace('_diff', '').replace('_percent', ''))

        print()
        for key, value in self.main_annotation.items():
            print(f'{key} in {dataframe_names} == {key in dataframe_names}')
            if key in dataframe_names:
                self.adapted_annotation[key] = value

        print(self.adapted_annotation)
        print()

        for key, value in self.post_filtering.items():
            main_name = key.split('__')[0]
            if main_name in dataframe_names:
                self.adapted_post_filtering[key] = value

    def rename_columns(self, queryset: list) -> list:
        df = pd.DataFrame(queryset)
        df.rename(columns=self.parsing_fields, inplace=True)
        return df.to_dict(orient='records')

    def get_timedelta(self, first_date: str, last_date: str) -> timedelta:
        return datetime.datetime.strptime(last_date, '%Y-%m-%d') - datetime.datetime.strptime(first_date, '%Y-%m-%d')

    def get_interval_field(self) -> str:
        return list(self.pre_annotation.keys())[0]

    def apply_dataframe_without_common_fields(self,
                                              current_range_df: pd.DataFrame,
                                              prev_range_df: pd.DataFrame) -> pd.DataFrame:
        """
        Evaluated dataframes with common fields
        """

        # drops indexes in order to get all records be able to subtract
        current_range_df.reset_index(drop=True, inplace=True)
        prev_range_df.reset_index(drop=True, inplace=True)
        print('current in APPLYWITHOUT:')
        print(current_range_df)
        print('previous in APPLIWITHOUT:')
        print(prev_range_df)
        for obj in self.dataframe_filtering:
            name: str = obj.get('name')
            existing_name = name.replace('_diff', '').replace('_percent', '')

            print(f'name: {name} extisting name: {existing_name}')

            # Calculate the 'field_diff' by subtracting 'field' from the previous DataFrame
            if 'percent' in name:
                current_range_df[name] = round(self.find_percent(
                    current_range_df[existing_name], prev_range_df[existing_name]
                ), 2)
            else:
                current_range_df[name] = round(current_range_df[existing_name] - prev_range_df[existing_name], 2)

            # Fill NaN values in 'field_diff' with 'field' from the current DataFrame
            current_range_df[name].fillna(current_range_df[existing_name], inplace=True)

            # iterating through 'options' inside every field and applying them
            for filter_data in obj.get('options', {}):
                option = filter_data['option']
                value = filter_data['value']

                comparison_func = self.comparison_functions[option]

                # get comparison function in order to further filtration of df
                filter_condition = comparison_func(current_range_df[name], value)

                current_range_df = current_range_df[filter_condition]
        return current_range_df

    def apply_dataframe_with_common_fields(self,
                                           filtered_df: pd.DataFrame,
                                           common_fields: list,
                                           exception_fields: list) -> pd.DataFrame:
        """
        Evaluates all metric without having common fields (only interval dimensions)
        """
        dataframe_fields = []
        for obj in self.dataframe_filtering:
            name: str = obj.get('name')
            dataframe_fields.append(name)
            existing_name = name.replace('_diff', '').replace('_percent', '')

            # Calculate the 'field_diff' and 'field_diff_percent' by subtracting 'field' from the previous DataFrame
            if 'percent' in name:
                filtered_df[name] = round(self.find_percent(
                    filtered_df[existing_name], filtered_df[f'{existing_name}_prev']), 2)
            else:
                filtered_df[name] = round(filtered_df[existing_name]
                                          - filtered_df[f'{existing_name}_prev'], 2)

            # Fill NaN values in 'field_diff' with 'field' from the current DataFrame
            filtered_df[name].fillna(filtered_df[existing_name])

            # iterating through 'options' inside every field and applying them
            for filter_data in obj.get('options', {}):
                option = filter_data['option']
                value = filter_data['value']

                comparison_func = self.comparison_functions[option]

                # get comparison function in order to further filtration of DataFrame
                filter_condition = comparison_func(filtered_df[name], value)

                filtered_df = filtered_df[filter_condition]

        result_df = filtered_df[common_fields + exception_fields + dataframe_fields]
        return result_df

    def apply_nullable_diff(self, cut_dataframe: pd.DataFrame) -> pd.DataFrame:
        for obj in self.dataframe_filtering:
            name: str = obj.get('name')
            existing_name = name.replace('_diff', '').replace('_percent', '')

            cut_dataframe[name] = cut_dataframe[existing_name]

            for filter_data in obj.get('options', {}):
                option = filter_data['option']
                value = filter_data['value']

                comparison_func = self.comparison_functions[option]

                # get comparison function in order to further filtration of DataFrame
                filter_condition = comparison_func(cut_dataframe[name], value)

                cut_dataframe = cut_dataframe[filter_condition]

        return cut_dataframe

    def find_percent(self, curr_value: float, prev_value: float) -> float:
        difference = curr_value - prev_value
        try:
            return difference * 100 / prev_value
        except ZeroDivisionError:
            return difference

    def find_additions_metrics(self, current_range_response: list, prev_range_response: list) -> list:
        """
        Execute evaluation of metrics in dataframe
        """
        if not current_range_response:
            return []

        print(len(current_range_response))
        print(len(prev_range_response))

        current_range_df = pd.DataFrame(current_range_response)
        prev_range_df = pd.DataFrame(prev_range_response)

        cut_current_range_df: pd.DataFrame = pd.DataFrame()

        if self.has_intervals:
            # getting timedelta of previous daterange and current daterange
            prev_timedelta = self.get_timedelta(list(self.date_previous_pre_filtering.values())[0],
                                                list(self.date_previous_pre_filtering.values())[1])
            curr_timedelta = self.get_timedelta(list(self.date_pre_filtering.values())[0],
                                                list(self.date_pre_filtering.values())[1])

            # if timedelta of previous daterange is less, we cut off from current daterange DataFrame all
            # records, whose interval date does not match previous (it means we persist here only last days,
            # that could be evaluated with dates of previous range)
            if prev_timedelta < curr_timedelta:
                print(f'{prev_timedelta} < {curr_timedelta}')
                interval_field: str = self.get_interval_field()
                last_date_current_range = datetime.datetime.strptime(list(self.date_pre_filtering.values())[1],
                                                                     '%Y-%m-%d')

                start_date_current_range: datetime = last_date_current_range - \
                    timedelta(days=prev_timedelta.days)

                # get period for further truncating of the date
                to_period_form = self.get_interval_class().get_to_period_by_name(self.get_interval_field())

                # Convert start_date_current_range to UTC datetime if it's not already and truncate
                # it to predefined period
                start_date_current_range = pd.to_datetime(start_date_current_range)\
                    .to_period(to_period_form)\
                    .to_timestamp()\
                    .tz_localize('UTC')

                print(f'start_date_current_range: {start_date_current_range}')

                # DataFrame whose intervals does NOT match previous daterange
                cut_current_df = current_range_df[current_range_df[interval_field] < start_date_current_range]

                # filters current DataFrame with only matching interval date
                current_range_df = current_range_df[current_range_df[interval_field] >= start_date_current_range]

                cut_current_range_df = self.apply_nullable_diff(cut_current_df)

        print(current_range_df)
        print(prev_range_df)

        # defines common field by which it must be merged
        exception_fields = list(self.main_annotation.keys()) + list(self.pre_annotation.keys())
        common_fields = [field for field in current_range_df.columns if field not in exception_fields]

        if common_fields:
            filtered_df: pd.DataFrame = current_range_df.merge(prev_range_df, on=common_fields, suffixes=('', '_prev'))
            result_df = self.apply_dataframe_with_common_fields(filtered_df, common_fields, exception_fields)
        else:
            result_df = self.apply_dataframe_without_common_fields(current_range_df, prev_range_df)

        print('result is:')
        print(result_df)

        # if there is cut DataFrame with unmatched dates we concatenate it ignoring indexes
        print(f'cut_current is: {cut_current_range_df}')
        if not cut_current_range_df.empty:
            result_df = pd.concat([cut_current_range_df, result_df], ignore_index=True)

        print('concatenated result:')
        print(result_df)

        return result_df.to_dict(orient='records')

    # def calculate_totals(self, answer: list):
    #     records_df = pd.DataFrame(answer)
    #     overall_record = pd.DataFrame({
    #         'product__name': ['overall'],
    #         'turnover': [records_df['turnover'].sum()],
    #         'column1': [records_df['column1'].sum()],
    #         'column2': [records_df['column2'].sum()],
    #         # Add more columns here as needed
    #     })
    #     pass

    @extend_schema(
        parameters=[
            OpenApiParameter(name='page_size', location=OpenApiParameter.QUERY,
                             description='Size of the queryset that will be returned', required=False, type=int),
            OpenApiParameter(name='page', location=OpenApiParameter.QUERY,
                             description='Number of the page of the queryset that will be returned', required=False,
                             type=int)
        ],
        request=inline_serializer(
            name='Analytics',
            fields={
                'name': CharField()
            }
        )
    )
    def post(self, request, *args, **kwargs) -> Response:
        self.get_data_from_request()

        self.validate_dimensions()

        self.set_metric_validation_model()

        self.validate_metric_answers()

        self.validate_date_ranges()

        current_range_response: list = self.get_queryset(self.date_pre_filtering)
        if self.date_ranges.get('previous', None):
            prev_range_response: list = self.get_queryset(self.date_previous_pre_filtering,
                                                          use_adapting=True)
            records_list = self.find_additions_metrics(list(current_range_response), list(prev_range_response))
            records_list = self.rename_columns(records_list)
            paginated_response = self.paginate_queryset(records_list)
            print(paginated_response)
            return self.get_paginated_response(self.paginate_queryset(records_list))

        current_range_response = self.rename_columns(current_range_response)
        paginated_response = self.paginate_queryset(current_range_response)
        # if self.request.query_params.get('evaluate_totals', None):
        #     paginated_response = self.calculate_totals(paginated_response)
        return self.get_paginated_response(paginated_response)
