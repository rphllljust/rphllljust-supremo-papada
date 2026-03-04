from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from apps.matriculas.models import (
    ConsolidacaoAcademica,
    DocumentoEmitido,
    DocumentoMatricula,
    EtapaFluxo,
    EtapaFluxoEmissao,
    EtapaFluxoTransferencia,
    FluxoEmissaoDocumento,
    FluxoMatricula,
    FluxoTransferencia,
    Matricula,
    PendenciaDocumental,
    RegraAcademica,
    Transferencia,
)
from .forms import (
    ConsolidacaoObservacaoForm,
    DocumentoEmitidoForm,
    DocumentoMatriculaForm,
    EntregaDocumentoForm,
    EtapaEmissaoObservacaoForm,
    EtapaObservacaoForm,
    EtapaTransferenciaObservacaoForm,
    FluxoEmissaoIniciarForm,
    FluxoEnturmarForm,
    FluxoMatriculaIniciarForm,
    FluxoTransferenciaIniciarForm,
    MatriculaForm,
    PendenciaDocumentalForm,
    PendenciaFluxoForm,
    RegraAcademicaForm,
    TransferenciaFluxoForm,
    TransferenciaForm,
    ValidarDocumentoForm,
    ValidarEntregaP02Form,
)


# ── Matrícula (UC01 – Realizar Matrícula/Rematrícula) ────────────────────────

def matriculas_list(request):
    matriculas = Matricula.objects.select_related("aluno", "curso", "turma", "turma__curso").all().order_by("-id")
    return render(request, "matriculas/matriculas_list.html", {"matriculas": matriculas})


def matriculas_create(request):
    form = MatriculaForm(request.POST or None)
    if form.is_valid():
        matricula = form.save()
        messages.success(request, "Matrícula registrada com sucesso.")
        return redirect("matriculas:matricula_documentos", pk=matricula.pk)
    return render(request, "matriculas/matriculas_form_atomic.html", {"form": form, "page_title": "Nova matrícula"})


def matriculas_update(request, pk):
    matricula = get_object_or_404(Matricula, pk=pk)
    form = MatriculaForm(request.POST or None, instance=matricula)
    if form.is_valid():
        form.save()
        messages.success(request, "Matrícula atualizada com sucesso.")
        return redirect("matriculas:matriculas_list")
    return render(request, "matriculas/matriculas_form_atomic.html", {"form": form, "page_title": "Editar matrícula"})


def matriculas_delete(request, pk):
    matricula = get_object_or_404(Matricula, pk=pk)
    if request.method == "POST":
        matricula.delete()
        messages.success(request, "Matrícula removida com sucesso.")
        return redirect("matriculas:matriculas_list")
    return render(request, "matriculas/matriculas_confirm_delete.html", {"matricula": matricula})


# ── Documentos (UC01 – include: Conferir Documentação) ──────────────────────

def matricula_documentos(request, pk):
    """UC01 – include: Conferir Documentação / Registrar no Sistema"""
    matricula = get_object_or_404(Matricula, pk=pk)
    documentos = matricula.documentos.all()
    return render(request, "matriculas/matricula_documentos.html", {
        "matricula": matricula,
        "documentos": documentos,
    })


def documento_create(request, matricula_pk):
    matricula = get_object_or_404(Matricula, pk=matricula_pk)
    form = DocumentoMatriculaForm(request.POST or None)
    if form.is_valid():
        doc = form.save(commit=False)
        doc.matricula = matricula
        doc.save()
        messages.success(request, "Documento registrado com sucesso.")
        return redirect("matriculas:matricula_documentos", pk=matricula_pk)
    return render(request, "matriculas/documento_form.html", {
        "form": form,
        "matricula": matricula,
        "page_title": "Adicionar Documento",
    })


def documento_update(request, pk):
    documento = get_object_or_404(DocumentoMatricula, pk=pk)
    form = DocumentoMatriculaForm(request.POST or None, instance=documento)
    if form.is_valid():
        form.save()
        messages.success(request, "Documento atualizado com sucesso.")
        return redirect("matriculas:matricula_documentos", pk=documento.matricula_id)
    return render(request, "matriculas/documento_form.html", {
        "form": form,
        "matricula": documento.matricula,
        "page_title": "Editar Documento",
    })


