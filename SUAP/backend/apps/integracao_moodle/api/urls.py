from django.urls import path

from .views import (
    MoodleAssignmentsIntegrationAPIView,
    MoodleCategoriesIntegrationAPIView,
    MoodleCategoriesMirrorAPIView,
    MoodleCategoriesSyncAPIView,
    MoodleCoursesIntegrationAPIView,
    MoodleCoursesMirrorAPIView,
    MoodleCoursesSyncAPIView,
    MoodleGradesIntegrationAPIView,
    MoodleCategoriesResetAndSyncAPIView,
    MoodleCategoriesDiffAndSyncAPIView,
    MoodleTestConnectionAPIView,
    MoodleIntegrationConfigAPIView,
    MoodleLocalResetAndSyncAPIView,
)

app_name = "integracao_moodle_api"

urlpatterns = [
    path("categorias/", MoodleCategoriesIntegrationAPIView.as_view(), name="categories-list"),
    path("cursos/", MoodleCoursesIntegrationAPIView.as_view(), name="courses-list"),
    path("espelho/categorias/", MoodleCategoriesMirrorAPIView.as_view(), name="categories-mirror"),
    path("espelho/cursos/", MoodleCoursesMirrorAPIView.as_view(), name="courses-mirror"),
    path("sincronizar/categorias/", MoodleCategoriesSyncAPIView.as_view(), name="categories-sync"),
    path("sincronizar/cursos/", MoodleCoursesSyncAPIView.as_view(), name="courses-sync"),
    path("notas/", MoodleGradesIntegrationAPIView.as_view(), name="grades-actions"),
    path("assignments/", MoodleAssignmentsIntegrationAPIView.as_view(), name="assignments-actions"),
    path('reset-sync-categorias/', MoodleCategoriesResetAndSyncAPIView.as_view(), name='moodle-reset-sync-categorias'),
    path('diff-sync-categorias/', MoodleCategoriesDiffAndSyncAPIView.as_view(), name='moodle-diff-sync-categorias'),
    path('test-connection/', MoodleTestConnectionAPIView.as_view(), name='moodle-test-connection'),
    path('config/', MoodleIntegrationConfigAPIView.as_view(), name='moodle-config'),
    path('reset-local-and-sync/', MoodleLocalResetAndSyncAPIView.as_view(), name='moodle-reset-local-and-sync'),
]