from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet


class DisplayViewSet(ListAPIView, RetrieveAPIView, GenericViewSet):
    model = None

    def check_model_variable(self):
        if not self.model:
            raise AttributeError(f'You did not define "model" variable in {self.__class__.__name__}')

    def get_queryset(self):
        self.check_model_variable()

        # if you have to make some select_related or prefetch_related, overwrite this method
        return self.model.objects.all()

    def get_object(self):
        self.check_model_variable()
        try:
            return self.model.objects.get(pk=self.kwargs.get(self.lookup_field))
        except self.model.DoesNotExist:
            raise ValidationError(detail={"detail": _("Не знайдено.")}, code=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        filtered_queryset = self.filter_queryset(queryset)
        paginated_queryset = self.paginate_queryset(filtered_queryset)
        serializer = self.get_serializer(instance=paginated_queryset, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = self.get_serializer(instance=obj)
        return Response(data=serializer.data, status=status.HTTP_200_OK)
