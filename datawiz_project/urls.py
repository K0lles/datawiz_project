from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("api/schema/", SpectacularAPIView.as_view(), name='schema'),
    path("api/schema/swagger-ui/", SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path("products/", include("products.urls")),
    path("receipts/", include("receipts.urls")),
    path("shops/", include("shops.urls")),
    path("analytics/", include('analytics.urls')),
    path("__debug__/", include("debug_toolbar.urls")),
]
