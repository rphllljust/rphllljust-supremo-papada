from django.urls import path

from .views import AtendimentoPedagogicoDetailApiView, AtendimentoPedagogicoListApiView

app_name = "api_v1_pedagogia"

urlpatterns = [
    path("", AtendimentoPedagogicoListApiView.as_view(), name="list"),
    path("<int:pk>/", AtendimentoPedagogicoDetailApiView.as_view(), name="detail"),
]
