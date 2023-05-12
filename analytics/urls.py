from django.urls import path

from analytics.views import AnalyticsRetrieveAPIView

urlpatterns = [
    path('', AnalyticsRetrieveAPIView.as_view(), name='analytics')
]