def documento_delete(request, pk):
    documento = get_object_or_404(DocumentoMatricula, pk=pk)
    matricula_pk = documento.matricula_id
    if request.method == "POST":
        documento.delete()
        messages.success(request, "Documento removido.")
        return redirect("matriculas:matricula_documentos", pk=matricula_pk)
    return render(request, "matriculas/documento_confirm_delete.html", {"documento": documento})


# ── Pendências (UC01 – extend: Abrir Pendência Documental) ──────────────────

def matricula_pendencias(request, pk):
    """UC01 – extend: Abrir Pendência Documental"""
    matricula = get_object_or_404(Matricula, pk=pk)
    pendencias = matricula.pendencias.all()
    return render(request, "matriculas/matricula_pendencias.html", {
        "matricula": matricula,
        "pendencias": pendencias,
    })


def pendencia_create(request, matricula_pk):
    matricula = get_object_or_404(Matricula, pk=matricula_pk)
    form = PendenciaDocumentalForm(request.POST or None)
    if form.is_valid():
        pendencia = form.save(commit=False)
        pendencia.matricula = matricula
        pendencia.save()
        messages.success(request, "Pendência aberta com sucesso.")
        return redirect("matriculas:matricula_pendencias", pk=matricula_pk)
    return render(request, "matriculas/pendencia_form.html", {
        "form": form,
        "matricula": matricula,
        "page_title": "Abrir Pendência Documental",
    })


def pendencia_update(request, pk):
    pendencia = get_object_or_404(PendenciaDocumental, pk=pk)
    form = PendenciaDocumentalForm(request.POST or None, instance=pendencia)
    if form.is_valid():
        form.save()
        messages.success(request, "Pendência atualizada com sucesso.")
        return redirect("matriculas:matricula_pendencias", pk=pendencia.matricula_id)
    return render(request, "matriculas/pendencia_form.html", {
        "form": form,
        "matricula": pendencia.matricula,
        "page_title": "Editar Pendência",
    })


def pendencia_delete(request, pk):
    pendencia = get_object_or_404(PendenciaDocumental, pk=pk)
    matricula_pk = pendencia.matricula_id
    if request.method == "POST":
        pendencia.delete()
        messages.success(request, "Pendência removida.")
        return redirect("matriculas:matricula_pendencias", pk=matricula_pk)
    return render(request, "matriculas/pendencia_confirm_delete.html", {"pendencia": pendencia})


# ── Documentos Emitidos (UC02 – Emitir Documentos) ──────────────────────────

def documentos_emitidos_list(request):
    """Lista geral de todos os documentos emitidos."""
    documentos = (
        DocumentoEmitido.objects
        .select_related("matricula", "matricula__aluno", "matricula__curso", "validado_por")
        .all()
    )
    return render(request, "matriculas/documentos_emitidos_list.html", {"documentos": documentos})


def matricula_documentos_emitidos(request, pk):
    """Documentos emitidos de uma matrícula específica."""
    matricula = get_object_or_404(Matricula, pk=pk)
    documentos = matricula.documentos_emitidos.select_related("validado_por").all()
    return render(request, "matriculas/matricula_documentos_emitidos.html", {
        "matricula": matricula,
        "documentos": documentos,
    })


def documento_emitido_create(request, matricula_pk):
    matricula = get_object_or_404(Matricula, pk=matricula_pk)
    form = DocumentoEmitidoForm(request.POST or None)
    form._matricula = matricula
    if form.is_valid():
        doc = form.save(commit=False)
        doc.matricula = matricula
        doc.save()
        messages.success(request, f"Documento emitido. Protocolo: {doc.numero_protocolo}")
        return redirect("matriculas:documento_emitido_detalhe", pk=doc.pk)
    return render(request, "matriculas/documento_emitido_form.html", {
        "form": form,
        "matricula": matricula,
        "page_title": "Emitir Documento",
    })


def documento_emitido_detalhe(request, pk):
    """Visualização/impressão do documento emitido."""
    doc = get_object_or_404(
        DocumentoEmitido.objects.select_related(
            "matricula", "matricula__aluno", "matricula__curso",
            "matricula__turma", "validado_por"
        ),
        pk=pk,
    )
    # Dados extras úteis para impressão
    frequencias = doc.matricula.frequencias.all()
    total = frequencias.count()
    presencas = frequencias.filter(presente=True).count()
    percentual = round((presencas / total * 100), 1) if total else 0

    notas = doc.matricula.notas.all()

    return render(request, "matriculas/documento_emitido_detalhe.html", {
        "doc": doc,
        "total_aulas": total,
        "presencas": presencas,
        "percentual_frequencia": percentual,
        "notas": notas,
    })


