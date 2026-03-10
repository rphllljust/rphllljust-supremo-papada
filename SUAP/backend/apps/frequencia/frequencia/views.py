from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from apps.frequencia.models import Frequencia
from .forms import FrequenciaForm


def frequencia_list(request):
    registros = Frequencia.objects.select_related("matricula", "matricula__aluno", "matricula__turma").all()
    return render(request, "frequencia/frequencia_list.html", {"registros": registros})


def frequencia_create(request):
    form = FrequenciaForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Registro de frequencia cadastrado com sucesso.")
        return redirect("frequencia:frequencia_list")
    return render(request, "frequencia/frequencia_form.html", {"form": form, "page_title": "Nova frequencia"})


def frequencia_update(request, pk):
    registro = get_object_or_404(Frequencia, pk=pk)
    form = FrequenciaForm(request.POST or None, instance=registro)
    if form.is_valid():
        form.save()
        messages.success(request, "Registro de frequencia atualizado com sucesso.")
        return redirect("frequencia:frequencia_list")
    return render(request, "frequencia/frequencia_form.html", {"form": form, "page_title": "Editar frequencia"})


def frequencia_delete(request, pk):
    registro = get_object_or_404(Frequencia, pk=pk)
    if request.method == "POST":
        registro.delete()
        messages.success(request, "Registro de frequencia removido com sucesso.")
        return redirect("frequencia:frequencia_list")
    return render(request, "frequencia/frequencia_confirm_delete.html", {"registro": registro})

