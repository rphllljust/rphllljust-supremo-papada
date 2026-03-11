from django.urls import path

from .views import DashboardOverviewApiView


app_name = "api_v1_dashboard"

urlpatterns = [
    path("overview/", DashboardOverviewApiView.as_view(), name="overview"),
]