def documento_emitido_validar(request, pk):
    """UC02 – include: Assinar/Validar"""
    doc = get_object_or_404(DocumentoEmitido, pk=pk)
    form = ValidarDocumentoForm(request.POST or None, instance=doc)
    if form.is_valid():
        validado = form.save(commit=False)
        if validado.validado:
            validado.validado_por = request.user
        else:
            validado.validado_por = None
            validado.data_validacao = None
        validado.save()
        messages.success(request, "Documento validado com sucesso.")
        return redirect("matriculas:documento_emitido_detalhe", pk=pk)
    return render(request, "matriculas/documento_emitido_validar.html", {
        "form": form,
        "doc": doc,
        "page_title": "Assinar / Validar Documento",
    })


def documento_emitido_entrega(request, pk):
    """UC02 – include: Registrar Entrega (Protocolo)"""
    doc = get_object_or_404(DocumentoEmitido, pk=pk)
    form = EntregaDocumentoForm(request.POST or None, instance=doc)
    if form.is_valid():
        form.save()
        messages.success(request, "Entrega registrada com sucesso.")
        return redirect("matriculas:documento_emitido_detalhe", pk=pk)
    return render(request, "matriculas/documento_emitido_entrega.html", {
        "form": form,
        "doc": doc,
        "page_title": "Registrar Entrega (Protocolo)",
    })


def documento_emitido_delete(request, pk):
    doc = get_object_or_404(DocumentoEmitido, pk=pk)
    matricula_pk = doc.matricula_id
    if request.method == "POST":
        doc.delete()
        messages.success(request, "Documento removido.")
        return redirect("matriculas:matricula_documentos_emitidos", pk=matricula_pk)
    return render(request, "matriculas/documento_emitido_confirm_delete.html", {"doc": doc})


# ── Transferência (UC03) ─────────────────────────────────────────────────────

def transferencias_list(request):
    transferencias = Transferencia.objects.select_related("matricula", "matricula__aluno", "matricula__curso").all()
    return render(request, "matriculas/transferencias_list.html", {"transferencias": transferencias})


def transferencia_create(request, matricula_pk):
    matricula = get_object_or_404(Matricula, pk=matricula_pk)
    form = TransferenciaForm(request.POST or None)
    if form.is_valid():
        t = form.save(commit=False)
        t.matricula = matricula
        t.save()
        messages.success(request, "Transferência registrada com sucesso.")
        return redirect("matriculas:transferencias_list")
    return render(request, "matriculas/transferencia_form.html", {
        "form": form,
        "matricula": matricula,
        "page_title": "Registrar Transferência",
    })


def transferencia_update(request, pk):
    transferencia = get_object_or_404(Transferencia, pk=pk)
    form = TransferenciaForm(request.POST or None, instance=transferencia)
    if form.is_valid():
        form.save()
        messages.success(request, "Transferência atualizada.")
        return redirect("matriculas:transferencias_list")
    return render(request, "matriculas/transferencia_form.html", {
        "form": form,
        "matricula": transferencia.matricula,
        "page_title": "Editar Transferência",
    })


def transferencia_delete(request, pk):
    transferencia = get_object_or_404(Transferencia, pk=pk)
    if request.method == "POST":
        transferencia.delete()
        messages.success(request, "Transferência removida.")
        return redirect("matriculas:transferencias_list")
    return render(request, "matriculas/transferencia_confirm_delete.html", {"transferencia": transferencia})


# ── Regras Acadêmicas e Consolidação (UC04) ──────────────────────────────────

def regras_list(request):
    regras = RegraAcademica.objects.select_related("curso").all()
    return render(request, "matriculas/regras_list.html", {"regras": regras})


def regra_create(request):
    form = RegraAcademicaForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Regra acadêmica configurada.")
        return redirect("matriculas:regras_list")
    return render(request, "matriculas/regra_form.html", {"form": form, "page_title": "Nova Regra Acadêmica"})


