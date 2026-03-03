from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from apps.matriculas.models import Matricula
from .forms import MatriculaForm


def matriculas_list(request):
    matriculas = Matricula.objects.select_related("aluno", "turma", "turma__curso").all().order_by("-id")
    return render(request, "matriculas/matriculas_list.html", {"matriculas": matriculas})


def matriculas_create(request):
    form = MatriculaForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Matricula cadastrada com sucesso.")
        return redirect("matriculas:matriculas_list")
    return render(request, "matriculas/matriculas_form.html", {"form": form, "page_title": "Nova matricula"})


def matriculas_update(request, pk):
    matricula = get_object_or_404(Matricula, pk=pk)
    form = MatriculaForm(request.POST or None, instance=matricula)
    if form.is_valid():
        form.save()
        messages.success(request, "Matricula atualizada com sucesso.")
        return redirect("matriculas:matriculas_list")
    return render(request, "matriculas/matriculas_form.html", {"form": form, "page_title": "Editar matricula"})


def matriculas_delete(request, pk):
    matricula = get_object_or_404(Matricula, pk=pk)
    if request.method == "POST":
        matricula.delete()
        messages.success(request, "Matricula removida com sucesso.")
        return redirect("matriculas:matriculas_list")
    return render(request, "matriculas/matriculas_confirm_delete.html", {"matricula": matricula})

