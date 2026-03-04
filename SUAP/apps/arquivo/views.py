"""UC06 – Arquivar e Gerir Guarda Documental"""

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    ClassificacaoForm,
    EmprestimoDocumentoForm,
    EtapaArquivoObservacaoForm,
    GuardaDocumentalForm,
    IndexacaoForm,
    PrazoGuardaForm,
    TermoEliminacaoForm,
)
from .models import (
    EmprestimoDocumento,
    EtapaFluxoArquivo,
    FluxoArquivo,
    GuardaDocumental,
    TermoEliminacao,
)


def arquivo_list(request):
    registros = GuardaDocumental.objects.select_related("matricula", "processo", "responsavel").all()
    return render(request, "arquivo/arquivo_list.html", {"registros": registros})


def arquivo_create(request):
    form = GuardaDocumentalForm(request.POST or None)
    if form.is_valid():
        guarda = form.save(commit=False)
        guarda.responsavel = request.user
        guarda.save()
        messages.success(request, f"Documento arquivado. Registro: {guarda.numero_registro}")
        return redirect("arquivo:arquivo_list")
    return render(request, "arquivo/arquivo_form.html", {"form": form, "page_title": "Arquivar Documento"})


def arquivo_update(request, pk):
    guarda = get_object_or_404(GuardaDocumental, pk=pk)
    form = GuardaDocumentalForm(request.POST or None, instance=guarda)
    if form.is_valid():
        form.save()
        messages.success(request, "Registro atualizado.")
        return redirect("arquivo:arquivo_list")
    return render(request, "arquivo/arquivo_form.html", {"form": form, "page_title": "Editar Registro"})


def arquivo_delete(request, pk):
    guarda = get_object_or_404(GuardaDocumental, pk=pk)
    if request.method == "POST":
        guarda.delete()
        messages.success(request, "Registro removido.")
        return redirect("arquivo:arquivo_list")
    return render(request, "arquivo/arquivo_confirm_delete.html", {"guarda": guarda})


def emprestimo_create(request, guarda_pk):
    guarda = get_object_or_404(GuardaDocumental, pk=guarda_pk)
    form = EmprestimoDocumentoForm(request.POST or None)
    if form.is_valid():
        emp = form.save(commit=False)
        emp.guarda = guarda
        emp.save()
        guarda.status = 'EMPRESTADO'
        guarda.save()
        messages.success(request, "Empréstimo registrado.")
        return redirect("arquivo:arquivo_list")
    return render(request, "arquivo/emprestimo_form.html", {
        "form": form,
        "guarda": guarda,
        "page_title": "Registrar Empréstimo",
    })


def emprestimo_update(request, pk):
    emp = get_object_or_404(EmprestimoDocumento, pk=pk)
    form = EmprestimoDocumentoForm(request.POST or None, instance=emp)
    if form.is_valid():
        form.save()
        if emp.devolvido:
            emp.guarda.status = 'ATIVO'
            emp.guarda.save()
        messages.success(request, "Empréstimo atualizado.")
        return redirect("arquivo:arquivo_list")
    return render(request, "arquivo/emprestimo_form.html", {
        "form": form,
        "guarda": emp.guarda,
        "page_title": "Editar Empréstimo",
    })


# ── P04 – Fluxo de Arquivo Escolar e Prazos ──────────────────────────────────

def fluxo_arquivo_list(request):
    fluxos = FluxoArquivo.objects.select_related(
        "guarda", "guarda__responsavel"
    ).all()
    return render(request, "arquivo/fluxo_arquivo_list.html", {"fluxos": fluxos})


def fluxo_arquivo_create(request, guarda_pk):
    """Inicia o fluxo P04 a partir de uma GuardaDocumental existente."""
    guarda = get_object_or_404(GuardaDocumental, pk=guarda_pk)
    if guarda.status == 'ELIMINADO':
        messages.error(request, "Este documento já foi eliminado.")
        return redirect("arquivo:arquivo_list")

    form_class = ClassificacaoForm
    form = form_class(request.POST or None, instance=guarda)
    if request.method == "POST" and form.is_valid():
        form.save()
        fluxo = FluxoArquivo.objects.create(
            guarda=guarda,
            observacoes=request.POST.get("observacoes", ""),
        )
        EtapaFluxoArquivo.objects.create(
            fluxo=fluxo,
            etapa='CLASSIFICADO',
            responsavel=request.user,
            observacao=f"Documento classificado como: {guarda.get_tipo_documento_display()}",
        )
        messages.success(request, f"Fluxo P04 iniciado para {guarda.numero_registro}.")
        return redirect("arquivo:fluxo_arquivo_detalhe", pk=fluxo.pk)
    return render(request, "arquivo/fluxo_arquivo_form.html", {
        "form": form,
        "guarda": guarda,
        "page_title": "P04 – Classificar Documento",
    })


