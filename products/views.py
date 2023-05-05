from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.exceptions import ValidationError

from datawiz_project.paginators import CustomNumberPaginator
from datawiz_project.viewsets import DisplayViewSet
from products.filters import CategoryFilter, ProducerFilter, ProductFilter
from products.models import Category, Producer, Product
from products.serializers import (CategorySerializer, ProducerSerializer,
                                  ProductSerializer)


class CategoryViewSet(DisplayViewSet):
    model = Category
    serializer_class = CategorySerializer
    pagination_class = CustomNumberPaginator
    filter_backends = (DjangoFilterBackend,)
    filterset_class = CategoryFilter

    def get_queryset(self):
        return self.model.objects.select_related("parent__parent__parent").all()

    def get_object(self):
        try:
            return self.model.objects.select_related("parent__parent__parent").get(
                pk=self.kwargs.get(self.lookup_field)
            )
        except self.model.DoesNotExist:
            raise ValidationError(detail={"detail": _("Не знайдено.")}, code=status.HTTP_400_BAD_REQUEST)


class ProductViewSet(DisplayViewSet):
    model = Product
    serializer_class = ProductSerializer
    pagination_class = CustomNumberPaginator
    filter_backends = (DjangoFilterBackend,)
    filterset_class = ProductFilter

    def get_queryset(self):
        return self.model.objects.select_related("category", "producer").all()

    def get_object(self):
        try:
            return self.model.objects.select_related("category", "producer").get(pk=self.kwargs.get(self.lookup_field))
        except self.model.DoesNotExist:
            raise ValidationError(detail={"detail": _("Не знайдено.")}, code=status.HTTP_400_BAD_REQUEST)


class ProducerViewSet(DisplayViewSet):
    model = Producer
    serializer_class = ProducerSerializer
    pagination_class = CustomNumberPaginator
    filter_backends = (DjangoFilterBackend,)
    filterset_class = ProducerFilter
