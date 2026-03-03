from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from apps.turmas.models import Turma
from .forms import TurmaForm


def turmas_list(request):
    turmas = Turma.objects.select_related("curso", "professor_responsavel").all().order_by("-ano_letivo", "nome")
    return render(request, "turmas/turmas_list.html", {"turmas": turmas})


def turmas_create(request):
    form = TurmaForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Turma cadastrada com sucesso.")
        return redirect("turmas:turmas_list")
    return render(request, "turmas/turmas_form.html", {"form": form, "page_title": "Nova turma"})


def turmas_update(request, pk):
    turma = get_object_or_404(Turma, pk=pk)
    form = TurmaForm(request.POST or None, instance=turma)
    if form.is_valid():
        form.save()
        messages.success(request, "Turma atualizada com sucesso.")
        return redirect("turmas:turmas_list")
    return render(request, "turmas/turmas_form.html", {"form": form, "page_title": "Editar turma"})


def turmas_delete(request, pk):
    turma = get_object_or_404(Turma, pk=pk)
    if request.method == "POST":
        turma.delete()
        messages.success(request, "Turma removida com sucesso.")
        return redirect("turmas:turmas_list")
    return render(request, "turmas/turmas_confirm_delete.html", {"turma": turma})

