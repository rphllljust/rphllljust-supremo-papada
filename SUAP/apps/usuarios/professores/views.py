from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from ..models import Usuario
from .forms import ProfessorForm


def professores_list(request):
    professores = Usuario.objects.filter(tipo="PROFESSOR").order_by("first_name", "last_name", "username")
    return render(request, "usuarios/professores_list.html", {"professores": professores})


def professores_create(request):
    form = ProfessorForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Professor cadastrado com sucesso.")
        return redirect("usuarios:professores_list")
    return render(request, "usuarios/professores_form.html", {"form": form, "page_title": "Novo professor"})


def professores_update(request, pk):
    professor = get_object_or_404(Usuario, pk=pk, tipo="PROFESSOR")
    form = ProfessorForm(request.POST or None, instance=professor)
    if form.is_valid():
        form.save()
        messages.success(request, "Professor atualizado com sucesso.")
        return redirect("usuarios:professores_list")
    return render(request, "usuarios/professores_form.html", {"form": form, "page_title": "Editar professor"})


def professores_delete(request, pk):
    professor = get_object_or_404(Usuario, pk=pk, tipo="PROFESSOR")
    if request.method == "POST":
        professor.delete()
        messages.success(request, "Professor removido com sucesso.")
        return redirect("usuarios:professores_list")
    return render(request, "usuarios/professores_confirm_delete.html", {"professor": professor})

