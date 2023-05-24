import hashlib
import json

import pandas as pd
from django.core.cache import cache
from drf_spectacular.utils import (OpenApiParameter, extend_schema,
                                   inline_serializer)
from pydantic import ValidationError
from rest_framework import status
from rest_framework.fields import CharField
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response

from analytics.aggregators import DataFrameAggregator, MainAggregator
from datawiz_project.paginators import CustomNumberPaginator


class AnalyticsRetrieveAPIView(CreateAPIView):
    serializer_class = None
    aggregator_class = MainAggregator
    dataframe_aggregator_class = DataFrameAggregator
    pagination_class = CustomNumberPaginator

    def form_cache_key(self, date_range_filtering: dict) -> str:
        cache_data = {
            'model_name': self.aggregator.model_name.__name__,
            'pre_filtering': self.aggregator.pre_filtering,
            'pre_values': self.aggregator.pre_values,
            'pre_annotation': str(self.aggregator.pre_annotation),
            'main_annotation': str(self.aggregator.main_annotation),
            'post_filtering': self.aggregator.post_filtering,
            'date_range_filtering': date_range_filtering
        }
        cache_key = hashlib.sha256(json.dumps(cache_data, sort_keys=True).encode()).hexdigest()
        return cache_key

    def get_queryset(self, date_range_filtering: dict, use_adapting: bool = False) -> list:
        if use_adapting:
            main_annotation = self.aggregator.adapted_annotation
            post_filtering = self.aggregator.adapted_post_filtering
        else:
            main_annotation = self.aggregator.main_annotation
            post_filtering = self.aggregator.post_filtering

        queryset = cache.get(self.form_cache_key(date_range_filtering))
        if queryset:
            return queryset

        queryset = self.aggregator.model_name.objects \
            .annotate(**self.aggregator.pre_annotation) \
            .values(*self.aggregator.pre_values) \
            .filter(**self.aggregator.pre_filtering, **date_range_filtering) \
            .annotate(**main_annotation) \
            .filter(**post_filtering)
        cache.set(self.form_cache_key(date_range_filtering), queryset, 60 * 15)
        return queryset

    def perform_filtration(self, data: list[dict]) -> list[dict]:
        df = pd.DataFrame(data)
        if self.request.query_params.get('field', None) and self.request.query_params.get('value', None):
            df = self.aggregator.search(df,
                                        self.request.query_params.get('field'),
                                        self.request.query_params.get('value'))
        if self.request.query_params.get('ordering', None):
            df = self.aggregator.sort_by_dimension_name(df, self.request.query_params.get('ordering'))

        return df.to_dict(orient='records')

    def totals_evaluation(self, data: list[dict]) -> list[dict]:
        df = pd.DataFrame(data)
        if self.request.query_params.get('apply_total', None):
            return self.aggregator.count_metric_totals(df)
        return df.to_dict(orient='records')

    def process_response(self, data: list[dict]) -> list[dict]:
        filtrated_response = self.perform_filtration(data)
        paginated_response = self.paginate_queryset(self.aggregator.rename_columns(filtrated_response))
        counted_response = self.totals_evaluation(paginated_response)
        return counted_response

    @extend_schema(
        parameters=[
            OpenApiParameter(name='page_size', location=OpenApiParameter.QUERY,
                             description='Size of the queryset that will be returned', required=False, type=int),
            OpenApiParameter(name='page', location=OpenApiParameter.QUERY,
                             description='Number of the page of the queryset that will be returned', required=False,
                             type=int),
            OpenApiParameter(name='apply_total', location=OpenApiParameter.QUERY,
                             description='Counts totals of each metric', required=False, type=str),
            OpenApiParameter(name='ordering', location=OpenApiParameter.QUERY,
                             description='Dimension field name for sorting', required=False, type=str),
            OpenApiParameter(name='field', location=OpenApiParameter.QUERY,
                             description='Field name by which searching will be executed',
                             required=False, type=str),
            OpenApiParameter(name='value', location=OpenApiParameter.QUERY,
                             description='Value basing on searching will be executed',
                             required=False, type=str)
        ],
        request=inline_serializer(
            name='Analytics',
            fields={
                'name': CharField()
            }
        )
    )
    def post(self, request, *args, **kwargs) -> Response:
        try:
            self.aggregator: MainAggregator = self.aggregator_class(**request.data)
        except ValidationError as e:
            return Response(data=e.errors(), status=status.HTTP_400_BAD_REQUEST)

        current_range_response: list = self.get_queryset(self.aggregator.date_pre_filtering)
        if self.aggregator.required_previous_date_range:
            prev_range_response: list = self.get_queryset(self.aggregator.date_previous_pre_filtering,
                                                          use_adapting=True)

            dataframe_aggregator = self.dataframe_aggregator_class(self.aggregator)
            records_list = dataframe_aggregator.find_additions_metrics(current_range_response, prev_range_response)
            records_list_renamed = self.aggregator.rename_columns(records_list)
            response = self.process_response(records_list_renamed)
            return self.get_paginated_response(response)

        current_range_response = self.aggregator.rename_columns(current_range_response)
        response = self.process_response(current_range_response)
        return self.get_paginated_response(response)