def regra_update(request, pk):
    regra = get_object_or_404(RegraAcademica, pk=pk)
    form = RegraAcademicaForm(request.POST or None, instance=regra)
    if form.is_valid():
        form.save()
        messages.success(request, "Regra acadêmica atualizada.")
        return redirect("matriculas:regras_list")
    return render(request, "matriculas/regra_form.html", {"form": form, "page_title": "Editar Regra Acadêmica"})


def consolidacao_view(request, matricula_pk):
    """UC04 – Lançar/Consolidar Notas e Frequência"""
    matricula = get_object_or_404(
        Matricula.objects.select_related("aluno", "curso", "turma"),
        pk=matricula_pk,
    )
    consolidacao, _ = ConsolidacaoAcademica.objects.get_or_create(matricula=matricula)

    if request.method == "POST":
        acao = request.POST.get("acao")
        if acao == "consolidar":
            consolidacao.consolidar()
            messages.success(request, "Consolidação realizada com sucesso.")
        elif acao == "editar":
            form = ConsolidacaoObservacaoForm(request.POST, instance=consolidacao)
            if form.is_valid():
                form.save()
                messages.success(request, "Situação atualizada.")
        return redirect("matriculas:consolidacao_view", matricula_pk=matricula_pk)

    form = ConsolidacaoObservacaoForm(instance=consolidacao)
    notas = matricula.notas.all()
    frequencias = matricula.frequencias.all()
    total = frequencias.count()
    presencas = frequencias.filter(presente=True).count()

    return render(request, "matriculas/consolidacao.html", {
        "matricula": matricula,
        "consolidacao": consolidacao,
        "form": form,
        "notas": notas,
        "total_aulas": total,
        "presencas": presencas,
        "percentual": round(presencas / total * 100, 1) if total else 0,
    })


# ── P01 – Fluxo de Matrícula ─────────────────────────────────────────────────

def fluxo_list(request):
    """Lista todos os fluxos P01 em andamento e concluídos."""
    fluxos = FluxoMatricula.objects.select_related("aluno", "matricula").all()
    return render(request, "matriculas/fluxo_list.html", {"fluxos": fluxos})


def fluxo_create(request):
    """Etapa 1 – Receber Requerimento."""
    form = FluxoMatriculaIniciarForm(request.POST or None)
    if form.is_valid():
        fluxo = form.save()
        EtapaFluxo.objects.create(
            fluxo=fluxo,
            etapa='REQUERIMENTO_RECEBIDO',
            responsavel=request.user,
            observacao=form.cleaned_data.get("observacoes", ""),
        )
        messages.success(request, "Requerimento recebido. Fluxo P01 iniciado.")
        return redirect("matriculas:fluxo_detalhe", pk=fluxo.pk)
    return render(request, "matriculas/fluxo_form.html", {"form": form, "page_title": "Receber Requerimento"})


def fluxo_detalhe(request, pk):
    """Painel principal do P01 com swimlanes e ações por etapa."""
    fluxo = get_object_or_404(
        FluxoMatricula.objects.select_related("aluno", "matricula", "documento_comprovante"),
        pk=pk,
    )
    log = fluxo.log_etapas.select_related("responsavel").all()
    etapas = fluxo.etapas_info()
    ctx = {"fluxo": fluxo, "etapas": etapas, "log": log}

    etapa = fluxo.etapa_atual

    # Formulários contextuais por etapa
    if etapa == 'DOCUMENTOS_CONFERIDOS':
        ctx["documentos"] = fluxo.matricula.documentos.all() if fluxo.matricula else []
    elif etapa == 'PENDENCIA_ABERTA':
        ctx["form_pendencia"] = PendenciaFluxoForm()
    elif etapa in ('REQUISITOS_VALIDADOS', 'MATRICULA_REGISTRADA', 'COMPROVANTE_EMITIDO', 'ARQUIVADO'):
        ctx["form_obs"] = EtapaObservacaoForm()
    elif etapa == 'ALUNO_ENTURMADO' and fluxo.matricula:
        ctx["form_enturmar"] = FluxoEnturmarForm(instance=fluxo.matricula)

    return render(request, "matriculas/fluxo_detalhe.html", ctx)


