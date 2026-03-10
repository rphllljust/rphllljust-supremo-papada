"""
Teste de Ponta a Ponta: Aluno de Técnico em Auxiliar Administrativo
Percorre todos os fluxos desde inscrição até emissão de diploma.

Execute:  python manage.py runscript teste_fluxo_completo
          OU diretamente: python teste_fluxo_completo.py (via django.setup())
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

# ─── imports ────────────────────────────────────────────────────────────────
from django.utils import timezone
from decimal import Decimal

from apps.unidades.models import Unidade
from apps.cursos.models import Curso, CalendarioLetivo
from apps.turmas.models import Turma, DiarioAcademico
from apps.usuarios.models import Usuario
from apps.matriculas.models import (
    Matricula, DocumentoMatricula, PendenciaDocumental,
    DocumentoEmitido, Transferencia, RegraAcademica,
    ConsolidacaoAcademica, FluxoMatricula, EtapaFluxo,
    FluxoEmissaoDocumento, EtapaFluxoEmissao,
    AproveitamentoComponente, ConselhoClasse, AtaResultado,
    CertificadoDiploma, AtaEscolar, DiplomaEscolar,
)
from apps.notas.models import Nota
from apps.frequencia.models import Frequencia
from apps.processos.models import Processo, Solicitacao
from apps.arquivo.models import GuardaDocumental, PlanoClassificacao
from apps.inscricoes.models import (
    PublicacaoInscricao, Inscricao, DocumentoInscricao,
    ProcessoSeletivo, Candidato,
)
from apps.estagio.models import Convenio, Estagio, TermoCompromisso, AcompanhamentoEstagio


SEP = "=" * 65

def titulo(texto):
    print(f"\n{SEP}")
    print(f"  {texto}")
    print(SEP)

def ok(msg):
    print(f"  [OK] {msg}")

def info(msg):
    print(f"       {msg}")


def run():
    titulo("LIMPANDO DADOS DO TESTE ANTERIOR")
    # Remove dados de testes anteriores com este aluno
    Usuario.objects.filter(username="joao.silva.teste").delete()
    Usuario.objects.filter(username="secretaria.teste").delete()
    Usuario.objects.filter(username="carlos.ferreira").delete()
    Unidade.objects.filter(nome="IDEP – Instituto de Educação Profissional").delete()
    ok("Limpeza concluída")

    # ─── 1. INFRAESTRUTURA ────────────────────────────────────────────────
    titulo("1. INFRAESTRUTURA — Unidade / Curso / Turma")

    unidade = Unidade.objects.create(
        nome="IDEP – Instituto de Educação Profissional",
        codigo="IDEP-001",
        endereco="Av. Governador Jorge Teixeira, 3146",
        cidade="Porto Velho",
        uf="RO",
    )
    ok(f"Unidade: {unidade}")

    curso = Curso.objects.create(
        unidade=unidade,
        nome="Técnico em Auxiliar Administrativo",
        carga_horaria=800,
    )
    ok(f"Curso: {curso}")

    calendario = CalendarioLetivo.objects.create(
        ano_letivo="2025/1",
        curso=curso,
        data_inicio=timezone.now().date().replace(month=2, day=3),
        data_fim=timezone.now().date().replace(month=12, day=5),
        dias_letivos=200,
        status="VIGENTE",
    )
    ok(f"Calendário: {calendario}")

    regra = RegraAcademica.objects.create(
        curso=curso,
        media_minima=Decimal("6.0"),
        frequencia_minima=Decimal("75.0"),
    )
    ok(f"Regra acadêmica: {regra}")

    # Usuários
    secretaria = Usuario.objects.create_user(
        username="secretaria.teste",
        password="senha123",
        cpf="00000000001",
        tipo="SECRETARIA",
        first_name="Maria",
        last_name="Secretaria",
    )
    ok(f"Usuário Secretaria: {secretaria}")

    professor = Usuario.objects.create_user(
        username="carlos.ferreira",
        password="senha123",
        cpf="00000000002",
        tipo="PROFESSOR",
        first_name="Carlos Eduardo",
        last_name="Ferreira",
    )
    ok(f"Usuário Professor: {professor.get_full_name()} ({professor.username})")

    turma = Turma.objects.create(
        curso=curso,
        nome="TAA-2025-A",
        ano_letivo=2025,
        professor_responsavel=professor,
    )
    ok(f"Turma: {turma}")

    # Aluno
    aluno = Usuario.objects.create_user(
        username="joao.silva.teste",
        password="senha123",
        cpf="12345678901",
        tipo="ALUNO",
        first_name="João",
        last_name="Silva",
    )
    ok(f"Aluno: {aluno}")

    # ─── 2. CAPTAÇÃO / INSCRIÇÃO ──────────────────────────────────────────
    titulo("2. CAPTAÇÃO — Publicação de Inscrições")

    publicacao = PublicacaoInscricao.objects.create(
        curso=curso,
        titulo="Processo Seletivo TAA 2025/1",
        descricao="Técnico em Auxiliar Administrativo – 40 vagas. Ensino Médio completo.",
        vagas=40,
        data_inicio=timezone.now().date(),
        data_fim=timezone.now().date().replace(day=28),
        status="PUBLICADO",
        publicado_por=secretaria,
    )
    ok(f"Publicação: {publicacao}")

    # ─── 3. INSCRIÇÃO ─────────────────────────────────────────────────────
    titulo("3. INSCRIÇÃO — Receber e Validar Documentos")

    inscricao = Inscricao.objects.create(
        publicacao=publicacao,
        nome_candidato="João Silva",
        cpf="12345678901",
        email="joao.silva@email.com",
        telefone="65999990001",
        data_nascimento=timezone.now().date().replace(year=2000, month=5, day=15),
        status="PENDENTE",
        usuario=aluno,
    )
    ok(f"Inscrição criada: {inscricao.numero_inscricao}")

    # Documentos da inscrição
    for tipo in ["RG", "CPF", "HISTORICO_ESCOLAR"]:
        doc = DocumentoInscricao.objects.create(
            inscricao=inscricao,
            tipo=tipo,
            entregue=True,
            data_entrega=timezone.now().date(),
        )
        ok(f"  Documento entregue: {doc.get_tipo_display()}")

    inscricao.status = "VALIDADA"
    inscricao.save()
    ok(f"Inscrição validada: {inscricao.get_status_display()}")

    # ─── 4. SELEÇÃO / CONVOCAÇÃO ──────────────────────────────────────────
    titulo("4. SELEÇÃO / CONVOCAÇÃO — Processo Seletivo")

    seletivo = ProcessoSeletivo.objects.create(
        publicacao=publicacao,
        modalidade="DEMANDA_ESPONTANEA",
        data_realizacao=timezone.now().date(),
        data_resultado=timezone.now().date(),
        status="CONCLUIDO",
        criterios="Ordem de inscrição e documentação completa.",
        resultado="João Silva – 1º classificado",
        responsavel=secretaria,
    )
    ok(f"Processo seletivo: {seletivo}")

    candidato = Candidato.objects.create(
        processo=seletivo,
        inscricao=inscricao,
        classificacao=1,
        pontuacao=Decimal("10.0"),
        situacao="CONVOCADO",
        data_convocacao=timezone.now().date(),
    )
    ok(f"Candidato convocado: {candidato}")

    # ─── 5. MATRÍCULA INICIAL (Fluxo P01) ────────────────────────────────
    titulo("5. MATRÍCULA INICIAL — Fluxo P01")

    # Etapa 1 – Requerimento Recebido
    fluxo = FluxoMatricula.objects.create(
        aluno=aluno,
        tipo_matricula="NOVA",
        etapa_atual="REQUERIMENTO_RECEBIDO",
        observacoes="Aluno convocado pelo processo seletivo TAA 2025/1",
    )
    EtapaFluxo.objects.create(fluxo=fluxo, etapa="REQUERIMENTO_RECEBIDO", responsavel=secretaria,
                               observacao="Requerimento recebido na secretaria.")
    ok(f"Fluxo P01 iniciado: {fluxo}")

    # Criar e vincular matrícula
    matricula = Matricula.objects.create(
        aluno=aluno,
        curso=curso,
        turma=turma,
        tipo_matricula="NOVA",
        status="ATIVA",
        turno="MANHA",
    )
    fluxo.matricula = matricula
    fluxo.save()
    ok(f"Matrícula criada: {matricula}")

    # Etapa 2 – Conferir Documentos
    fluxo.avancar("DOCUMENTOS_CONFERIDOS")
    EtapaFluxo.objects.create(fluxo=fluxo, etapa="DOCUMENTOS_CONFERIDOS", responsavel=secretaria)
    ok(f"Etapa: {fluxo.get_etapa_atual_display()}")

    # Registrar documentos da matrícula
    docs_matricula = [
        ("RG", True), ("CPF", True), ("COMPROVANTE_RESIDENCIA", True),
        ("HISTORICO_ESCOLAR", True), ("FOTO", True),
    ]
    for tipo, entregue in docs_matricula:
        DocumentoMatricula.objects.create(
            matricula=matricula, tipo_documento=tipo,
            entregue=entregue, data_entrega=timezone.now().date(),
        )
        ok(f"  Documento: {tipo} {'✓' if entregue else '✗'}")

    # Etapa 3 – Requisitos Validados (sem pendências)
    fluxo.avancar("REQUISITOS_VALIDADOS")
    EtapaFluxo.objects.create(fluxo=fluxo, etapa="REQUISITOS_VALIDADOS", responsavel=secretaria,
                               observacao="Documentação completa. Sem pendências.")
    ok(f"Etapa: {fluxo.get_etapa_atual_display()}")

    # Etapa 4 – Matrícula Registrada
    fluxo.avancar("MATRICULA_REGISTRADA")
    EtapaFluxo.objects.create(fluxo=fluxo, etapa="MATRICULA_REGISTRADA", responsavel=secretaria)
    ok(f"Etapa: {fluxo.get_etapa_atual_display()}")

    # Etapa 5 – Enturmar
    fluxo.avancar("ALUNO_ENTURMADO")
    EtapaFluxo.objects.create(fluxo=fluxo, etapa="ALUNO_ENTURMADO", responsavel=secretaria,
                               observacao=f"Turno: Manhã | Turma: {turma.nome}")
    ok(f"Etapa: {fluxo.get_etapa_atual_display()}")

    # Etapa 6 – Emitir Comprovante
    comprovante = DocumentoEmitido.objects.create(
        matricula=matricula,
        tipo="DECLARACAO_MATRICULA",
        observacao="Comprovante de matrícula emitido pelo fluxo P01.",
    )
    fluxo.documento_comprovante = comprovante
    fluxo.avancar("COMPROVANTE_EMITIDO")
    EtapaFluxo.objects.create(fluxo=fluxo, etapa="COMPROVANTE_EMITIDO", responsavel=secretaria,
                               observacao=f"Protocolo: {comprovante.numero_protocolo}")
    ok(f"Comprovante de matrícula emitido: {comprovante.numero_protocolo}")

    # Etapa 7 – Arquivar
    plano, _ = PlanoClassificacao.objects.get_or_create(
        codigo="PASTAS-ALUNO",
        defaults=dict(descricao="Pastas de Alunos", prazo_guarda_anos=10, destinacao="GUARDA_PERMANENTE"),
    )
    GuardaDocumental.objects.create(
        tipo_documento="PASTA_ALUNO",
        descricao=f"Pasta de matrícula – {aluno}",
        matricula=matricula,
        responsavel=secretaria,
        plano_classificacao=plano,
    )
    fluxo.avancar("ARQUIVADO")
    EtapaFluxo.objects.create(fluxo=fluxo, etapa="ARQUIVADO", responsavel=secretaria)
    ok(f"Fluxo P01 concluído: {fluxo}")
    info(f"Matrícula status: {matricula.get_status_display()} | Turno: {matricula.get_turno_display()}")

    # ─── 6. ORGANIZAÇÃO ACADÊMICA ─────────────────────────────────────────
    titulo("6. ORGANIZAÇÃO ACADÊMICA — Diário / Calendário")

    diario = DiarioAcademico.objects.create(
        turma=turma,
        periodo="2025/1",
        componente_curricular="Gestão Administrativa e Comunicação Empresarial",
        status="ABERTO",
        observacoes="Diário aberto para o semestre 2025/1",
        aberto_por=secretaria,
    )
    ok(f"Diário acadêmico aberto: {diario}")

    # ─── 7. EXECUÇÃO DO PERÍODO LETIVO — Notas e Frequência ──────────────
    titulo("7. EXECUÇÃO DO PERÍODO LETIVO — Lançamentos")

    # Notas
    notas_lancadas = [
        ("Prova 1 – Gestão Básica", Decimal("7.5"), Decimal("1")),
        ("Prova 2 – Comunicação Empresarial", Decimal("8.0"), Decimal("1")),
        ("Trabalho – Planilhas", Decimal("9.0"), Decimal("1")),
        ("Avaliação Final", Decimal("7.0"), Decimal("2")),
    ]
    from datetime import date, timedelta
    base_date = date(2025, 3, 1)
    for i, (desc, valor, peso) in enumerate(notas_lancadas):
        Nota.objects.create(
            matricula=matricula, descricao=desc, valor=valor,
            peso=peso, data_lancamento=base_date + timedelta(weeks=i*4),
        )
        ok(f"  Nota lançada: {desc} = {valor} (peso {peso})")

    # Frequência (85% presença — 17/20 aulas)
    for i in range(20):
        presente = i < 17  # 85% de presença
        Frequencia.objects.create(
            matricula=matricula,
            data=base_date + timedelta(days=i*5),
            presente=presente,
            observacao="" if presente else "Falta justificada",
        )
    presencas = Frequencia.objects.filter(matricula=matricula, presente=True).count()
    total_aulas = Frequencia.objects.filter(matricula=matricula).count()
    ok(f"Frequência lançada: {presencas}/{total_aulas} presenças ({presencas/total_aulas*100:.1f}%)")

    # Consolidação
    consolidacao, _ = ConsolidacaoAcademica.objects.get_or_create(matricula=matricula)
    consolidacao.consolidar()
    ok(f"Consolidação: média={consolidacao.media_final} | freq={consolidacao.percentual_frequencia}% | situação={consolidacao.get_situacao_display()}")

    # ─── 8. APROVEITAMENTO DE COMPONENTE ─────────────────────────────────
    titulo("8. MOVIMENTAÇÕES — Aproveitamento de Componente")

    aproveitamento = AproveitamentoComponente.objects.create(
        matricula=matricula,
        componente_origem="Informática Básica",
        instituicao_origem="Centro de Formação Profissional – SENAC",
        carga_horaria=40,
        componente_destino="Tecnologia da Informação Aplicada",
        status="APROVADO",
        data_decisao=timezone.now().date(),
        decisao_por=secretaria,
        justificativa="Componente equivalente verificado pela coordenação pedagógica.",
    )
    ok(f"Aproveitamento: {aproveitamento}")

    # ─── 9. EMISSÃO DE DECLARAÇÃO (Fluxo P02) ────────────────────────────
    titulo("9. EXECUÇÃO — Emissão de Declaração de Frequência (P02)")

    fluxo_p02 = FluxoEmissaoDocumento.objects.create(
        solicitante=aluno,
        matricula=matricula,
        tipo_documento="DECLARACAO_FREQUENCIA",
        etapa_atual="PROTOCOLO_ABERTO",
        observacoes="Solicitação de declaração de frequência para apresentação ao empregador.",
    )
    processo_p02 = Processo.objects.create(
        tipo="REQUERIMENTO",
        requerente=aluno,
        assunto=f"Declaração de Frequência – {aluno.get_full_name()}",
        descricao=fluxo_p02.observacoes,
    )
    fluxo_p02.processo = processo_p02
    fluxo_p02.save()
    EtapaFluxoEmissao.objects.create(fluxo=fluxo_p02, etapa="PROTOCOLO_ABERTO", responsavel=secretaria,
                                      observacao=f"Protocolo: {processo_p02.numero}")
    ok(f"P02 iniciado – protocolo: {processo_p02.numero}")

    # Verificar elegibilidade
    elegivel = fluxo_p02.verificar_elegibilidade()
    fluxo_p02.avancar("ELEGIBILIDADE_VERIFICADA")
    EtapaFluxoEmissao.objects.create(fluxo=fluxo_p02, etapa="ELEGIBILIDADE_VERIFICADA", responsavel=secretaria)
    ok(f"Elegibilidade: {'Apto' if elegivel else 'Inapto'}")

    # Gerar documento
    doc_freq = DocumentoEmitido.objects.create(
        matricula=matricula,
        tipo="DECLARACAO_FREQUENCIA",
        observacao=f"Gerado pelo Fluxo P02 – {processo_p02.numero}",
    )
    fluxo_p02.documento_emitido = doc_freq
    fluxo_p02.save()
    fluxo_p02.avancar("DOCUMENTO_GERADO")
    EtapaFluxoEmissao.objects.create(fluxo=fluxo_p02, etapa="DOCUMENTO_GERADO",
                                      observacao=f"Documento: {doc_freq.numero_protocolo}")
    ok(f"Declaração gerada: {doc_freq.numero_protocolo}")

    # Validar e entregar
    doc_freq.validado = True
    doc_freq.validado_por = secretaria
    doc_freq.data_validacao = timezone.now().date()
    doc_freq.save()
    fluxo_p02.avancar("DOCUMENTO_VALIDADO")
    EtapaFluxoEmissao.objects.create(fluxo=fluxo_p02, etapa="DOCUMENTO_VALIDADO", responsavel=secretaria)

    doc_freq.entregue = True
    doc_freq.data_entrega = timezone.now().date()
    doc_freq.recebido_por = "João Silva (pessoalmente)"
    doc_freq.save()
    fluxo_p02.avancar("ENTREGA_REGISTRADA")
    EtapaFluxoEmissao.objects.create(fluxo=fluxo_p02, etapa="ENTREGA_REGISTRADA", responsavel=secretaria)
    fluxo_p02.avancar("ARQUIVADO")
    fluxo_p02.concluido = True
    fluxo_p02.save()
    ok(f"P02 concluído – declaração entregue a: {doc_freq.recebido_por}")

    # ─── 10. ESTÁGIO ──────────────────────────────────────────────────────
    titulo("10. ESTÁGIO — Convênio / TCE / Acompanhamento / Encerramento")

    convenio = Convenio.objects.create(
        empresa="Contabilidade Rápida Ltda",
        cnpj="12.345.678/0001-99",
        responsavel_empresa="Ana Paula Moreira",
        email_empresa="rh@contabilidaderap.com.br",
        telefone_empresa="65 3333-0001",
        data_assinatura=date(2025, 2, 1),
        data_vencimento=date(2026, 1, 31),
        status="VIGENTE",
        objeto="Oferta de vagas de estágio obrigatório para alunos do TAA.",
        responsavel_idep=secretaria,
    )
    ok(f"Convênio: {convenio}")

    estagio = Estagio.objects.create(
        matricula=matricula,
        convenio=convenio,
        modalidade="OBRIGATORIO",
        empresa="Contabilidade Rápida Ltda",
        supervisor_empresa="Ana Paula Moreira",
        orientador_idep=professor,
        carga_horaria_total=200,
        carga_horaria_semanal=20,
        data_inicio=date(2025, 7, 1),
        data_fim_prevista=date(2025, 11, 28),
        status="EM_ANDAMENTO",
        bolsa_mensal=Decimal("600.00"),
        seguro_numero="SEG-2025-00123",
    )
    ok(f"Estágio: {estagio}")

    termo = TermoCompromisso.objects.create(
        estagio=estagio,
        data_assinatura=date(2025, 6, 25),
        status="ASSINADO",
        assinado_aluno=True,
        assinado_empresa=True,
        assinado_idep=True,
    )
    ok(f"Termo de Compromisso: {termo}")

    acomp1 = AcompanhamentoEstagio.objects.create(
        estagio=estagio,
        tipo="VISITA",
        data=date(2025, 8, 15),
        descricao="Visita ao local do estágio. Aluno bem adaptado. Desempenho satisfatório.",
        registrado_por=professor,
    )
    ok(f"Acompanhamento 1: {acomp1.get_tipo_display()} – {acomp1.data}")

    acomp2 = AcompanhamentoEstagio.objects.create(
        estagio=estagio,
        tipo="RELATORIO",
        data=date(2025, 10, 10),
        descricao="Relatório parcial entregue pelo estagiário. Carga: 120h cumpridas.",
        registrado_por=professor,
    )
    ok(f"Acompanhamento 2: {acomp2.get_tipo_display()} – {acomp2.data}")

    # Encerrar estágio
    estagio.status = "CONCLUIDO"
    estagio.data_fim_real = date(2025, 11, 28)
    estagio.observacao = "Estágio concluído com sucesso. 200h integralizadas."
    estagio.save()
    ok(f"Estágio encerrado: {estagio.get_status_display()} em {estagio.data_fim_real}")

    # ─── 11. FECHAMENTO / CONSELHO DE CLASSE / ATA ───────────────────────
    titulo("11. FECHAMENTO — Fechar Diário / Conselho / Ata")

    # Fechar diário
    diario.status = "FECHADO"
    diario.data_fechamento = date(2025, 12, 1)
    diario.fechado_por = secretaria
    diario.observacoes = "Diário fechado após verificação de consistência de notas e frequências."
    diario.save()
    ok(f"Diário fechado em: {diario.data_fechamento}")

    # Conselho de Classe
    conselho = ConselhoClasse.objects.create(
        turma=turma,
        periodo="2025/1",
        data_reuniao=date(2025, 12, 3),
        status="REALIZADO",
        pauta="1. Análise de notas e frequências da turma TAA-2025-A\n2. Decisão sobre alunos em recuperação\n3. Validação de requisitos para conclusão",
        ata="Conselho realizado. João Silva aprovado com média 7.66 e 85% de frequência.",
        responsavel=secretaria,
    )
    ok(f"Conselho de Classe: {conselho}")

    ata = AtaResultado.objects.create(
        conselho=conselho,
        data_publicacao=date(2025, 12, 4),
        conteudo=(
            "ATA DE RESULTADO – TAA-2025-A / 2025.1\n\n"
            "Aluno: João Silva\n"
            f"Matrícula: {matricula.pk}\n"
            f"Média Final: {consolidacao.media_final}\n"
            f"Frequência: {consolidacao.percentual_frequencia}%\n"
            f"Situação: {consolidacao.get_situacao_display()}\n\n"
            "Aprovado para emissão de Certificado."
        ),
        publicado_por=secretaria,
    )
    ok(f"Ata publicada: {ata.numero_ata}")

    # ── Ata Escolar (Documento Formal) ─────────────────────────────────────
    from datetime import time as dtime
    _meses_pt = ['janeiro','fevereiro','março','abril','maio','junho',
                 'julho','agosto','setembro','outubro','novembro','dezembro']
    def _data_pt(d):
        return f'{d.day:02d} de {_meses_pt[d.month - 1]} de {d.year}'

    _dr = conselho.data_reuniao
    _abertura_texto = (
        f"Aos {_dr.day:02d} dias do mês de {_meses_pt[_dr.month - 1]} "
        f"do ano de {_dr.year}, às 08h00, reuniu-se o Conselho de Classe "
        f"da turma {turma.nome}, referente ao período {conselho.periodo}, "
        f"na {unidade.nome}, com a finalidade de deliberar sobre o "
        f"resultado final dos alunos."
    )
    ata_escolar = AtaEscolar.objects.create(
        conselho=conselho,
        tipo="RESULTADO_FINAL",
        titulo=f"ATA DE RESULTADO FINAL – {turma.nome} / {conselho.periodo}",
        unidade_nome=unidade.nome,
        local_reuniao=f"Sala de Reuniões – {unidade.nome}, {unidade.cidade}/{unidade.uf}",
        data_reuniao=conselho.data_reuniao,
        hora_inicio=dtime(8, 0),
        hora_fim=dtime(10, 30),
        presidente=secretaria,
        secretario=professor,
        membros_presentes=(
            f"Maria Secretaria – Secretária Escolar (Presidente)\n"
            f"Carlos Eduardo Ferreira – Professor Responsável (Secretário)\n"
            f"João Pereira da Costa – Coordenador Pedagógico\n"
            f"Ana Lima Rodrigues – Orientadora Educacional\n"
            f"Pedro Alves Mendes – Representante de Turma"
        ),
        abertura=_abertura_texto,
        deliberacoes=conselho.ata,
        encerramento=(
            "Nada mais havendo a tratar, a presente Ata foi lavrada e será "
            "assinada pelos presentes, encerrando-se a reunião às 10h30."
        ),
        assinado=True,
        data_assinatura=conselho.data_reuniao,
    )
    ok(f"Ata Escolar emitida: {ata_escolar.numero_documento}")

    # ─── 12. EMISSÃO DE HISTÓRICO ESCOLAR ────────────────────────────────
    titulo("12. FECHAMENTO — Histórico Escolar (P02)")

    historico = DocumentoEmitido.objects.create(
        matricula=matricula,
        tipo="HISTORICO_ESCOLAR",
        observacao="Histórico final emitido após aprovação em conselho de classe.",
        validado=True,
        validado_por=secretaria,
        data_validacao=date(2025, 12, 5),
    )
    ok(f"Histórico Escolar emitido: {historico.numero_protocolo}")

    # ─── 13. CERTIFICADO / DIPLOMA ────────────────────────────────────────
    titulo("13. CONCLUSÃO — Emissão do Certificado")

    certificado = CertificadoDiploma.objects.create(
        matricula=matricula,
        tipo="CERTIFICADO",
        data_emissao=date(2025, 12, 10),
        data_entrega=date(2025, 12, 15),
        status="ENTREGUE",
        emitido_por=secretaria,
        observacao="Certificado de Conclusão do Curso Técnico em Auxiliar Administrativo.",
    )
    ok(f"Certificado emitido: {certificado.numero_registro}")
    info(f"Tipo: {certificado.get_tipo_display()} | Status: {certificado.get_status_display()}")
    info(f"Emissão: {certificado.data_emissao} | Entrega: {certificado.data_entrega}")

    # Atualizar status da matrícula para CONCLUÍDA
    matricula.status = "CONCLUIDA"
    matricula.save()
    ok(f"Matrícula encerrada como: {matricula.get_status_display()}")

    # ── Diploma Escolar (Documento Formal) ─────────────────────────────────
    diploma = DiplomaEscolar.objects.create(
        certificado=certificado,
        nome_completo=aluno.get_full_name(),
        data_nascimento=date(2000, 5, 15),
        local_nascimento="Porto Velho – RO",
        nome_pai="José da Silva",
        nome_mae="Maria Aparecida Silva",
        cpf="123.456.789-01",
        rg="1234567-0 SSP/RO",
        curso_nome=curso.nome,
        habilitacao="Técnico em Auxiliar Administrativo",
        carga_horaria=curso.carga_horaria,
        data_inicio_curso=date(2025, 2, 3),
        data_conclusao=date(2025, 12, 5),
        media_final=consolidacao.media_final,
        unidade_nome=unidade.nome,
        municipio_uf=f"{unidade.cidade} – {unidade.uf}",
        diretor_nome="Maria Auxiliadora Campos",
        diretor_cargo="Diretora",
        secretario_nome="Maria Secretaria",
        data_emissao=certificado.data_emissao,
    )
    ok(f"Diploma Escolar registrado: {diploma.numero_diploma}")
    info(f"Código de verificação: {diploma.codigo_verificacao}")

    # ─── 14. ARQUIVO E CONFORMIDADE ───────────────────────────────────────
    titulo("14. ARQUIVO E CONFORMIDADE — Guarda Documental")

    plano_cert, _ = PlanoClassificacao.objects.get_or_create(
        codigo="CERT-CONCL",
        defaults=dict(descricao="Certificados de Conclusão", prazo_guarda_anos=50, destinacao="GUARDA_PERMANENTE"),
    )
    guarda = GuardaDocumental.objects.create(
        tipo_documento="HISTORICO",
        descricao=f"Dossiê de conclusão – {aluno.get_full_name()} / TAA 2025/1",
        matricula=matricula,
        numero_caixa="CX-2025-TAA-001",
        localizacao="Arquivo Central – Prateleira A / Gaveta 3",
        status="ATIVO",
        plano_classificacao=plano_cert,
        responsavel=secretaria,
    )
    ok(f"Guarda documental: {guarda.numero_registro}")
    info(f"Localização: {guarda.localizacao}")

    # ─── RESUMO FINAL ─────────────────────────────────────────────────────
    titulo("RESUMO DO TESTE — FLUXO COMPLETO")
    print(f"""
  Aluno          : {aluno.get_full_name()} ({aluno.username})
  CPF            : {aluno.cpf}
  Professor      : {professor.get_full_name()} ({professor.username})
  Curso          : {curso.nome}
  Turma          : {turma.nome} | Turno: Manhã
  Inscrição      : {inscricao.numero_inscricao} [{inscricao.get_status_display()}]
  Matrícula      : #{matricula.pk} [{matricula.get_status_display()}]
  Média Final    : {consolidacao.media_final}
  Frequência     : {consolidacao.percentual_frequencia}%
  Situação       : {consolidacao.get_situacao_display()}
  Comprovante    : {comprovante.numero_protocolo}
  Declaração Freq: {doc_freq.numero_protocolo}
  Histórico      : {historico.numero_protocolo}
  Certificado    : {certificado.numero_registro}
  Ata Escolar    : {ata_escolar.numero_documento}
  Diploma Escolar: {diploma.numero_diploma}
  Fluxo P01      : {fluxo.get_etapa_atual_display()} | Concluído: {fluxo.concluido}
  Fluxo P02      : {fluxo_p02.get_etapa_atual_display()} | Concluído: {fluxo_p02.concluido}
  Estágio        : {estagio.get_status_display()} | {estagio.carga_horaria_total}h
  Convênio       : {convenio.numero_convenio}
  Ata Resultado  : {ata.numero_ata}
  Guarda         : {guarda.numero_registro}
    """)
    print(f"{SEP}")
    print("  TODOS OS FLUXOS CONCLUÍDOS COM SUCESSO!")
    print(f"{SEP}\n")

    # ─── IMPRESSÃO DOS DOCUMENTOS OFICIAIS ────────────────────────────────
    titulo("DOCUMENTO OFICIAL — DIÁRIO DE CLASSE (SEDUC-RO)")
    print(diario.gerar_documento())

    titulo("DOCUMENTO OFICIAL — ATA ESCOLAR (SEDUC-RO)")
    print(ata_escolar.gerar_documento())

    titulo("DOCUMENTO OFICIAL — DIPLOMA ESCOLAR (SEDUC-RO)")
    print(diploma.gerar_documento())


if __name__ == "__main__":
    run()
