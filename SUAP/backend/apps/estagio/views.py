from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    AcompanhamentoEstagioForm,
    ConvenioForm,
    EncerrarEstagioForm,
    EstagioForm,
    TermoCompromissoForm,
)
from .models import AcompanhamentoEstagio, Convenio, Estagio, TermoCompromisso


# ── Convênios ─────────────────────────────────────────────────────────────────

def convenios_list(request):
    convenios = Convenio.objects.select_related("responsavel_idep").all()
    return render(request, "estagio/convenios_list.html", {"convenios": convenios})


def convenio_create(request):
    form = ConvenioForm(request.POST or None)
    if form.is_valid():
        c = form.save(commit=False)
        if not c.responsavel_idep:
            c.responsavel_idep = request.user
        c.save()
        messages.success(request, f"Convênio registrado: {c.numero_convenio}")
        return redirect("estagio:convenios_list")
    return render(request, "estagio/convenio_form.html", {
        "form": form,
        "page_title": "Novo Convênio de Estágio",
    })


def convenio_update(request, pk):
    convenio = get_object_or_404(Convenio, pk=pk)
    form = ConvenioForm(request.POST or None, instance=convenio)
    if form.is_valid():
        form.save()
        messages.success(request, "Convênio atualizado.")
        return redirect("estagio:convenios_list")
    return render(request, "estagio/convenio_form.html", {
        "form": form,
        "page_title": "Editar Convênio",
    })


def convenio_delete(request, pk):
    convenio = get_object_or_404(Convenio, pk=pk)
    if request.method == "POST":
        convenio.delete()
        messages.success(request, "Convênio removido.")
        return redirect("estagio:convenios_list")
    return render(request, "estagio/convenio_confirm_delete.html", {"convenio": convenio})


# ── Estágios ──────────────────────────────────────────────────────────────────

def estagios_list(request):
    estagios = Estagio.objects.select_related(
        "matricula", "matricula__aluno", "matricula__curso",
        "convenio", "orientador_idep",
    ).all()
    return render(request, "estagio/estagios_list.html", {"estagios": estagios})


def estagio_create(request):
    form = EstagioForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Estágio registrado com sucesso.")
        return redirect("estagio:estagios_list")
    return render(request, "estagio/estagio_form.html", {
        "form": form,
        "page_title": "Registrar Estágio",
    })


def estagio_update(request, pk):
    estagio = get_object_or_404(Estagio, pk=pk)
    form = EstagioForm(request.POST or None, instance=estagio)
    if form.is_valid():
        form.save()
        messages.success(request, "Estágio atualizado.")
        return redirect("estagio:estagios_list")
    return render(request, "estagio/estagio_form.html", {
        "form": form,
        "page_title": "Editar Estágio",
    })


def estagio_encerrar(request, pk):
    estagio = get_object_or_404(Estagio, pk=pk)
    form = EncerrarEstagioForm(request.POST or None, instance=estagio)
    if form.is_valid():
        form.save()
        messages.success(request, "Estágio encerrado e arquivado.")
        return redirect("estagio:estagios_list")
    return render(request, "estagio/estagio_encerrar.html", {
        "form": form,
        "estagio": estagio,
        "page_title": "Encerrar Estágio",
    })


def estagio_delete(request, pk):
    estagio = get_object_or_404(Estagio, pk=pk)
    if request.method == "POST":
        estagio.delete()
        messages.success(request, "Estágio removido.")
        return redirect("estagio:estagios_list")
    return render(request, "estagio/estagio_confirm_delete.html", {"estagio": estagio})


# ── Termos de Compromisso ─────────────────────────────────────────────────────

def termos_list(request):
    termos = TermoCompromisso.objects.select_related("estagio", "estagio__matricula").all()
    return render(request, "estagio/termos_list.html", {"termos": termos})


def termo_create(request):
    form = TermoCompromissoForm(request.POST or None)
    if form.is_valid():
        t = form.save()
        messages.success(request, f"Termo gerado: {t.numero_termo}")
        return redirect("estagio:termos_list")
    return render(request, "estagio/termo_form.html", {
        "form": form,
        "page_title": "Gerar Termo de Compromisso",
    })


def termo_update(request, pk):
    termo = get_object_or_404(TermoCompromisso, pk=pk)
    form = TermoCompromissoForm(request.POST or None, instance=termo)
    if form.is_valid():
        form.save()
        messages.success(request, "Termo atualizado.")
        return redirect("estagio:termos_list")
    return render(request, "estagio/termo_form.html", {
        "form": form,
        "page_title": "Editar Termo de Compromisso",
    })


def termo_delete(request, pk):
    termo = get_object_or_404(TermoCompromisso, pk=pk)
    if request.method == "POST":
        termo.delete()
        messages.success(request, "Termo removido.")
        return redirect("estagio:termos_list")
    return render(request, "estagio/termo_confirm_delete.html", {"termo": termo})


# ── Acompanhamentos ───────────────────────────────────────────────────────────

def acompanhamentos_list(request):
    acompanhamentos = AcompanhamentoEstagio.objects.select_related(
        "estagio", "estagio__matricula", "registrado_por"
    ).all()
    return render(request, "estagio/acompanhamentos_list.html", {"acompanhamentos": acompanhamentos})


def acompanhamento_create(request):
    form = AcompanhamentoEstagioForm(request.POST or None)
    if form.is_valid():
        a = form.save(commit=False)
        a.registrado_por = request.user
        a.save()
        messages.success(request, "Acompanhamento registrado.")
        return redirect("estagio:acompanhamentos_list")
    return render(request, "estagio/acompanhamento_form.html", {
        "form": form,
        "page_title": "Registrar Acompanhamento",
    })


def acompanhamento_delete(request, pk):
    acomp = get_object_or_404(AcompanhamentoEstagio, pk=pk)
    if request.method == "POST":
        acomp.delete()
        messages.success(request, "Acompanhamento removido.")
        return redirect("estagio:acompanhamentos_list")
    return render(request, "estagio/acompanhamento_confirm_delete.html", {"acomp": acomp})
