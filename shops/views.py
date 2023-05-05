from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.exceptions import ValidationError

from datawiz_project.paginators import CustomNumberPaginator
from datawiz_project.viewsets import DisplayViewSet
from shops.filters import ShopFilter, ShopGroupFilter
from shops.models import Shop, ShopGroup
from shops.serializers import ShopGroupSerializer, ShopSerializer


class ShopViewSet(DisplayViewSet):
    model = Shop
    serializer_class = ShopSerializer
    pagination_class = CustomNumberPaginator
    filter_backends = (DjangoFilterBackend,)
    filterset_class = ShopFilter

    def get_queryset(self):
        return self.model.objects.select_related("group__parent__parent").all()

    def get_object(self):
        self.check_model_variable()
        try:
            return self.model.objects.select_related("group__parent__parent").get(pk=self.kwargs.get(self.lookup_field))
        except self.model.DoesNotExist:
            raise ValidationError(detail={"detail": _("Не знайдено.")}, code=status.HTTP_400_BAD_REQUEST)


class ShopGroupViewSet(DisplayViewSet):
    model = ShopGroup
    serializer_class = ShopGroupSerializer
    pagination_class = CustomNumberPaginator
    filter_backends = (DjangoFilterBackend,)
    filterset_class = ShopGroupFilter

    def get_queryset(self):
        return self.model.objects.select_related("parent__parent__parent").all()

    def get_object(self):
        self.check_model_variable()
        try:
            return self.model.objects.select_related("parent__parent__parent").get(
                pk=self.kwargs.get(self.lookup_field)
            )
        except self.model.DoesNotExist:
            raise ValidationError(detail={"detail": _("Не знайдено.")}, code=status.HTTP_400_BAD_REQUEST)
