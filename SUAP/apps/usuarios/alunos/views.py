from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from apps.core.permissions import role_required
from ..models import PerfilUsuario, Usuario
from .forms import AlunoForm


@role_required(PerfilUsuario.SECRETARIA, PerfilUsuario.COORDENACAO)
def alunos_list(request):
    alunos = Usuario.objects.filter(tipo=PerfilUsuario.ALUNO).order_by("first_name", "last_name", "username")
    return render(request, "usuarios/alunos_list.html", {"alunos": alunos})


@role_required(PerfilUsuario.SECRETARIA)
def alunos_create(request):
    form = AlunoForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Aluno cadastrado com sucesso.")
        return redirect("usuarios:alunos_list")
    return render(request, "usuarios/alunos_form.html", {"form": form, "page_title": "Novo aluno"})


@role_required(PerfilUsuario.SECRETARIA)
def alunos_update(request, pk):
    aluno = get_object_or_404(Usuario, pk=pk, tipo=PerfilUsuario.ALUNO)
    form = AlunoForm(request.POST or None, instance=aluno)
    if form.is_valid():
        form.save()
        messages.success(request, "Aluno atualizado com sucesso.")
        return redirect("usuarios:alunos_list")
    return render(request, "usuarios/alunos_form.html", {"form": form, "page_title": "Editar aluno"})


@role_required(PerfilUsuario.SECRETARIA)
def alunos_delete(request, pk):
    aluno = get_object_or_404(Usuario, pk=pk, tipo=PerfilUsuario.ALUNO)
    if request.method == "POST":
        aluno.delete()
        messages.success(request, "Aluno removido com sucesso.")
        return redirect("usuarios:alunos_list")
    return render(request, "usuarios/alunos_confirm_delete.html", {"aluno": aluno})
