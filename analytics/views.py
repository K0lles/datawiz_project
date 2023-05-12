from enum import Enum
from typing import Type

from django.db.models import Model
from django.utils.translation import gettext_lazy as _
from pydantic import BaseModel
from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response

from analytics.metrics import (FullCategoryProductMaterializedViewMetric,
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

    @classmethod
    def get_metric_model_by_name(cls, name: str) -> Type[ModelMetric]:
        for item in cls:
            if item.value[0] == name:
                return item.value[1]
        raise ValueError(_("Введіть коректне значення 'name'."))


class AnalyticsRetrieveAPIView(RetrieveAPIView):
    serializer_class = None
    pagination_class = CustomNumberPaginator

    def retrieve(self, request, *args, **kwargs):

        # gets from request.data all necessary objects
        dimension_data = request.data.get('dimensions')
        metrics_data = request.data.get('metrics')
        date_ranges = {'date_range': request.data.get('date_range', None)}

        if request.data.get('prev_date_range', None):
            date_ranges['prev_date_range'] = request.data.get('prev_date_range', None)
            date_ranges['previous'] = True

        # get right BaseModel for correct validation
        dimension_model_object: Type[BaseModel] = \
            DimensionQualifierBaseModel(name=dimension_data.get('name', None)).dict()['name']

        dimension_answer: dict = dimension_model_object(**dimension_data).dict()
        model_name: Type[Model] = dimension_answer.get('name', None)
        previous = dimension_answer.get('required_date_ranges', False)
        pre_annotation = dimension_answer.get('pre_annotation', {})   # forming first annotations
        pre_filtering = dimension_answer.get('filtering', {})     # forming starting filtering conditions
        prev_values = dimension_answer.get('pre_values', [])    # forming start values

        metric_answer: dict = MetricsBaseModel(metrics=metrics_data).dict()

        model_metric: Type[ModelMetric] = MetricModelsEnum.get_metric_model_by_name(model_name.__name__)

        parsed_metric_answers = model_metric(**metric_answer['post_filtering']).response()
        main_annotation: dict = parsed_metric_answers.get('annotation')
        post_filtering: dict = parsed_metric_answers.get('post_filtering')
        select_related = parsed_metric_answers.get('select_related')
        prefetch_related = parsed_metric_answers.get('prefetch_related')

        print(pre_annotation, pre_filtering, prev_values, main_annotation, post_filtering, select_related,
              prefetch_related)

        if date_ranges.get('date_range', None):
            date_range_answer: dict = DateRangeBaseModel(**date_ranges, previous=previous).dict()
        else:
            date_range_answer = {}

        print({'dimension_answer': dimension_answer,
               'metric_answer': metric_answer,
               'date_range_answer': date_range_answer})

        print(type(dimension_answer))

        return Response({'result': 'okey'})
        # return Response({'dimension_answer': json.dumps(dimension_answer).encode('utf-8'),
        #                  'metric_answer': json.dumps(metric_answer).encode('utf-8'),
        #                  'date_range_answer': json.dumps(date_range_answer).encode('utf-8')})
