from django.urls import include, path
from rest_framework.routers import DefaultRouter

from receipts.views import SupplierViewSet, TerminalViewSet

router = DefaultRouter()
router.register(r"supplier", SupplierViewSet, basename="supplier")
router.register(r"terminal", TerminalViewSet, basename="terminal")


urlpatterns = [path("", include(router.urls))]
