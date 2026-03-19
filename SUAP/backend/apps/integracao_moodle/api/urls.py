from django.urls import path

from .views import (
    MoodleAssignmentsIntegrationAPIView,
    MoodleCategoriesIntegrationAPIView,
    MoodleCoursesIntegrationAPIView,
    MoodleGradesIntegrationAPIView,
    MoodleCategoriesResetAndSyncAPIView,
)

app_name = "integracao_moodle_api"

urlpatterns = [
    path("categorias/", MoodleCategoriesIntegrationAPIView.as_view(), name="categories-list"),
    path("cursos/", MoodleCoursesIntegrationAPIView.as_view(), name="courses-list"),
    path("notas/", MoodleGradesIntegrationAPIView.as_view(), name="grades-actions"),
    path("assignments/", MoodleAssignmentsIntegrationAPIView.as_view(), name="assignments-actions"),
    path('reset-sync-categorias/', MoodleCategoriesResetAndSyncAPIView.as_view(), name='moodle-reset-sync-categorias'),
]