def fluxo_avancar(request, pk):
    """POST: avança o P01 para a próxima etapa, processando a lógica da etapa atual."""
    if request.method != "POST":
        return redirect("matriculas:fluxo_detalhe", pk=pk)

    fluxo = get_object_or_404(FluxoMatricula, pk=pk)
    etapa_atual = fluxo.etapa_atual
    obs = request.POST.get("observacao", "")

    # ── Etapa 1→2: Documentos Conferidos ────────────────────────────────────
    if etapa_atual == 'REQUERIMENTO_RECEBIDO':
        # Garante que existe uma matrícula vinculada (cria se necessário)
        if not fluxo.matricula_id:
            messages.error(request, "Vincule uma matrícula antes de avançar.")
            return redirect("matriculas:fluxo_detalhe", pk=pk)
        fluxo.avancar('DOCUMENTOS_CONFERIDOS')

    # ── Etapa 2 → decisão: Completo? ────────────────────────────────────────
    elif etapa_atual == 'DOCUMENTOS_CONFERIDOS':
        decisao = request.POST.get("decisao")
        if decisao == "incompleto":
            form = PendenciaFluxoForm(request.POST)
            if form.is_valid():
                pendencia = form.save(commit=False)
                pendencia.matricula = fluxo.matricula
                pendencia.save()
                fluxo.avancar('PENDENCIA_ABERTA')
                obs = f"Pendência: {pendencia.descricao} | Prazo: {pendencia.prazo}"
            else:
                messages.error(request, "Corrija os erros na pendência.")
                return redirect("matriculas:fluxo_detalhe", pk=pk)
        else:
            fluxo.avancar('REQUISITOS_VALIDADOS')

    # ── Etapa 3→4: Pendência resolvida → Validar requisitos ─────────────────
    elif etapa_atual == 'PENDENCIA_ABERTA':
        fluxo.avancar('REQUISITOS_VALIDADOS')

    # ── Etapa 4→5: Registrar Matrícula ──────────────────────────────────────
    elif etapa_atual == 'REQUISITOS_VALIDADOS':
        fluxo.avancar('MATRICULA_REGISTRADA')

    # ── Etapa 5→6: Enturmar / Alocar Turno ──────────────────────────────────
    elif etapa_atual == 'MATRICULA_REGISTRADA':
        if fluxo.matricula:
            form = FluxoEnturmarForm(request.POST, instance=fluxo.matricula)
            if form.is_valid():
                form.save()
                fluxo.avancar('ALUNO_ENTURMADO')
            else:
                messages.error(request, "Selecione a turma e o turno.")
                return redirect("matriculas:fluxo_detalhe", pk=pk)
        else:
            fluxo.avancar('ALUNO_ENTURMADO')

    # ── Etapa 6→7: Emitir Comprovante ───────────────────────────────────────
    elif etapa_atual == 'ALUNO_ENTURMADO':
        if fluxo.matricula and not fluxo.documento_comprovante:
            comprovante = DocumentoEmitido.objects.create(
                matricula=fluxo.matricula,
                tipo='DECLARACAO_MATRICULA',
                observacao='Comprovante gerado automaticamente pelo fluxo P01.',
            )
            fluxo.documento_comprovante = comprovante
            fluxo.save()
        fluxo.avancar('COMPROVANTE_EMITIDO')
        obs = f"Comprovante: {fluxo.documento_comprovante.numero_protocolo}" if fluxo.documento_comprovante else obs

    # ── Etapa 7→8: Arquivar ─────────────────────────────────────────────────
    elif etapa_atual == 'COMPROVANTE_EMITIDO':
        from apps.arquivo.models import GuardaDocumental
        if fluxo.matricula:
            GuardaDocumental.objects.create(
                tipo_documento='PASTA_ALUNO',
                descricao=f"Pasta de matrícula – {fluxo.aluno}",
                matricula=fluxo.matricula,
                responsavel=request.user,
            )
        fluxo.avancar('ARQUIVADO')

    EtapaFluxo.objects.create(
        fluxo=fluxo,
        etapa=fluxo.etapa_atual,
        responsavel=request.user,
        observacao=obs,
    )
    messages.success(request, f"Etapa avançada: {fluxo.get_etapa_atual_display()}")
    return redirect("matriculas:fluxo_detalhe", pk=pk)


