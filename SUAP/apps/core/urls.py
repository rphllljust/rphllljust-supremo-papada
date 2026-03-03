from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("alunos/", views.students_page, name="students_page"),
    path("turmas/", views.classes_page, name="classes_page"),
    path("matriculas/", views.enrollments_page, name="enrollments_page"),
    path("notas/", views.grades_page, name="grades_page"),
    path("frequencia/", views.attendance_page, name="attendance_page"),
    path("agenda/", views.agenda_page, name="agenda_page"),
    path("modulo/<slug:slug>/", views.module_page, name="module_page"),
]