from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CategoryViewSet, ProducerViewSet, ProductViewSet

router = DefaultRouter()
router.register(r"category", CategoryViewSet, basename="category")
router.register(r"product", ProductViewSet, basename="product")
router.register(r"producer", ProducerViewSet, basename="producer")


urlpatterns = [path("", include(router.urls))]
