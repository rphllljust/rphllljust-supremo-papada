from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from apps.notas.models import Nota
from .forms import NotaForm


def notas_list(request):
    notas = Nota.objects.select_related("matricula", "matricula__aluno", "matricula__turma").all()
    return render(request, "notas/notas_list.html", {"notas": notas})


def notas_create(request):
    form = NotaForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Nota cadastrada com sucesso.")
        return redirect("notas:notas_list")
    return render(request, "notas/notas_form.html", {"form": form, "page_title": "Nova nota"})


def notas_update(request, pk):
    nota = get_object_or_404(Nota, pk=pk)
    form = NotaForm(request.POST or None, instance=nota)
    if form.is_valid():
        form.save()
        messages.success(request, "Nota atualizada com sucesso.")
        return redirect("notas:notas_list")
    return render(request, "notas/notas_form.html", {"form": form, "page_title": "Editar nota"})


def notas_delete(request, pk):
    nota = get_object_or_404(Nota, pk=pk)
    if request.method == "POST":
        nota.delete()
        messages.success(request, "Nota removida com sucesso.")
        return redirect("notas:notas_list")
    return render(request, "notas/notas_confirm_delete.html", {"nota": nota})