def fluxo_vincular_matricula(request, pk):
    """Vincula uma matrícula existente ao fluxo P01 (etapa 1)."""
    fluxo = get_object_or_404(FluxoMatricula, pk=pk)
    form = MatriculaForm(request.POST or None)
    if form.is_valid():
        matricula = form.save()
        fluxo.matricula = matricula
        fluxo.save()
        messages.success(request, "Matrícula vinculada ao fluxo.")
        return redirect("matriculas:fluxo_detalhe", pk=pk)
    return render(request, "matriculas/fluxo_vincular_matricula.html", {
        "form": form,
        "fluxo": fluxo,
        "page_title": "Registrar Matrícula no Fluxo",
    })


# ── P02 – Fluxo de Emissão de Histórico/Declaração ───────────────────────────

def emissao_list(request):
    fluxos = FluxoEmissaoDocumento.objects.select_related(
        "solicitante", "matricula", "processo", "documento_emitido"
    ).all()
    return render(request, "matriculas/emissao_list.html", {"fluxos": fluxos})


def emissao_create(request):
    """Etapa 1 – Abrir Protocolo."""
    form = FluxoEmissaoIniciarForm(request.POST or None)
    if form.is_valid():
        fluxo = form.save()
        # Cria o processo/protocolo automaticamente (UC05)
        from apps.processos.models import Processo
        processo = Processo.objects.create(
            tipo='REQUERIMENTO',
            requerente=fluxo.solicitante,
            assunto=f"Emissão de {fluxo.get_tipo_documento_display()} – {fluxo.solicitante}",
            descricao=fluxo.observacoes,
        )
        fluxo.processo = processo
        fluxo.save()
        EtapaFluxoEmissao.objects.create(
            fluxo=fluxo,
            etapa='PROTOCOLO_ABERTO',
            responsavel=request.user,
            observacao=f"Protocolo criado: {processo.numero}",
        )
        messages.success(request, f"Protocolo aberto: {processo.numero}")
        return redirect("matriculas:emissao_detalhe", pk=fluxo.pk)
    return render(request, "matriculas/emissao_form.html", {
        "form": form,
        "page_title": "Abrir Protocolo – P02",
    })


def emissao_detalhe(request, pk):
    """Painel principal do P02 com swimlanes."""
    fluxo = get_object_or_404(
        FluxoEmissaoDocumento.objects.select_related(
            "solicitante", "matricula", "matricula__aluno",
            "matricula__curso", "processo", "documento_emitido",
        ),
        pk=pk,
    )
    log = fluxo.log_etapas.select_related("responsavel").all()
    etapas = fluxo.etapas_info()
    ctx = {
        "fluxo": fluxo,
        "etapas": etapas,
        "log": log,
        "form_obs": EtapaEmissaoObservacaoForm(),
    }

    etapa = fluxo.etapa_atual
    if etapa == 'DOCUMENTO_VALIDADO' and fluxo.documento_emitido:
        ctx["form_validar"] = ValidarDocumentoForm(instance=fluxo.documento_emitido)
    if etapa == 'ENTREGA_REGISTRADA' and fluxo.documento_emitido:
        ctx["form_entrega"] = ValidarEntregaP02Form(instance=fluxo.documento_emitido)

    return render(request, "matriculas/emissao_detalhe.html", ctx)