def fluxo_arquivo_detalhe(request, pk):
    fluxo = get_object_or_404(
        FluxoArquivo.objects.select_related("guarda", "guarda__responsavel"),
        pk=pk,
    )
    log = fluxo.log_etapas.select_related("responsavel").all()
    etapas = fluxo.etapas_info()
    ctx = {
        "fluxo": fluxo,
        "etapas": etapas,
        "log": log,
        "form_obs": EtapaArquivoObservacaoForm(),
    }

    etapa = fluxo.etapa_atual
    if etapa == 'INDEXADO':
        ctx["form_index"] = IndexacaoForm(instance=fluxo.guarda)
    elif etapa == 'PRAZO_APLICADO':
        ctx["form_prazo"] = PrazoGuardaForm(instance=fluxo.guarda)
    elif etapa == 'ELIMINADO':
        termo = getattr(fluxo, 'termo_eliminacao', None)
        ctx["termo"] = termo
        if not termo:
            ctx["form_termo"] = TermoEliminacaoForm()

    return render(request, "arquivo/fluxo_arquivo_detalhe.html", ctx)


def fluxo_arquivo_avancar(request, pk):
    if request.method != "POST":
        return redirect("arquivo:fluxo_arquivo_detalhe", pk=pk)

    fluxo = get_object_or_404(FluxoArquivo, pk=pk)
    etapa_atual = fluxo.etapa_atual
    obs = request.POST.get("observacao", "")

    # ── Etapa 1→2: Indexar / Localizar ───────────────────────────────────────
    if etapa_atual == 'CLASSIFICADO':
        form = IndexacaoForm(request.POST, instance=fluxo.guarda)
        if form.is_valid():
            form.save()
            fluxo.avancar('INDEXADO')
            obs = f"Localização: {fluxo.guarda.localizacao or fluxo.guarda.numero_caixa}"
        else:
            messages.error(request, "Informe a localização do documento.")
            return redirect("arquivo:fluxo_arquivo_detalhe", pk=pk)

    # ── Etapa 2→3: Aplicar Prazo de Guarda ───────────────────────────────────
    elif etapa_atual == 'INDEXADO':
        form = PrazoGuardaForm(request.POST, instance=fluxo.guarda)
        if form.is_valid():
            form.save()
            fluxo.avancar('PRAZO_APLICADO')
            obs = f"Prazo de guarda: {fluxo.guarda.data_eliminacao_prevista:%d/%m/%Y}"
        else:
            messages.error(request, "Informe a data de eliminação prevista.")
            return redirect("arquivo:fluxo_arquivo_detalhe", pk=pk)

    # ── Etapa 3→4: Eliminar + Gerar Termo ────────────────────────────────────
    elif etapa_atual == 'PRAZO_APLICADO':
        form = TermoEliminacaoForm(request.POST)
        if form.is_valid():
            termo = form.save(commit=False)
            termo.fluxo = fluxo
            termo.autorizado_por = termo.autorizado_por or request.user
            termo.save()
            # Marca a guarda como eliminada
            fluxo.guarda.status = 'ELIMINADO'
            fluxo.guarda.save()
            fluxo.avancar('ELIMINADO')
            obs = f"Termo de eliminação emitido: {termo.numero}"
        else:
            messages.error(request, "Corrija os dados do termo de eliminação.")
            return redirect("arquivo:fluxo_arquivo_detalhe", pk=pk)

    EtapaFluxoArquivo.objects.create(
        fluxo=fluxo,
        etapa=fluxo.etapa_atual,
        responsavel=request.user,
        observacao=obs,
    )
    messages.success(request, f"Etapa: {fluxo.get_etapa_atual_display()}")
    return redirect("arquivo:fluxo_arquivo_detalhe", pk=pk)


def termo_eliminacao_detalhe(request, pk):
    """Visualização/impressão do Termo de Eliminação."""
    termo = get_object_or_404(
        TermoEliminacao.objects.select_related(
            "fluxo", "fluxo__guarda", "fluxo__guarda__matricula",
            "fluxo__guarda__processo", "autorizado_por",
        ),
        pk=pk,
    )
    return render(request, "arquivo/termo_eliminacao_detalhe.html", {"termo": termo})
