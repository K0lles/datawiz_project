from django.urls import path

from analytics.views import AnalyticsRetrieveAPIView

urlpatterns = [
    path('', AnalyticsRetrieveAPIView.as_view(), name='analytics'),
    # path('__debug__/', include('debug_toolbar.urls')),
]
