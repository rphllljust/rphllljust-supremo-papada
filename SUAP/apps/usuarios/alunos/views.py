from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from ..models import Usuario
from .forms import AlunoForm


def alunos_list(request):
    alunos = Usuario.objects.filter(tipo="ALUNO").order_by("first_name", "last_name", "username")
    return render(request, "usuarios/alunos_list.html", {"alunos": alunos})


def alunos_create(request):
    form = AlunoForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Aluno cadastrado com sucesso.")
        return redirect("usuarios:alunos_list")
    return render(request, "usuarios/alunos_form.html", {"form": form, "page_title": "Novo aluno"})


def alunos_update(request, pk):
    aluno = get_object_or_404(Usuario, pk=pk, tipo="ALUNO")
    form = AlunoForm(request.POST or None, instance=aluno)
    if form.is_valid():
        form.save()
        messages.success(request, "Aluno atualizado com sucesso.")
        return redirect("usuarios:alunos_list")
    return render(request, "usuarios/alunos_form.html", {"form": form, "page_title": "Editar aluno"})


def alunos_delete(request, pk):
    aluno = get_object_or_404(Usuario, pk=pk, tipo="ALUNO")
    if request.method == "POST":
        aluno.delete()
        messages.success(request, "Aluno removido com sucesso.")
        return redirect("usuarios:alunos_list")
    return render(request, "usuarios/alunos_confirm_delete.html", {"aluno": aluno})

