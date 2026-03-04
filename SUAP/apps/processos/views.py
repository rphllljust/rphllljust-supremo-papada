"""UC05 – Abrir e Tramitar Processo/Protocolo"""

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ProcessoForm, TramitacaoForm
from .models import Processo, Tramitacao


def processos_list(request):
    processos = Processo.objects.select_related("requerente").all()
    return render(request, "processos/processos_list.html", {"processos": processos})


def processo_create(request):
    form = ProcessoForm(request.POST or None)
    if form.is_valid():
        processo = form.save()
        messages.success(request, f"Processo aberto. Número: {processo.numero}")
        return redirect("processos:processo_detalhe", pk=processo.pk)
    return render(request, "processos/processo_form.html", {"form": form, "page_title": "Abrir Processo"})


def processo_update(request, pk):
    processo = get_object_or_404(Processo, pk=pk)
    form = ProcessoForm(request.POST or None, instance=processo)
    if form.is_valid():
        form.save()
        messages.success(request, "Processo atualizado.")
        return redirect("processos:processo_detalhe", pk=pk)
    return render(request, "processos/processo_form.html", {"form": form, "page_title": "Editar Processo"})


def processo_detalhe(request, pk):
    processo = get_object_or_404(
        Processo.objects.select_related("requerente").prefetch_related("tramitacoes__responsavel"),
        pk=pk,
    )
    tramitacoes = processo.tramitacoes.all()
    form = TramitacaoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        tramitacao = form.save(commit=False)
        tramitacao.processo = processo
        tramitacao.responsavel = request.user
        tramitacao.save()
        # Atualiza status automaticamente conforme a ação
        acao = tramitacao.acao
        if acao == 'ARQUIVADO':
            processo.status = 'ARQUIVADO'
        elif acao == 'RESPONDIDO':
            processo.status = 'CONCLUIDO'
        elif acao in ('ENCAMINHADO', 'RECEBIDO'):
            processo.status = 'EM_TRAMITACAO'
        processo.save()
        messages.success(request, "Tramitação registrada.")
        return redirect("processos:processo_detalhe", pk=pk)
    return render(request, "processos/processo_detalhe.html", {
        "processo": processo,
        "tramitacoes": tramitacoes,
        "form": form,
    })


def processo_delete(request, pk):
    processo = get_object_or_404(Processo, pk=pk)
    if request.method == "POST":
        processo.delete()
        messages.success(request, "Processo removido.")
        return redirect("processos:processos_list")
    return render(request, "processos/processo_confirm_delete.html", {"processo": processo})
