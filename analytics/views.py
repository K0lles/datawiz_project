from enum import Enum
from typing import Type

import pandas as pd
from django.db.models import Model, QuerySet
from django.utils.translation import gettext_lazy as _
from pydantic import BaseModel
from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response

from analytics.functions import assign_path_to_date_field
from analytics.metrics import (CartItemMetric,
                               FullCategoryProductMaterializedViewMetric,
                               FullShopGroupShopMaterializedViewMetric,
                               ModelMetric, ProducerMetric, ProductMetric,
                               ShopMetric, SupplierMetric, TerminalMetric)
from analytics.serializers import (DateRangeBaseModel,
                                   DimensionQualifierBaseModel,
                                   MetricsBaseModel)
from datawiz_project.paginators import CustomNumberPaginator


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


class AnalyticsRetrieveAPIView(RetrieveAPIView):
    serializer_class = None
    pagination_class = CustomNumberPaginator

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.dimension_data: dict = {}
        self.metrics_data: list = []
        self.date_ranges: dict = {}

        self.model_name = None
        self.model_dimension = None
        self.model_metric = None

        self.select_related: list = []
        self.prefetch_related: list = []

        self.pre_filtering: dict = {}
        self.pre_values: list = []
        self.pre_annotation: dict = {}

        self.main_annotation: dict = {}
        self.post_filtering: dict = {}

        self.dataframe_filtering = {}

        self.date_pre_filtering = {}
        self.date_previous_pre_filtering = {}

    def get_queryset(self, date_range_filtering: dict) -> dict:
        queryset = self.model_name.objects \
                    .select_related(*self.select_related) \
                    .prefetch_related(*self.prefetch_related) \
                    .annotate(**self.pre_annotation) \
                    .values(*self.pre_values) \
                    .filter(**self.pre_filtering, **date_range_filtering) \
                    .annotate(**self.main_annotation) \
                    .filter(**self.post_filtering)
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

    def get_dimension_base_model(self) -> None:
        """
        Returns Dimension base model for validation dimension's input data
        """
        self.model_dimension: Type[BaseModel] = \
            DimensionQualifierBaseModel(name=self.dimension_data.get('name', None)).dict()['name']

    def validate_dimensions(self) -> None:
        """
        Validates data from dimension dictionary.
        """
        dimension_answer: dict = self.model_dimension(**self.dimension_data).dict()
        self.set_dimension_answers(dimension_answer)

    def set_dimension_answers(self, dimension_answer: dict) -> None:
        self.model_name: Type[Model] = dimension_answer.get('name', None)
        self.date_ranges['previous'] = dimension_answer.get('required_date_ranges', False)
        self.pre_annotation = dimension_answer.get('pre_annotation', {})  # forming first annotations
        self.pre_filtering = dimension_answer.get('filtering', {})  # forming starting filtering conditions
        self.pre_values = dimension_answer.get('pre_values', [])  # forming start values

    def set_metric_validation_model(self) -> None:
        self.model_metric: Type[ModelMetric] = MetricModelsEnum.get_metric_model_by_name(self.model_name.__name__)

    def validate_metric_answers(self) -> None:
        metric_answer: dict = MetricsBaseModel(metrics=self.metrics_data).dict()

        for metric in metric_answer.get('post_filtering', []):
            parsed_metric_answers = self.model_metric(**metric).response()
            self.main_annotation.update(parsed_metric_answers.get('annotation'))
            self.post_filtering.update(parsed_metric_answers.get('post_filtering'))
            self.select_related.extend(parsed_metric_answers.get('select_related'))
            self.prefetch_related.extend(parsed_metric_answers.get('prefetch_related'))

        self.select_related = set(self.select_related)
        self.prefetch_related = set(self.prefetch_related)

    def validate_date_ranges(self) -> None:
        date_range_answer: dict = DateRangeBaseModel(**self.date_ranges).dict()
        self.date_pre_filtering: dict = assign_path_to_date_field(
            self.model_metric.__name__,
            self.model_metric.base_field, date_range_answer.get('pre_filtering')
        )
        self.date_previous_pre_filtering: dict = date_range_answer.get('previous_pre_filtering', {})

    def find_additions_metrics(self, current_range_response: list, prev_range_response: list) -> None:
        # comparison_functions = {
        #     'eq': operator.eq,
        #     'ne': operator.ne,
        #     'lt': operator.lt,
        #     'lte': operator.le,
        #     'gt': operator.gt,
        #     'gte': operator.ge,
        # }
        current_range_df = pd.DataFrame(current_range_response)
        prev_range_df = pd.DataFrame(prev_range_response)

        current_range_df.set_index('id', inplace=True)
        prev_range_df.set_index('id', inplace=True)

        for obj in self.dataframe_filtering:
            name: str = obj.get('name')
            existing_name = name.replace('_diff', '').replace('_percent', '')
            # Calculate the 'turnover_diff' by subtracting 'turnover' from the previous DataFrame
            if 'percent' in name:
                pass
            else:
                current_range_df[name] = current_range_df[existing_name] - prev_range_df[existing_name]

            # Fill NaN values in 'turnover_diff' with 'turnover' from the current DataFrame
            current_range_df['turnover_diff'].fillna(current_range_df['turnover'], inplace=True)

            # for filter_data in self.dataframe_filtering:
            #     column_name = filter_data['name']
            #     filter_options = filter_data['options']
            #
            #     for option_data in filter_options:
            #         option = option_data['option']
            #         value = option_data['value']
            #
            #         comparison_func = comparison_functions[option]
            #         filter_condition = comparison_func(df[column_name], value)
            #
            #         df = df[filter_condition]

    def retrieve(self, request, *args, **kwargs) -> Response:
        self.get_data_from_request()

        self.get_dimension_base_model()

        self.validate_dimensions()

        self.set_metric_validation_model()

        self.validate_metric_answers()

        self.validate_date_ranges()

        current_range_response: QuerySet = self.paginate_queryset(self.get_queryset(self.date_pre_filtering))
        # if self.date_ranges.get('previous', None):
        #    prev_range_response: QuerySet = self.paginate_queryset(self.get_queryset(self.date_previous_pre_filtering))
        #     self.find_additions_metrics(list(current_range_response), list(prev_range_response))
        print(current_range_response)

        return self.get_paginated_response(current_range_response)
