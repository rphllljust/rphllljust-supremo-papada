from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AtaOficioMemorandoForm, DeclaracaoForm, GuiaTransferenciaForm, HistoricoEscolarForm
from .models import AtaOficioMemorando, Declaracao, GuiaTransferencia, HistoricoEscolar


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
    docs = AtaOficioMemorando.objects.select_related("emitido_por", "processo").all()
    return render(request, "documentos/ata_list.html", {"docs": docs})


def ata_create(request):
    form = AtaOficioMemorandoForm(request.POST or None)
    if form.is_valid():
        doc = form.save(commit=False)
        doc.emitido_por = request.user
        doc.save()
        messages.success(request, f"Documento emitido. Protocolo: {doc.numero_protocolo}")
        return redirect("documentos:ata_list")
    return render(request, "documentos/documento_form.html", {"form": form, "page_title": "Emitir Ata / Ofício / Memorando"})


def ata_detalhe(request, pk):
    doc = get_object_or_404(AtaOficioMemorando.objects.select_related("emitido_por", "processo"), pk=pk)
    return render(request, "documentos/ata_detalhe.html", {"doc": doc})
