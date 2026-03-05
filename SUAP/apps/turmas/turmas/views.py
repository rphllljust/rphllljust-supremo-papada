from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.core.permissions import role_required
from apps.turmas.models import DiarioAcademico, Turma
from apps.usuarios.models import PerfilUsuario
from .forms import DiarioAcademicoForm, DiarioFecharForm, TurmaForm


@role_required(PerfilUsuario.SECRETARIA, PerfilUsuario.COORDENACAO)
def turmas_list(request):
    turmas = Turma.objects.select_related("curso", "professor_responsavel").all().order_by("-ano_letivo", "nome")
    return render(request, "turmas/turmas_list.html", {"turmas": turmas})


@role_required(PerfilUsuario.SECRETARIA)
def turmas_create(request):
    form = TurmaForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Turma cadastrada com sucesso.")
        return redirect("turmas:turmas_list")
    return render(request, "turmas/turmas_form.html", {"form": form, "page_title": "Nova turma"})


@role_required(PerfilUsuario.SECRETARIA)
def turmas_update(request, pk):
    turma = get_object_or_404(Turma, pk=pk)
    form = TurmaForm(request.POST or None, instance=turma)
    if form.is_valid():
        form.save()
        messages.success(request, "Turma atualizada com sucesso.")
        return redirect("turmas:turmas_list")
    return render(request, "turmas/turmas_form.html", {"form": form, "page_title": "Editar turma"})


@role_required(PerfilUsuario.SECRETARIA)
def turmas_delete(request, pk):
    turma = get_object_or_404(Turma, pk=pk)
    if request.method == "POST":
        turma.delete()
        messages.success(request, "Turma removida com sucesso.")
        return redirect("turmas:turmas_list")
    return render(request, "turmas/turmas_confirm_delete.html", {"turma": turma})


# ── Diário Acadêmico ─────────────────────────────────────────────────────────

def diarios_list(request):
    diarios = DiarioAcademico.objects.select_related("turma", "turma__curso", "aberto_por").all()
    return render(request, "turmas/diarios_list.html", {"diarios": diarios})


def diario_create(request, turma_pk):
    turma = get_object_or_404(Turma, pk=turma_pk)
    form = DiarioAcademicoForm(request.POST or None, initial={"turma": turma})
    if form.is_valid():
        diario = form.save(commit=False)
        diario.turma = turma
        diario.aberto_por = request.user
        diario.save()
        messages.success(request, f"Diário acadêmico aberto para {turma}.")
        return redirect("turmas:diarios_list")
    return render(request, "turmas/diario_form.html", {
        "form": form,
        "turma": turma,
        "page_title": "Abrir Diário Acadêmico",
    })


def diario_fechar(request, pk):
    diario = get_object_or_404(DiarioAcademico, pk=pk)
    if diario.status == 'FECHADO':
        messages.warning(request, "Este diário já está fechado.")
        return redirect("turmas:diarios_list")
    form = DiarioFecharForm(request.POST or None, instance=diario)
    if form.is_valid():
        d = form.save(commit=False)
        d.status = 'FECHADO'
        d.data_fechamento = d.data_fechamento or timezone.now().date()
        d.fechado_por = request.user
        d.save()
        messages.success(request, "Diário fechado com sucesso.")
        return redirect("turmas:diarios_list")
    return render(request, "turmas/diario_fechar.html", {
        "form": form,
        "diario": diario,
        "page_title": "Fechar Diário Acadêmico",
    })


def diario_delete(request, pk):
    diario = get_object_or_404(DiarioAcademico, pk=pk)
    if request.method == "POST":
        diario.delete()
        messages.success(request, "Diário removido.")
        return redirect("turmas:diarios_list")
    return render(request, "turmas/diario_confirm_delete.html", {"diario": diario})
