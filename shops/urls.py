from django.urls import include, path
from rest_framework.routers import DefaultRouter

from shops.views import ShopGroupViewSet, ShopViewSet

router = DefaultRouter()
router.register(r"shop", ShopViewSet, basename="shop")
router.register(r"shop-group", ShopGroupViewSet, basename="shop-group")


urlpatterns = [
    path("", include(router.urls)),
]
