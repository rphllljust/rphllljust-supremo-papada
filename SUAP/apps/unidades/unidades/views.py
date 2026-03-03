from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from apps.unidades.models import Unidade
from .forms import UnidadeForm


def unidades_list(request):
    unidades = Unidade.objects.all().order_by("nome")
    return render(request, "unidades/unidades_list.html", {"unidades": unidades})


def unidades_create(request):
    form = UnidadeForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Unidade cadastrada com sucesso.")
        return redirect("unidades:unidades_list")
    return render(request, "unidades/unidades_form.html", {"form": form, "page_title": "Nova unidade"})


def unidades_update(request, pk):
    unidade = get_object_or_404(Unidade, pk=pk)
    form = UnidadeForm(request.POST or None, instance=unidade)
    if form.is_valid():
        form.save()
        messages.success(request, "Unidade atualizada com sucesso.")
        return redirect("unidades:unidades_list")
    return render(request, "unidades/unidades_form.html", {"form": form, "page_title": "Editar unidade"})


def unidades_delete(request, pk):
    unidade = get_object_or_404(Unidade, pk=pk)
    if request.method == "POST":
        unidade.delete()
        messages.success(request, "Unidade removida com sucesso.")
        return redirect("unidades:unidades_list")
    return render(request, "unidades/unidades_confirm_delete.html", {"unidade": unidade})

