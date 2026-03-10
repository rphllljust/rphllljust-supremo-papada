from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from apps.unidades.models import Unidade


def unidades_list(request):
    unidades = Unidade.objects.all().order_by("nome")
    return render(request, "unidades/unidades_list.html", {"unidades": unidades})


def unidades_create(request):
    messages.warning(request, "As unidades sao fixas e nao podem ser cadastradas manualmente.")
    return redirect("unidades:unidades_list")


def unidades_update(request, pk):
    get_object_or_404(Unidade, pk=pk)
    messages.warning(request, "As unidades sao fixas e nao podem ser editadas.")
    return redirect("unidades:unidades_list")


def unidades_delete(request, pk):
    get_object_or_404(Unidade, pk=pk)
    messages.warning(request, "As unidades sao fixas e nao podem ser removidas.")
    return redirect("unidades:unidades_list")
