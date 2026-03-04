from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from apps.cursos.models import Curso
from .forms import CursoForm


def cursos_list(request):
    cursos = Curso.objects.select_related("unidade").all().order_by("nome")
    return render(request, "cursos/cursos_list.html", {"cursos": cursos})


def cursos_create(request):
    form = CursoForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Curso cadastrado com sucesso.")
        return redirect("cursos:cursos_list")
    return render(request, "cursos/cursos_form.html", {"form": form, "page_title": "Novo curso"})


def cursos_update(request, pk):
    curso = get_object_or_404(Curso, pk=pk)
    form = CursoForm(request.POST or None, instance=curso)
    if form.is_valid():
        form.save()
        messages.success(request, "Curso atualizado com sucesso.")
        return redirect("cursos:cursos_list")
    return render(request, "cursos/cursos_form.html", {"form": form, "page_title": "Editar curso"})


def cursos_delete(request, pk):
    curso = get_object_or_404(Curso, pk=pk)
    if request.method == "POST":
        curso.delete()
        messages.success(request, "Curso removido com sucesso.")
        return redirect("cursos:cursos_list")
    return render(request, "cursos/cursos_confirm_delete.html", {"curso": curso})

