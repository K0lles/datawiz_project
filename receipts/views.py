from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.exceptions import ValidationError

from datawiz_project.paginators import CustomNumberPaginator
from datawiz_project.viewsets import DisplayViewSet
from receipts.filters import SupplierFilter, TerminalFilter
from receipts.models import Supplier, Terminal
from receipts.serializers import SupplierSerializer, TerminalSerializer


class SupplierViewSet(DisplayViewSet):
    model = Supplier
    serializer_class = SupplierSerializer
    pagination_class = CustomNumberPaginator
    filter_backends = (DjangoFilterBackend,)
    filterset_class = SupplierFilter


class TerminalViewSet(DisplayViewSet):
    model = Terminal
    serializer_class = TerminalSerializer
    pagination_class = CustomNumberPaginator
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TerminalFilter

    def get_queryset(self):
        return Terminal.objects.select_related("shop", "shop__group").all()

    def get_object(self):
        try:
            return Terminal.objects.select_related("shop", "shop__group").get(pk=self.kwargs.get(self.lookup_field))
        except Terminal.DoesNotExist:
            raise ValidationError(detail={"detail": _("Не знайдено.")}, code=status.HTTP_400_BAD_REQUEST)