def emissao_avancar(request, pk):
    """POST: avança P02 para a próxima etapa processando a lógica de cada step."""
    if request.method != "POST":
        return redirect("matriculas:emissao_detalhe", pk=pk)

    fluxo = get_object_or_404(FluxoEmissaoDocumento, pk=pk)
    etapa_atual = fluxo.etapa_atual
    obs = request.POST.get("observacao", "")

    # ── Etapa 1→2: Verificar Elegibilidade (automático pelo Sistema) ─────────
    if etapa_atual == 'PROTOCOLO_ABERTO':
        elegivel = fluxo.verificar_elegibilidade()
        if elegivel:
            fluxo.avancar('ELEGIBILIDADE_VERIFICADA')
            obs = "Aluno elegível. Requisitos verificados pelo sistema."
        else:
            messages.error(request, f"Aluno não elegível: {fluxo.motivo_inelegivel}")
            return redirect("matriculas:emissao_detalhe", pk=pk)

    # ── Etapa 2→3: Gerar Documento Padrão (automático pelo Sistema) ──────────
    elif etapa_atual == 'ELEGIBILIDADE_VERIFICADA':
        if not fluxo.documento_emitido:
            doc = DocumentoEmitido.objects.create(
                matricula=fluxo.matricula,
                tipo=fluxo.tipo_documento,
                observacao=f"Gerado automaticamente pelo Fluxo P02 – {fluxo.processo.numero if fluxo.processo else ''}",
            )
            fluxo.documento_emitido = doc
            fluxo.save()
        fluxo.avancar('DOCUMENTO_GERADO')
        obs = f"Documento gerado: {fluxo.documento_emitido.numero_protocolo}"

    # ── Etapa 3→4: Assinar / Validar ─────────────────────────────────────────
    elif etapa_atual == 'DOCUMENTO_GERADO':
        fluxo.avancar('DOCUMENTO_VALIDADO')

    # ── Etapa 4: Confirmação da validação ────────────────────────────────────
    elif etapa_atual == 'DOCUMENTO_VALIDADO':
        if fluxo.documento_emitido:
            form = ValidarDocumentoForm(request.POST, instance=fluxo.documento_emitido)
            if form.is_valid():
                validado = form.save(commit=False)
                if validado.validado:
                    validado.validado_por = request.user
                validado.save()
                fluxo.avancar('ENTREGA_REGISTRADA')
                obs = f"Documento validado em {validado.data_validacao}"
            else:
                messages.error(request, "Corrija os erros de validação.")
                return redirect("matriculas:emissao_detalhe", pk=pk)
        else:
            fluxo.avancar('ENTREGA_REGISTRADA')

    # ── Etapa 5: Registrar Entrega ────────────────────────────────────────────
    elif etapa_atual == 'ENTREGA_REGISTRADA':
        if fluxo.documento_emitido:
            form = ValidarEntregaP02Form(request.POST, instance=fluxo.documento_emitido)
            if form.is_valid():
                form.save()
                fluxo.avancar('ARQUIVADO')
                obs = f"Entregue a: {fluxo.documento_emitido.recebido_por}"
            else:
                messages.error(request, "Corrija os dados de entrega.")
                return redirect("matriculas:emissao_detalhe", pk=pk)
        else:
            fluxo.avancar('ARQUIVADO')

    # ── Etapa 6→fim: Arquivar via Protocolo ──────────────────────────────────
    elif etapa_atual == 'ARQUIVADO':
        from apps.arquivo.models import GuardaDocumental
        if fluxo.documento_emitido:
            GuardaDocumental.objects.get_or_create(
                tipo_documento='DECLARACAO',
                descricao=f"{fluxo.get_tipo_documento_display()} – {fluxo.solicitante}",
                defaults={
                    "matricula": fluxo.matricula,
                    "processo": fluxo.processo,
                    "responsavel": request.user,
                },
            )
        fluxo.concluido = True
        fluxo.save()
        obs = "Fluxo P02 concluído e arquivado."

    EtapaFluxoEmissao.objects.create(
        fluxo=fluxo,
        etapa=fluxo.etapa_atual,
        responsavel=request.user,
        observacao=obs,
    )
    messages.success(request, f"Etapa: {fluxo.get_etapa_atual_display()}")
    return redirect("matriculas:emissao_detalhe", pk=pk)


# ── P03 – Fluxo de Transferência ─────────────────────────────────────────────

def transferencia_fluxo_list(request):
    fluxos = FluxoTransferencia.objects.select_related(
        "matricula", "matricula__aluno", "matricula__curso",
        "transferencia", "processo", "documento_emitido",
    ).all()
    return render(request, "matriculas/transferencia_fluxo_list.html", {"fluxos": fluxos})


def transferencia_fluxo_create(request):
    """Etapa 1 – Solicitação: abre o fluxo P03 e registra a transferência."""
    form_fluxo = FluxoTransferenciaIniciarForm(request.POST or None)
    form_trans = TransferenciaFluxoForm(request.POST or None)
    if request.method == "POST" and form_fluxo.is_valid() and form_trans.is_valid():
        fluxo = form_fluxo.save(commit=False)
        transferencia = form_trans.save(commit=False)
        transferencia.matricula = fluxo.matricula
        transferencia.save()
        fluxo.transferencia = transferencia
        fluxo.save()
        from apps.processos.models import Processo
        processo = Processo.objects.create(
            tipo='REQUERIMENTO',
            requerente=fluxo.matricula.aluno,
            assunto=f"Transferência ({transferencia.get_tipo_display()}) – {fluxo.matricula.aluno}",
            descricao=fluxo.observacoes,
        )
        fluxo.processo = processo
        fluxo.save()
        EtapaFluxoTransferencia.objects.create(
            fluxo=fluxo,
            etapa='SOLICITACAO',
            responsavel=request.user,
            observacao=f"Protocolo: {processo.numero} | Tipo: {transferencia.get_tipo_display()}",
        )
        messages.success(request, f"Solicitação registrada. Protocolo: {processo.numero}")
        return redirect("matriculas:transferencia_fluxo_detalhe", pk=fluxo.pk)
    return render(request, "matriculas/transferencia_fluxo_form.html", {
        "form_fluxo": form_fluxo,
        "form_trans": form_trans,
        "page_title": "P03 – Solicitação de Transferência",
    })


