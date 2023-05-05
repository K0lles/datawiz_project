from django_filters import CharFilter
from django_filters.rest_framework import FilterSet, OrderingFilter

from receipts.models import Supplier, Terminal


class SupplierFilter(FilterSet):
    name = CharFilter(field_name="name", lookup_expr="icontains")

    ordering = OrderingFilter(fields=(("id", "id"), ("name", "name")))

    class Meta:
        model = Supplier
        fields = "__all__"


class TerminalFilter(FilterSet):
    name = CharFilter(field_name="name", lookup_expr="icontains")
    shop = CharFilter(field_name="shop__name", lookup_expr="icontains")

    ordering = OrderingFilter(fields=(("id", "id"), ("name", "name"), ("shop__name", "shop")))

    class Meta:
        model = Terminal
        fields = "__all__"
