from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from apps.unidades.models import Unidade

from .forms import AtaOficioMemorandoForm, DeclaracaoForm, GuiaTransferenciaForm, HistoricoEscolarForm
from .models import AtaAnexo, AtaOficioMemorando, Declaracao, GuiaTransferencia, HistoricoEscolar
from .historico_digital_views import (
    consulta_publica_historico,
    exportar_historico_pdf,
    exportar_historico_xml,
    validar_historico_publico,
)


def _salvar_anexos_ata(doc, anexos_metadata, files):
    AtaAnexo.objects.filter(ata=doc).delete()
    for index, anexo in enumerate(anexos_metadata or []):
        tipo = (anexo.get("tipo") or "OUTROS").strip() or "OUTROS"
        descricao = (anexo.get("descricao") or "").strip()
        arquivo = files.get(f"anexo_arquivo_{index}")
        AtaAnexo.objects.create(
            ata=doc,
            tipo_anexo=tipo,
            descricao=descricao,
            arquivo=arquivo,
        )


# ── Declaração ────────────────────────────────────────────────────────────────

def declaracao_list(request):
    docs = Declaracao.objects.select_related("matricula", "emitido_por").all()
    return render(request, "documentos/declaracao_list.html", {"docs": docs})


def declaracao_create(request):
    form = DeclaracaoForm(request.POST or None)
    if form.is_valid():
        doc = form.save(commit=False)
        doc.emitido_por = request.user
        doc.save()
        messages.success(request, f"Declaração emitida. Protocolo: {doc.numero_protocolo}")
        return redirect("documentos:declaracao_list")
    return render(request, "documentos/documento_form.html", {"form": form, "page_title": "Emitir Declaração"})


def declaracao_detalhe(request, pk):
    doc = get_object_or_404(Declaracao.objects.select_related("matricula", "emitido_por"), pk=pk)
    return render(request, "documentos/declaracao_detalhe.html", {"doc": doc})


# ── Histórico Escolar ─────────────────────────────────────────────────────────

def historico_list(request):
    docs = HistoricoEscolar.objects.select_related("matricula", "emitido_por").all()
    return render(request, "documentos/historico_list.html", {"docs": docs})


def historico_create(request):
    form = HistoricoEscolarForm(request.POST or None)
    if form.is_valid():
        doc = form.save(commit=False)
        doc.emitido_por = request.user
        doc.save()
        messages.success(request, f"Histórico emitido. Protocolo: {doc.numero_protocolo}")
        return redirect("documentos:historico_list")
    return render(request, "documentos/documento_form.html", {"form": form, "page_title": "Emitir Histórico Escolar"})


def historico_detalhe(request, pk):
    doc = get_object_or_404(HistoricoEscolar.objects.select_related("matricula", "emitido_por"), pk=pk)
    return render(request, "documentos/historico_detalhe.html", {"doc": doc})


# ── Guia de Transferência ─────────────────────────────────────────────────────

def guia_list(request):
    docs = GuiaTransferencia.objects.select_related("matricula", "emitido_por").all()
    return render(request, "documentos/guia_list.html", {"docs": docs})


def guia_create(request):
    form = GuiaTransferenciaForm(request.POST or None)
    if form.is_valid():
        doc = form.save(commit=False)
        doc.emitido_por = request.user
        doc.save()
        messages.success(request, f"Guia emitida. Protocolo: {doc.numero_protocolo}")
        return redirect("documentos:guia_list")
    return render(request, "documentos/documento_form.html", {"form": form, "page_title": "Emitir Guia de Transferência"})


def guia_detalhe(request, pk):
    doc = get_object_or_404(GuiaTransferencia.objects.select_related("matricula", "emitido_por", "transferencia"), pk=pk)
    return render(request, "documentos/guia_detalhe.html", {"doc": doc})


# ── Ata / Ofício / Memorando ──────────────────────────────────────────────────

def ata_list(request):
    docs = AtaOficioMemorando.objects.select_related("emitido_por", "processo").filter(tipo="ATA")
    return render(request, "documentos/ata_list.html", {"docs": docs})


def ata_create(request):
    form = AtaOficioMemorandoForm(request.POST or None, request.FILES or None)
    escola = Unidade.objects.order_by("id").first()

    if form.is_valid():
        doc = form.save(commit=False)
        doc.emitido_por = request.user
        acao = form.cleaned_data.get("acao")
        if acao == "emitir":
            doc.emitir()
            doc.save()
            _salvar_anexos_ata(doc, form.cleaned_data.get("anexos", []), request.FILES)
            messages.success(
                request,
                (
                    f"Ata emitida com sucesso. Numero: {doc.numero_ata} | "
                    f"Protocolo: {doc.numero_protocolo}. A ata agora esta bloqueada para edicao."
                ),
            )
        else:
            doc.situacao = "RASCUNHO"
            doc.save()
            _salvar_anexos_ata(doc, form.cleaned_data.get("anexos", []), request.FILES)
            messages.success(request, f"Rascunho salvo. Protocolo: {doc.numero_protocolo}")
        return redirect("documentos:ata_list")

    context = {
        "form": form,
        "page_title": "Assistente de Ata Escolar Digital",
        "modo": "create",
        "doc": None,
        "escola": escola,
        "initial_anexos": [],
    }
    return render(request, "documentos/ata_form_assistente.html", context)


def ata_update(request, pk):
    doc = get_object_or_404(AtaOficioMemorando, pk=pk)
    if doc.situacao == "EMITIDO":
        messages.warning(request, "Esta ata já foi emitida e está em modo somente leitura.")
        return redirect("documentos:ata_detalhe", pk=doc.pk)

    form = AtaOficioMemorandoForm(request.POST or None, request.FILES or None, instance=doc)
    escola = Unidade.objects.order_by("id").first()

    if form.is_valid():
        doc = form.save(commit=False)
        doc.emitido_por = request.user
        acao = form.cleaned_data.get("acao")
        if acao == "emitir":
            doc.emitir()
            messages.success(
                request,
                (
                    f"Ata emitida com sucesso. Numero: {doc.numero_ata} | "
                    f"Protocolo: {doc.numero_protocolo}. A ata agora esta bloqueada para edicao."
                ),
            )
        else:
            doc.situacao = "RASCUNHO"
            messages.success(request, "Rascunho atualizado com sucesso.")
        doc.save()
        _salvar_anexos_ata(doc, form.cleaned_data.get("anexos", []), request.FILES)
        if acao == "emitir":
            return redirect("documentos:ata_list")
        return redirect("documentos:ata_detalhe", pk=doc.pk)

    context = {
        "form": form,
        "page_title": "Editar Rascunho de Ata Escolar",
        "modo": "edit",
        "doc": doc,
        "escola": escola,
        "initial_anexos": [
            {
                "tipo": anexo.tipo_anexo,
                "descricao": anexo.descricao,
                "arquivo_nome": anexo.arquivo.name.split('/')[-1] if anexo.arquivo else "",
            }
            for anexo in doc.anexos_upload.all()
        ],
    }
    return render(request, "documentos/ata_form_assistente.html", context)


def ata_detalhe(request, pk):
    doc = get_object_or_404(AtaOficioMemorando.objects.select_related("emitido_por", "processo"), pk=pk)
    return render(request, "documentos/ata_detalhe.html", {"doc": doc})
