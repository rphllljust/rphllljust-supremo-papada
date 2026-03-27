from datetime import date

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    CandidatoForm,
    DocumentoInscricaoForm,
    InscricaoForm,
    InscricaoValidarForm,
    ProcessoSeletivoForm,
    PublicacaoInscricaoForm,
    RecursoDecisaoForm,
    RecursoInscricaoForm,
)
from .models import (
    Candidato,
    DocumentoInscricao,
    Inscricao,
    ProcessoSeletivo,
    PublicacaoInscricao,
    RecursoInscricao,
)


# ── Publicação de Inscrição ───────────────────────────────────────────────────

def publicacoes_list(request):
    publicacoes = PublicacaoInscricao.objects.select_related("curso", "publicado_por").all()
    return render(request, "inscricoes/publicacoes_list.html", {"publicacoes": publicacoes})


def publicacao_create(request):
    form = PublicacaoInscricaoForm(request.POST or None)
    if form.is_valid():
        pub = form.save(commit=False)
        pub.publicado_por = request.user
        pub.save()
        messages.success(request, "Publicação de inscrição criada.")
        return redirect("inscricoes:publicacoes_list")
    return render(request, "inscricoes/publicacao_form.html", {
        "form": form,
        "page_title": "Nova Publicação de Inscrição",
    })


def publicacao_update(request, pk):
    pub = get_object_or_404(PublicacaoInscricao, pk=pk)
    form = PublicacaoInscricaoForm(request.POST or None, instance=pub)
    if form.is_valid():
        form.save()
        messages.success(request, "Publicação atualizada.")
        return redirect("inscricoes:publicacoes_list")
    return render(request, "inscricoes/publicacao_form.html", {
        "form": form,
        "page_title": "Editar Publicação",
    })


def publicacao_delete(request, pk):
    pub = get_object_or_404(PublicacaoInscricao, pk=pk)
    if request.method == "POST":
        pub.delete()
        messages.success(request, "Publicação removida.")
        return redirect("inscricoes:publicacoes_list")
    return render(request, "inscricoes/publicacao_confirm_delete.html", {"pub": pub})


# ── Inscrições ────────────────────────────────────────────────────────────────

def inscricoes_list(request):
    inscricoes = Inscricao.objects.select_related("publicacao", "publicacao__curso").all()
    return render(request, "inscricoes/inscricoes_list.html", {"inscricoes": inscricoes})


def inscricao_create(request):
    form = InscricaoForm(request.POST or None)
    if form.is_valid():
        ins = form.save()
        messages.success(request, f"Inscrição registrada: {ins.numero_inscricao}")
        return redirect("inscricoes:inscricao_documentos", pk=ins.pk)
    return render(request, "inscricoes/inscricao_form.html", {
        "form": form,
        "page_title": "Registrar Inscrição",
    })


def inscricao_validar(request, pk):
    ins = get_object_or_404(Inscricao, pk=pk)
    form = InscricaoValidarForm(request.POST or None, instance=ins)
    if form.is_valid():
        form.save()
        messages.success(request, "Status da inscrição atualizado.")
        return redirect("inscricoes:inscricoes_list")
    return render(request, "inscricoes/inscricao_validar.html", {
        "form": form,
        "inscricao": ins,
        "page_title": "Validar Inscrição",
    })


def inscricao_delete(request, pk):
    ins = get_object_or_404(Inscricao, pk=pk)
    if request.method == "POST":
        ins.delete()
        messages.success(request, "Inscrição removida.")
        return redirect("inscricoes:inscricoes_list")
    return render(request, "inscricoes/inscricao_confirm_delete.html", {"inscricao": ins})


def inscricao_documentos(request, pk):
    ins = get_object_or_404(Inscricao, pk=pk)
    documentos = ins.documentos.all()
    form = DocumentoInscricaoForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        doc = form.save(commit=False)
        doc.inscricao = ins
        if doc.status_validacao != "PENDENTE":
            doc.validado_por = request.user if request.user.is_authenticated else None
            doc.data_validacao = date.today()
        doc.save()
        messages.success(request, "Documento registrado.")
        return redirect("inscricoes:inscricao_documentos", pk=pk)
    return render(request, "inscricoes/inscricao_documentos.html", {
        "inscricao": ins,
        "documentos": documentos,
        "form": form,
    })


# ── Processo Seletivo ─────────────────────────────────────────────────────────