def transferencia_fluxo_detalhe(request, pk):
    fluxo = get_object_or_404(
        FluxoTransferencia.objects.select_related(
            "matricula", "matricula__aluno", "matricula__curso",
            "transferencia", "processo", "documento_emitido",
        ),
        pk=pk,
    )
    log = fluxo.log_etapas.select_related("responsavel").all()
    etapas = fluxo.etapas_info()
    ctx = {
        "fluxo": fluxo,
        "etapas": etapas,
        "log": log,
        "form_obs": EtapaTransferenciaObservacaoForm(),
    }
    return render(request, "matriculas/transferencia_fluxo_detalhe.html", ctx)


def transferencia_fluxo_avancar(request, pk):
    if request.method != "POST":
        return redirect("matriculas:transferencia_fluxo_detalhe", pk=pk)

    fluxo = get_object_or_404(FluxoTransferencia, pk=pk)
    etapa_atual = fluxo.etapa_atual
    obs = request.POST.get("observacao", "")

    # ── Etapa 1→2: Conferência de Dados ──────────────────────────────────────
    if etapa_atual == 'SOLICITACAO':
        fluxo.avancar('CONFERENCIA_DADOS')

    # ── Etapa 2→3: Emitir Guia / Histórico Parcial ───────────────────────────
    elif etapa_atual == 'CONFERENCIA_DADOS':
        tipo_doc = (
            'GUIA_TRANSFERENCIA'
            if fluxo.transferencia and fluxo.transferencia.tipo == 'SAIDA'
            else 'HISTORICO_ESCOLAR'
        )
        if not fluxo.documento_emitido:
            doc = DocumentoEmitido.objects.create(
                matricula=fluxo.matricula,
                tipo=tipo_doc,
                observacao=f"Gerado pelo Fluxo P03 – {fluxo.processo.numero if fluxo.processo else ''}",
            )
            fluxo.documento_emitido = doc
            fluxo.save()
        fluxo.avancar('GUIA_EMITIDA')
        obs = f"Documento gerado: {fluxo.documento_emitido.numero_protocolo}"

    # ── Etapa 3→4: Baixa / Atualização no Sistema ────────────────────────────
    elif etapa_atual == 'GUIA_EMITIDA':
        if fluxo.transferencia:
            if fluxo.transferencia.tipo == 'SAIDA':
                fluxo.matricula.status = 'CANCELADA'
                fluxo.matricula.save()
                obs = obs or "Matrícula cancelada por transferência de saída."
            fluxo.transferencia.status = 'CONCLUIDA'
            fluxo.transferencia.save()
        fluxo.avancar('BAIXA_ATUALIZADA')

    # ── Etapa 4→5: Arquivamento ───────────────────────────────────────────────
    elif etapa_atual == 'BAIXA_ATUALIZADA':
        from apps.arquivo.models import GuardaDocumental
        GuardaDocumental.objects.get_or_create(
            tipo_documento='PASTA_ALUNO',
            descricao=f"Transferência – {fluxo.matricula.aluno}",
            defaults={
                "matricula": fluxo.matricula,
                "processo": fluxo.processo,
                "responsavel": request.user,
            },
        )
        fluxo.avancar('ARQUIVADO')
        obs = obs or "Processo arquivado."

    EtapaFluxoTransferencia.objects.create(
        fluxo=fluxo,
        etapa=fluxo.etapa_atual,
        responsavel=request.user,
        observacao=obs,
    )
    messages.success(request, f"Etapa: {fluxo.get_etapa_atual_display()}")
    return redirect("matriculas:transferencia_fluxo_detalhe", pk=pk)
