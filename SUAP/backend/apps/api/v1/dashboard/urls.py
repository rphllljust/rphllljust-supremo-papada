from django.urls import path

from .views import DashboardOverviewApiView, DashboardOverviewSheetsCsvApiView, DashboardSheetsModuleApiView


app_name = "api_v1_dashboard"

urlpatterns = [
    path("overview/", DashboardOverviewApiView.as_view(), name="overview"),
    path("overview-sheets.csv", DashboardOverviewSheetsCsvApiView.as_view(), name="overview_sheets_csv"),
    path("sheets/module/", DashboardSheetsModuleApiView.as_view(), name="sheets_module"),
]
