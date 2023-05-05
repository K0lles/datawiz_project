from django.urls import include, path

urlpatterns = [
    path("products/", include("products.urls")),
    path("receipts/", include("receipts.urls")),
    path("shops/", include("shops.urls")),
    path("__debug__/", include("debug_toolbar.urls")),
]
