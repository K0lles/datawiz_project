from django_filters import OrderingFilter
from django_filters.rest_framework import CharFilter, FilterSet, NumberFilter

from products.models import Category, Producer, Product


class CategoryFilter(FilterSet):
    name = CharFilter(field_name="name", lookup_expr="icontains")
    parent = CharFilter(field_name="parent__name", lookup_expr="icontains")
    left = NumberFilter(field_name="left", lookup_expr="exact")
    left__lte = NumberFilter(field_name="left", lookup_expr="lte")
    left__gte = NumberFilter(field_name="left", lookup_expr="gte")
    right = NumberFilter(field_name="right", lookup_expr="exact")
    right__lte = NumberFilter(field_name="right", lookup_expr="lte")
    right__gte = NumberFilter(field_name="right", lookup_expr="gte")
    level = NumberFilter(field_name="level", lookup_expr="exact")
    level__lte = NumberFilter(field_name="level", lookup_expr="lte")
    level__gte = NumberFilter(field_name="level", lookup_expr="gte")

    ordering = OrderingFilter(fields=(("id", "id"), ("name", "name"), ("parent__name", "category")))

    class Meta:
        model = Category
        fields = "__all__"


class ProductFilter(FilterSet):
    name = CharFilter(field_name="name", lookup_expr="icontains")
    category = CharFilter(field_name="category__name", lookup_expr="icontains")
    producer = CharFilter(field_name="producer__name", lookup_expr="icontains")
    article = CharFilter(field_name="article", lookup_expr="icontains")
    barcode = CharFilter(field_name="barcode", lookup_expr="icontains")

    ordering = OrderingFilter(
        fields=(
            ("id", "id"),
            ("name", "name"),
            ("category__name", "category"),
            ("producer__name", "producer"),
            ("article", "article"),
        )
    )

    class Meta:
        model = Product
        exclude = "__all__"


class ProducerFilter(FilterSet):
    name = CharFilter(field_name="name", lookup_expr="icontains")

    ordering = OrderingFilter(
        fields=(
            ("id", "id"),
            ("name", "name"),
        )
    )

    class Meta:
        model = Producer
        fields = "__all__"
