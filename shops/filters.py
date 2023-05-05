from django_filters import CharFilter, NumberFilter
from django_filters.rest_framework import FilterSet, OrderingFilter

from shops.models import Shop, ShopGroup


class ShopFilter(FilterSet):
    name = CharFilter(field_name="name", lookup_expr="icontains")
    group = CharFilter(field_name="group__name", lookup_expr="icontains")

    ordering = OrderingFilter(fields=(("id", "id"), ("name", "name"), ("group__name", "group")))

    class Meta:
        model = Shop
        fields = "__all__"


class ShopGroupFilter(FilterSet):
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

    ordering = OrderingFilter(fields=(("id", "id"), ("name", "name"), ("parent__name", "parent")))

    class Meta:
        model = ShopGroup
        fields = "__all__"