def seletivos_list(request):
    seletivos = ProcessoSeletivo.objects.select_related("publicacao", "publicacao__curso", "responsavel").all()
    return render(request, "inscricoes/seletivos_list.html", {"seletivos": seletivos})


def seletivo_create(request):
    form = ProcessoSeletivoForm(request.POST or None)
    if form.is_valid():
        s = form.save(commit=False)
        if not s.responsavel:
            s.responsavel = request.user
        s.save()
        messages.success(request, "Processo seletivo criado.")
        return redirect("inscricoes:seletivos_list")
    return render(request, "inscricoes/seletivo_form.html", {
        "form": form,
        "page_title": "Novo Processo Seletivo",
    })


def seletivo_update(request, pk):
    seletivo = get_object_or_404(ProcessoSeletivo, pk=pk)
    form = ProcessoSeletivoForm(request.POST or None, instance=seletivo)
    if form.is_valid():
        form.save()
        messages.success(request, "Processo seletivo atualizado.")
        return redirect("inscricoes:seletivos_list")
    return render(request, "inscricoes/seletivo_form.html", {
        "form": form,
        "page_title": "Editar Processo Seletivo",
    })


def seletivo_delete(request, pk):
    seletivo = get_object_or_404(ProcessoSeletivo, pk=pk)
    if request.method == "POST":
        seletivo.delete()
        messages.success(request, "Processo seletivo removido.")
        return redirect("inscricoes:seletivos_list")
    return render(request, "inscricoes/seletivo_confirm_delete.html", {"seletivo": seletivo})


# ── Candidatos ────────────────────────────────────────────────────────────────

def candidatos_list(request):
    candidatos = Candidato.objects.select_related(
        "processo", "processo__publicacao", "inscricao"
    ).all().order_by("processo", "classificacao")
    return render(request, "inscricoes/candidatos_list.html", {"candidatos": candidatos})


def candidato_create(request):
    form = CandidatoForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Candidato registrado e convocado.")
        return redirect("inscricoes:candidatos_list")
    return render(request, "inscricoes/candidato_form.html", {
        "form": form,
        "page_title": "Registrar Candidato / Convocação",
    })


def candidato_update(request, pk):
    candidato = get_object_or_404(Candidato, pk=pk)
    form = CandidatoForm(request.POST or None, instance=candidato)
    if form.is_valid():
        form.save()
        messages.success(request, "Candidato atualizado.")
        return redirect("inscricoes:candidatos_list")
    return render(request, "inscricoes/candidato_form.html", {
        "form": form,
        "page_title": "Editar Candidato",
    })


def candidato_delete(request, pk):
    candidato = get_object_or_404(Candidato, pk=pk)
    if request.method == "POST":
        candidato.delete()
        messages.success(request, "Candidato removido.")
        return redirect("inscricoes:candidatos_list")
    return render(request, "inscricoes/candidato_confirm_delete.html", {"candidato": candidato})


# ── Recursos ──────────────────────────────────────────────────────────────────

def recursos_list(request):
    recursos = RecursoInscricao.objects.select_related(
        "candidato", "candidato__inscricao", "candidato__processo", "decidido_por"
    ).all()
    return render(request, "inscricoes/recursos_list.html", {"recursos": recursos})


def recurso_create(request):
    form = RecursoInscricaoForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Recurso registrado.")
        return redirect("inscricoes:recursos_list")
    return render(request, "inscricoes/recurso_form.html", {
        "form": form,
        "page_title": "Registrar Recurso",
    })


def recurso_decisao(request, pk):
    recurso = get_object_or_404(RecursoInscricao, pk=pk)
    form = RecursoDecisaoForm(request.POST or None, instance=recurso)
    if form.is_valid():
        dec = form.save(commit=False)
        dec.decidido_por = request.user
        dec.save()
        messages.success(request, "Decisão registrada.")
        return redirect("inscricoes:recursos_list")
    return render(request, "inscricoes/recurso_decisao.html", {
        "form": form,
        "recurso": recurso,
        "page_title": "Decidir Recurso",
    })


def recurso_delete(request, pk):
    recurso = get_object_or_404(RecursoInscricao, pk=pk)
    if request.method == "POST":
        recurso.delete()
        messages.success(request, "Recurso removido.")
        return redirect("inscricoes:recursos_list")
    return render(request, "inscricoes/recurso_confirm_delete.html", {"recurso": recurso})
