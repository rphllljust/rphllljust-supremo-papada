"""
Management command: python manage.py teste_fluxo
Testa o fluxo completo de um aluno desde a inscrição até o diploma.
Curso: Auxiliar Administrativo - Eixo: Gestão e Negócios
Matriz: Gestão de Recursos Humanos | Gestão Financeira | Logística | Marketing e Vendas
"""

from decimal import Decimal
from datetime import date

from django.core.management.base import BaseCommand
from django.utils import timezone


COMPONENTES_MATRIZ = [
    {"nome": "Gestão de Recursos Humanos", "carga_horaria": 80,  "ordem": 1},
    {"nome": "Gestão Financeira",          "carga_horaria": 80,  "ordem": 2},
    {"nome": "Logística",                  "carga_horaria": 60,  "ordem": 3},
    {"nome": "Marketing e Vendas",         "carga_horaria": 60,  "ordem": 4},
]

# Notas por componente: (desc, valor, peso)
NOTAS_POR_COMPONENTE = {
    "Gestão de Recursos Humanos": [
        ("Av. 1 - Recrutamento e Seleção",     Decimal("8.5"), Decimal("1")),
        ("Av. 2 - Gestão de Desempenho",       Decimal("7.5"), Decimal("1")),
        ("Av. Final - GRH",                    Decimal("8.0"), Decimal("2")),
    ],
    "Gestão Financeira": [
        ("Av. 1 - Fluxo de Caixa",             Decimal("7.0"), Decimal("1")),
        ("Av. 2 - Análise de Balanço",         Decimal("8.0"), Decimal("1")),
        ("Av. Final - Financeira",             Decimal("9.0"), Decimal("2")),
    ],
    "Logística": [
        ("Av. 1 - Cadeia de Suprimentos",      Decimal("9.0"), Decimal("1")),
        ("Av. 2 - Gestão de Estoques",         Decimal("8.5"), Decimal("1")),
        ("Av. Final - Logística",              Decimal("9.5"), Decimal("2")),
    ],
    "Marketing e Vendas": [
        ("Av. 1 - Fundamentos de Marketing",   Decimal("7.5"), Decimal("1")),
        ("Av. 2 - Técnicas de Vendas",         Decimal("8.0"), Decimal("1")),
        ("Av. Final - Marketing",              Decimal("8.5"), Decimal("2")),
    ],
}


class Command(BaseCommand):
    help = "Teste de ponta a ponta: Auxiliar Administrativo - Gestão e Negócios."

    def handle(self, *args, **options):
        self.SEP = "=" * 70

        from apps.unidades.models import Unidade
        from apps.cursos.models import Curso, CalendarioLetivo, ComponenteCurricular
        from apps.turmas.models import Turma, DiarioAcademico
        from apps.usuarios.models import Usuario
        from apps.matriculas.models import (
            Matricula, DocumentoMatricula, DocumentoEmitido,
            RegraAcademica, ConsolidacaoAcademica,
            FluxoMatricula, EtapaFluxo,
            FluxoEmissaoDocumento, EtapaFluxoEmissao,
            AproveitamentoComponente, ConselhoClasse,
            AtaResultado, CertificadoDiploma,
        )
        from apps.notas.models import Nota
        from apps.frequencia.models import Frequencia
        from apps.processos.models import Processo
        from apps.arquivo.models import GuardaDocumental, PlanoClassificacao
        from apps.inscricoes.models import (
            PublicacaoInscricao, Inscricao, DocumentoInscricao,
            ProcessoSeletivo, Candidato,
        )
        from apps.estagio.models import (
            Convenio, Estagio, TermoCompromisso, AcompanhamentoEstagio,
        )

        # ── LIMPEZA ───────────────────────────────────────────────────────
        self._titulo("LIMPANDO DADOS DO TESTE ANTERIOR")
        Usuario.objects.filter(username__in=[
            "joao.silva.teste", "secretaria.teste", "professor.teste"
        ]).delete()
        Usuario.objects.filter(cpf__in=[
            "12345678901", "00000000001", "00000000002"
        ]).delete()
        Unidade.objects.filter(nome="ETEC IDEP - Teste").delete()
        self._ok("Limpeza concluida")

        # ── 1. INFRAESTRUTURA ─────────────────────────────────────────────
        self._titulo("1. INFRAESTRUTURA - Unidade / Curso / Matriz / Turma")

        unidade = Unidade.objects.create(
            nome="ETEC IDEP - Teste",
            endereco="Av. das Flores, 100",
            cidade="Porto Velho",
            uf="RO",
        )
        self._ok(f"Unidade: {unidade}")

        curso = Curso.objects.create(
            unidade=unidade,
            nome="Técnico em Auxiliar Administrativo",
            eixo_tecnologico="Gestão e Negócios",
            carga_horaria=800,
        )
        self._ok(f"Curso   : {curso.nome}")
        self._ok(f"Eixo    : {curso.eixo_tecnologico}")

        # Matriz curricular
        self._titulo("1a. MATRIZ CURRICULAR")
        componentes = []
        for c in COMPONENTES_MATRIZ:
            comp = ComponenteCurricular.objects.create(
                curso=curso,
                nome=c["nome"],
                carga_horaria=c["carga_horaria"],
                ordem=c["ordem"],
            )
            componentes.append(comp)
            self._info(f"  [{comp.ordem}] {comp.nome:40s}  {comp.carga_horaria}h")
        total_ch = sum(c["carga_horaria"] for c in COMPONENTES_MATRIZ)
        self._ok(f"Matriz: {len(componentes)} componentes | {total_ch}h na grade")

        CalendarioLetivo.objects.create(
            ano_letivo="2025/1",
            curso=curso,
            data_inicio=date(2025, 2, 3),
            data_fim=date(2025, 12, 5),
            dias_letivos=200,
            status="VIGENTE",
        )
        self._ok("Calendário letivo 2025/1 criado")

        RegraAcademica.objects.create(
            curso=curso,
            media_minima=Decimal("6.0"),
            frequencia_minima=Decimal("75.0"),
        )
        self._ok("Regra academica: media >= 6,0 | freq >= 75%")

        secretaria = Usuario.objects.create_user(
            username="secretaria.teste", password="senha123",
            cpf="00000000001", tipo="SECRETARIA",
            first_name="Maria", last_name="Secretaria",
        )
        self._ok(f"Usuário Secretaria: {secretaria}")

        professor = Usuario.objects.create_user(
            username="professor.teste", password="senha123",
            cpf="00000000002", tipo="PROFESSOR",
            first_name="Carlos", last_name="Professor",
        )
        self._ok(f"Usuário Professor: {professor}")

        turma = Turma.objects.create(
            curso=curso, nome="TAA-2025-A",
            ano_letivo=2025, professor_responsavel=professor,
        )
        self._ok(f"Turma: {turma}")

        aluno = Usuario.objects.create_user(
            username="joao.silva.teste", password="senha123",
            cpf="12345678901", tipo="ALUNO",
            first_name="João", last_name="Silva",
        )
        self._ok(f"Aluno: {aluno.get_full_name()} ({aluno.username})")

        # ── 2. CAPTAÇÃO / PUBLICAÇÃO ──────────────────────────────────────
        self._titulo("2. CAPTAÇÃO - Publicação de Inscrições")

        publicacao = PublicacaoInscricao.objects.create(
            curso=curso,
            titulo="Processo Seletivo TAA 2025/1",
            descricao="Técnico em Auxiliar Administrativo - 40 vagas. Ensino Médio completo.",
            vagas=40,
            data_inicio=date(2025, 1, 6),
            data_fim=date(2025, 1, 31),
            status="PUBLICADO",
            publicado_por=secretaria,
        )
        self._ok(f"Edital publicado: {publicacao.titulo}")
        self._info(f"Vagas: {publicacao.vagas} | Período: {publicacao.data_inicio} a {publicacao.data_fim}")

        # ── 3. INSCRIÇÃO ──────────────────────────────────────────────────
        self._titulo("3. INSCRIÇÃO - Receber e Validar")

        inscricao = Inscricao.objects.create(
            publicacao=publicacao,
            nome_candidato="João Silva",
            cpf="12345678901",
            email="joao.silva@email.com",
            telefone="65 99999-0001",
            data_nascimento=date(2000, 5, 15),
            status="PENDENTE",
            usuario=aluno,
        )
        self._ok(f"Inscrição registrada: {inscricao.numero_inscricao}")

        for tipo in ["RG", "CPF", "HISTORICO_ESCOLAR"]:
            DocumentoInscricao.objects.create(
                inscricao=inscricao, tipo=tipo,
                entregue=True, data_entrega=date(2025, 1, 10),
            )
            self._info(f"Documento entregue: {tipo}")

        inscricao.status = "VALIDADA"
        inscricao.save()
        self._ok(f"Inscrição validada -> {inscricao.get_status_display()}")

        # ── 4. SELEÇÃO / CONVOCAÇÃO ───────────────────────────────────────
        self._titulo("4. SELEÇÃO / CONVOCAÇÃO")

        seletivo = ProcessoSeletivo.objects.create(
            publicacao=publicacao,
            modalidade="DEMANDA_ESPONTANEA",
            data_realizacao=date(2025, 2, 1),
            data_resultado=date(2025, 2, 3),
            status="CONCLUIDO",
            criterios="Ordem de inscrição; documentação completa.",
            resultado="1º João Silva - CONVOCADO",
            responsavel=secretaria,
        )
        self._ok(f"Processo seletivo: {seletivo.get_modalidade_display()} | {seletivo.get_status_display()}")

        candidato = Candidato.objects.create(
            processo=seletivo, inscricao=inscricao,
            classificacao=1, pontuacao=Decimal("10.0"),
            situacao="CONVOCADO", data_convocacao=date(2025, 2, 3),
        )
        self._ok(f"Candidato convocado: {candidato}")

        # ── 5. MATRÍCULA INICIAL - Fluxo P01 ─────────────────────────────
        self._titulo("5. MATRÍCULA INICIAL - Fluxo P01 (8 etapas)")

        fluxo = FluxoMatricula.objects.create(
            aluno=aluno, tipo_matricula="NOVA",
            etapa_atual="REQUERIMENTO_RECEBIDO",
            observacoes="Aluno convocado pelo processo seletivo TAA 2025/1.",
        )
        EtapaFluxo.objects.create(fluxo=fluxo, etapa="REQUERIMENTO_RECEBIDO",
                                   responsavel=secretaria, observacao="Requerimento recebido.")
        self._ok(f"P01 iniciado: {fluxo.get_etapa_atual_display()}")

        matricula = Matricula.objects.create(
            aluno=aluno, curso=curso, turma=turma,
            tipo_matricula="NOVA", status="ATIVA", turno="MANHA",
        )
        fluxo.matricula = matricula
        fluxo.save()
        self._ok(f"Matrícula #{matricula.pk} criada e vinculada ao fluxo")

        fluxo.avancar("DOCUMENTOS_CONFERIDOS")
        EtapaFluxo.objects.create(fluxo=fluxo, etapa="DOCUMENTOS_CONFERIDOS", responsavel=secretaria)
        self._ok(f"Etapa: {fluxo.get_etapa_atual_display()}")

        for tipo_doc, ok_flag in [
            ("RG", True), ("CPF", True), ("COMPROVANTE_RESIDENCIA", True),
            ("HISTORICO_ESCOLAR", True), ("FOTO", True), ("CERTIDAO_NASCIMENTO", True),
        ]:
            DocumentoMatricula.objects.create(
                matricula=matricula, tipo_documento=tipo_doc,
                entregue=ok_flag, data_entrega=date(2025, 2, 10),
            )
            self._info(f"  Doc matrícula: {tipo_doc} ({'OK' if ok_flag else 'X'})")

        fluxo.avancar("REQUISITOS_VALIDADOS")
        EtapaFluxo.objects.create(fluxo=fluxo, etapa="REQUISITOS_VALIDADOS",
                                   responsavel=secretaria, observacao="Documentação completa.")
        self._ok(f"Etapa: {fluxo.get_etapa_atual_display()}")

        fluxo.avancar("MATRICULA_REGISTRADA")
        EtapaFluxo.objects.create(fluxo=fluxo, etapa="MATRICULA_REGISTRADA", responsavel=secretaria)
        self._ok(f"Etapa: {fluxo.get_etapa_atual_display()}")

        fluxo.avancar("ALUNO_ENTURMADO")
        EtapaFluxo.objects.create(fluxo=fluxo, etapa="ALUNO_ENTURMADO",
                                   responsavel=secretaria, observacao="Turno Manhã | TAA-2025-A")
        self._ok(f"Etapa: {fluxo.get_etapa_atual_display()}")

        comprovante = DocumentoEmitido.objects.create(
            matricula=matricula, tipo="DECLARACAO_MATRICULA",
            observacao="Comprovante P01 - gerado automaticamente.",
        )
        fluxo.documento_comprovante = comprovante
        fluxo.avancar("COMPROVANTE_EMITIDO")
        EtapaFluxo.objects.create(fluxo=fluxo, etapa="COMPROVANTE_EMITIDO",
                                   responsavel=secretaria,
                                   observacao=f"Protocolo: {comprovante.numero_protocolo}")
        self._ok(f"Comprovante emitido: {comprovante.numero_protocolo}")

        plano_pasta, _ = PlanoClassificacao.objects.get_or_create(
            codigo="PASTAS-ALUNO",
            defaults=dict(descricao="Pastas de Alunos", prazo_guarda_anos=10,
                          destinacao="GUARDA_PERMANENTE"),
        )
        GuardaDocumental.objects.create(
            tipo_documento="PASTA_ALUNO",
            descricao=f"Pasta de matrícula - {aluno.get_full_name()}",
            matricula=matricula, responsavel=secretaria,
            plano_classificacao=plano_pasta,
        )
        fluxo.avancar("ARQUIVADO")
        EtapaFluxo.objects.create(fluxo=fluxo, etapa="ARQUIVADO", responsavel=secretaria)
        self._ok(f"P01 CONCLUÍDO: {fluxo.get_etapa_atual_display()} | concluido={fluxo.concluido}")

        # ── 6. DIÁRIOS - um por componente da matriz ──────────────────────
        self._titulo("6. ORGANIZAÇÃO ACADÊMICA - Diário por Componente")

        diarios = {}
        for comp in componentes:
            d = DiarioAcademico.objects.create(
                turma=turma,
                periodo="2025/1",
                componente_curricular=comp.nome,
                status="ABERTO",
                observacoes=f"Diário de {comp.nome}",
                aberto_por=secretaria,
            )
            diarios[comp.nome] = d
            self._ok(f"Diário aberto: {comp.nome}")

        # ── 7. NOTAS E FREQUÊNCIA - por componente ────────────────────────
        self._titulo("7. EXECUÇÃO LETIVA - Notas por Componente e Frequência")

        from datetime import timedelta
        base = date(2025, 3, 1)
        todas_notas_registradas = []

        for comp in componentes:
            self._info(f"\n  Componente: {comp.nome}")
            for i, (desc, valor, peso) in enumerate(NOTAS_POR_COMPONENTE[comp.nome]):
                n = Nota.objects.create(
                    matricula=matricula,
                    descricao=f"[{comp.nome[:20]}] {desc}",
                    valor=valor,
                    peso=peso,
                    data_lancamento=base + timedelta(weeks=comp.ordem * 4 + i),
                )
                todas_notas_registradas.append(n)
                self._info(f"    {desc:<45} = {valor}  (peso {peso})")

        # Frequência geral (20 dias letivos)
        for i in range(20):
            Frequencia.objects.create(
                matricula=matricula,
                data=base + timedelta(days=i * 5),
                presente=(i < 17),
                observacao="" if i < 17 else "Falta justificada",
            )
        pres = Frequencia.objects.filter(matricula=matricula, presente=True).count()
        tot  = Frequencia.objects.filter(matricula=matricula).count()
        self._ok(f"Frequência: {pres}/{tot} presenças ({pres/tot*100:.1f}%)")

        # Consolidação acadêmica
        consolidacao, _ = ConsolidacaoAcademica.objects.get_or_create(matricula=matricula)
        consolidacao.consolidar()
        self._ok(
            f"Consolidação -> média={consolidacao.media_final} | "
            f"freq={consolidacao.percentual_frequencia}% | "
            f"situação={consolidacao.get_situacao_display()}"
        )

        # ── 8. QUADRO DE NOTAS POR COMPONENTE ────────────────────────────
        self._titulo("8. QUADRO DE NOTAS - Aluno: " + aluno.get_full_name())

        W = 70
        self.stdout.write("  " + "─" * W)
        self.stdout.write(
            f"  {'COMPONENTE CURRICULAR':<38}  {'Av1':>5}  {'Av2':>5}  {'AvF':>5}  {'MÉDIA':>6}"
        )
        self.stdout.write("  " + "─" * W)

        medias_por_componente = {}
        for comp in componentes:
            notas_comp = [n for n in todas_notas_registradas
                          if n.descricao.startswith(f"[{comp.nome[:20]}]")]
            # calcular média ponderada
            soma_pond = sum(n.valor * n.peso for n in notas_comp)
            soma_peso = sum(n.peso for n in notas_comp)
            media_comp = soma_pond / soma_peso if soma_peso else Decimal("0")
            medias_por_componente[comp.nome] = media_comp

            vals = [f"{n.valor:.1f}".replace(".", ",") for n in notas_comp]
            while len(vals) < 3:
                vals.append("---")

            self.stdout.write(
                f"  {comp.nome:<38}  {vals[0]:>5}  {vals[1]:>5}  {vals[2]:>5}  "
                f"{str(media_comp.quantize(Decimal('0.1'))).replace('.', ','):>6}"
            )

        self.stdout.write("  " + "─" * W)
        media_geral = sum(medias_por_componente.values()) / len(medias_por_componente)
        self.stdout.write(
            f"  {'MÉDIA GERAL (consolidada)':<38}  {'':>5}  {'':>5}  {'':>5}  "
            f"{str(media_geral.quantize(Decimal('0.1'))).replace('.', ','):>6}"
        )
        self.stdout.write("  " + "─" * W)

        # ── 9. APROVEITAMENTO ─────────────────────────────────────────────
        self._titulo("9. MOVIMENTAÇÕES - Aproveitamento de Componente")

        aprov = AproveitamentoComponente.objects.create(
            matricula=matricula,
            componente_origem="Informática Básica",
            instituicao_origem="SENAC-RO",
            carga_horaria=40,
            componente_destino="Tecnologia da Informação Aplicada",
            status="APROVADO",
            data_decisao=date(2025, 4, 1),
            decisao_por=secretaria,
            justificativa="Componente equivalente validado pela coordenação pedagógica.",
        )
        self._ok(f"Aproveitamento: {aprov.componente_origem} -> {aprov.componente_destino} [{aprov.get_status_display()}]")

        # ── 10. DECLARAÇÃO DE FREQUÊNCIA - Fluxo P02 ─────────────────────
        self._titulo("10. EXECUÇÃO - Declaração de Frequência (Fluxo P02)")

        fluxo_p02 = FluxoEmissaoDocumento.objects.create(
            solicitante=aluno, matricula=matricula,
            tipo_documento="DECLARACAO_FREQUENCIA",
            etapa_atual="PROTOCOLO_ABERTO",
            observacoes="Solicitação para apresentação ao empregador.",
        )
        proc_p02 = Processo.objects.create(
            tipo="REQUERIMENTO", requerente=aluno,
            assunto=f"Declaração de Frequência - {aluno.get_full_name()}",
            descricao=fluxo_p02.observacoes,
        )
        fluxo_p02.processo = proc_p02
        fluxo_p02.save()
        EtapaFluxoEmissao.objects.create(fluxo=fluxo_p02, etapa="PROTOCOLO_ABERTO",
                                          responsavel=secretaria,
                                          observacao=f"Protocolo: {proc_p02.numero}")
        self._ok(f"P02 iniciado - protocolo: {proc_p02.numero}")

        elegivel = fluxo_p02.verificar_elegibilidade()
        fluxo_p02.avancar("ELEGIBILIDADE_VERIFICADA")
        EtapaFluxoEmissao.objects.create(fluxo=fluxo_p02, etapa="ELEGIBILIDADE_VERIFICADA",
                                          responsavel=secretaria)
        self._ok(f"Elegibilidade: {'Apto' if elegivel else 'Inapto - ' + fluxo_p02.motivo_inelegivel}")

        doc_freq = DocumentoEmitido.objects.create(
            matricula=matricula, tipo="DECLARACAO_FREQUENCIA",
            observacao=f"Gerado pelo Fluxo P02 - {proc_p02.numero}",
        )
        fluxo_p02.documento_emitido = doc_freq
        fluxo_p02.save()
        fluxo_p02.avancar("DOCUMENTO_GERADO")
        EtapaFluxoEmissao.objects.create(fluxo=fluxo_p02, etapa="DOCUMENTO_GERADO",
                                          observacao=f"Documento: {doc_freq.numero_protocolo}")
        self._ok(f"Declaração gerada: {doc_freq.numero_protocolo}")

        doc_freq.validado = True
        doc_freq.validado_por = secretaria
        doc_freq.data_validacao = date(2025, 5, 10)
        doc_freq.entregue = True
        doc_freq.data_entrega = date(2025, 5, 10)
        doc_freq.recebido_por = "João Silva (pessoalmente)"
        doc_freq.save()
        fluxo_p02.avancar("DOCUMENTO_VALIDADO")
        EtapaFluxoEmissao.objects.create(fluxo=fluxo_p02, etapa="DOCUMENTO_VALIDADO",
                                          responsavel=secretaria)
        fluxo_p02.avancar("ENTREGA_REGISTRADA")
        EtapaFluxoEmissao.objects.create(fluxo=fluxo_p02, etapa="ENTREGA_REGISTRADA",
                                          responsavel=secretaria,
                                          observacao=f"Entregue a: {doc_freq.recebido_por}")
        fluxo_p02.avancar("ARQUIVADO")
        fluxo_p02.concluido = True
        fluxo_p02.save()
        self._ok(f"P02 CONCLUÍDO: {fluxo_p02.get_etapa_atual_display()}")

        # ── 11. ESTÁGIO ───────────────────────────────────────────────────
        self._titulo("11. ESTÁGIO - Convênio / TCE / Acompanhamento / Encerramento")

        convenio = Convenio.objects.create(
            empresa="Contabilidade Rápida Ltda",
            cnpj="12.345.678/0001-99",
            responsavel_empresa="Ana Paula Moreira",
            email_empresa="rh@contabilidaderap.com.br",
            telefone_empresa="65 3333-0001",
            data_assinatura=date(2025, 2, 1),
            data_vencimento=date(2026, 1, 31),
            status="VIGENTE",
            objeto="Vagas de estágio obrigatório para alunos do TAA.",
            responsavel_idep=secretaria,
        )
        self._ok(f"Convênio: {convenio}")

        estagio = Estagio.objects.create(
            matricula=matricula, convenio=convenio,
            modalidade="OBRIGATORIO",
            empresa="Contabilidade Rápida Ltda",
            supervisor_empresa="Ana Paula Moreira",
            orientador_idep=professor,
            carga_horaria_total=200, carga_horaria_semanal=20,
            data_inicio=date(2025, 7, 1),
            data_fim_prevista=date(2025, 11, 28),
            status="EM_ANDAMENTO",
            bolsa_mensal=Decimal("600.00"),
            seguro_numero="SEG-2025-00123",
        )
        self._ok(f"Estágio: {estagio}")

        termo = TermoCompromisso.objects.create(
            estagio=estagio, data_assinatura=date(2025, 6, 25),
            status="ASSINADO",
            assinado_aluno=True, assinado_empresa=True, assinado_idep=True,
        )
        self._ok(f"TCE assinado: {termo.numero_termo}")

        AcompanhamentoEstagio.objects.create(
            estagio=estagio, tipo="VISITA", data=date(2025, 8, 15),
            descricao="Visita ao local. Desempenho satisfatório. Adaptação ótima.",
            registrado_por=professor,
        )
        self._ok("Acompanhamento 1: Visita ao Local (ago/2025)")

        AcompanhamentoEstagio.objects.create(
            estagio=estagio, tipo="RELATORIO", data=date(2025, 10, 10),
            descricao="Relatório parcial entregue. 120h cumpridas.",
            registrado_por=professor,
        )
        self._ok("Acompanhamento 2: Relatório do Estagiário (out/2025)")

        estagio.status = "CONCLUIDO"
        estagio.data_fim_real = date(2025, 11, 28)
        estagio.observacao = "Estágio concluído. 200h integralizadas com sucesso."
        estagio.save()
        self._ok(f"Estágio encerrado: {estagio.get_status_display()} em {estagio.data_fim_real}")

        # ── 12. FECHAMENTO - Diários / Conselho / Ata ─────────────────────
        self._titulo("12. FECHAMENTO - Fechar Diários / Conselho / Ata")

        for comp in componentes:
            d = diarios[comp.nome]
            d.status = "FECHADO"
            d.data_fechamento = date(2025, 12, 1)
            d.fechado_por = secretaria
            d.save()
            self._ok(f"Diário fechado: {comp.nome}")

        conselho = ConselhoClasse.objects.create(
            turma=turma, periodo="2025/1",
            data_reuniao=date(2025, 12, 3), status="REALIZADO",
            pauta=(
                "1. Análise de notas e frequências - TAA-2025-A\n"
                "2. Aprovação de alunos para emissão de certificado\n"
                "3. Publicação de resultados"
            ),
            ata=(
                "Conselho realizado em 03/12/2025.\n"
                "João Silva: média " + str(media_geral.quantize(Decimal("0.01"))) +
                " / freq 85% -> APROVADO para certificação."
            ),
            responsavel=secretaria,
        )
        self._ok(f"Conselho de Classe: {conselho}")

        # ── 13. ATA DE RESULTADO ──────────────────────────────────────────
        self._titulo("13. ATA DE RESULTADO")

        # Monta quadro de notas para a ata
        linhas_ata = []
        linhas_ata.append(f"{'COMPONENTE CURRICULAR':<38}  {'Av1':>5}  {'Av2':>5}  {'AvF':>5}  {'MÉDIA':>6}")
        linhas_ata.append("─" * 62)
        for comp in componentes:
            notas_comp = [n for n in todas_notas_registradas
                          if n.descricao.startswith(f"[{comp.nome[:20]}]")]
            vals = [f"{n.valor:.1f}" for n in notas_comp]
            while len(vals) < 3:
                vals.append("---")
            m = medias_por_componente[comp.nome]
            linhas_ata.append(
                f"{comp.nome:<38}  {vals[0]:>5}  {vals[1]:>5}  {vals[2]:>5}  "
                f"{str(m.quantize(Decimal('0.1'))):>6}"
            )
        linhas_ata.append("─" * 62)
        linhas_ata.append(
            f"{'MÉDIA GERAL':<38}  {'':>5}  {'':>5}  {'':>5}  "
            f"{str(media_geral.quantize(Decimal('0.1'))):>6}"
        )

        quadro_notas = "\n".join(linhas_ata)

        ata = AtaResultado.objects.create(
            conselho=conselho,
            data_publicacao=date(2025, 12, 4),
            conteudo=(
                f"ATA DE RESULTADO - TAA-2025-A / 2025.1\n"
                f"Eixo Tecnológico: {curso.eixo_tecnologico}\n\n"
                f"Aluno         : {aluno.get_full_name()}\n"
                f"Matrícula nº  : {matricula.pk}\n"
                f"Frequência    : {consolidacao.percentual_frequencia}%\n"
                f"Estágio       : {estagio.get_status_display()} ({estagio.carga_horaria_total}h)\n\n"
                f"QUADRO DE NOTAS POR COMPONENTE:\n\n"
                f"{quadro_notas}\n\n"
                f"Média Final Consolidada: {consolidacao.media_final}\n"
                f"Situação: {consolidacao.get_situacao_display()}\n\n"
                "RESULTADO: APROVADO para emissão de Certificado de Conclusão."
            ),
            publicado_por=secretaria,
        )
        self._ok(f"Ata publicada: {ata.numero_ata}")

        # Exibe a ata completa
        self.stdout.write("")
        self.stdout.write(self.style.HTTP_INFO("  " + "─" * 68))
        for linha in ata.conteudo.split("\n"):
            self.stdout.write(f"  {linha}")
        self.stdout.write(self.style.HTTP_INFO("  " + "─" * 68))

        # ── 14. HISTÓRICO ESCOLAR ─────────────────────────────────────────
        self._titulo("14. CONCLUSÃO - Histórico Escolar Final")

        historico = DocumentoEmitido.objects.create(
            matricula=matricula, tipo="HISTORICO_ESCOLAR",
            observacao="Histórico final - emitido após aprovação em Conselho de Classe.",
            validado=True, validado_por=secretaria,
            data_validacao=date(2025, 12, 5),
        )
        self._ok(f"Histórico Escolar: {historico.numero_protocolo}")

        # ── 15. DIPLOMA ───────────────────────────────────────────────────
        self._titulo("15. CONCLUSÃO - Emissão do Diploma / Certificado")

        matricula.status = "CONCLUIDA"
        matricula.save()
        self._ok(f"Matrícula encerrada: {matricula.get_status_display()}")

        certificado = CertificadoDiploma.objects.create(
            matricula=matricula,
            tipo="CERTIFICADO",
            data_emissao=date(2025, 12, 10),
            data_entrega=date(2025, 12, 15),
            status="ENTREGUE",
            emitido_por=secretaria,
            observacao=(
                f"CERTIFICADO DE CONCLUSÃO\n"
                f"Curso: {curso.nome}\n"
                f"Eixo Tecnológico: {curso.eixo_tecnologico}\n"
                f"Matriz Curricular: {' | '.join(c.nome for c in componentes)}\n"
                f"Carga Horária Total: {curso.carga_horaria}h | Estágio: {estagio.carga_horaria_total}h\n"
                f"Aluno: {aluno.get_full_name()}\n"
                f"Média Final: {consolidacao.media_final} | Frequência: {consolidacao.percentual_frequencia}%\n"
                f"Situação: {consolidacao.get_situacao_display()}"
            ),
        )
        self._ok(f"Certificado/Diploma emitido: {certificado.numero_registro}")
        self._info(f"Tipo: {certificado.get_tipo_display()} | Status: {certificado.get_status_display()}")
        self._info(f"Emissão: {certificado.data_emissao} | Entregue: {certificado.data_entrega}")

        # Exibe o diploma
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("  " + "=" * 68))
        self.stdout.write(self.style.SUCCESS("  " + " " * 20 + "C E R T I F I C A D O"))
        self.stdout.write(self.style.SUCCESS("  " + "=" * 68))
        for linha in certificado.observacao.split("\n"):
            self.stdout.write(self.style.SUCCESS(f"  {linha}"))
        self.stdout.write(self.style.SUCCESS("  " + "=" * 68))

        # ── 16. ARQUIVO E CONFORMIDADE ────────────────────────────────────
        self._titulo("16. ARQUIVO E CONFORMIDADE - Guarda Documental Final")

        plano_cert, _ = PlanoClassificacao.objects.get_or_create(
            codigo="CERT-CONCL",
            defaults=dict(descricao="Certificados de Conclusão", prazo_guarda_anos=50,
                          destinacao="GUARDA_PERMANENTE"),
        )
        guarda = GuardaDocumental.objects.create(
            tipo_documento="HISTORICO",
            descricao=f"Dossiê de conclusão - {aluno.get_full_name()} / TAA 2025/1",
            matricula=matricula,
            numero_caixa="CX-2025-TAA-001",
            localizacao="Arquivo Central - Prateleira A / Gaveta 3",
            status="ATIVO",
            plano_classificacao=plano_cert,
            responsavel=secretaria,
        )
        self._ok(f"Guarda documental: {guarda.numero_registro}")
        self._info(f"Local: {guarda.localizacao} | Caixa: {guarda.numero_caixa}")

        # ── RESUMO FINAL ──────────────────────────────────────────────────
        self._titulo("RESUMO DO FLUXO COMPLETO")
        self.stdout.write(self.style.SUCCESS(f"""
  Aluno            : {aluno.get_full_name()} ({aluno.username})
  Curso            : {curso.nome} ({curso.carga_horaria}h)
  Eixo Tecnológico : {curso.eixo_tecnologico}
  Matriz           : {' | '.join(c.nome for c in componentes)}
  Turma            : {turma.nome} | Turno: Manhã

  Inscrição        : {inscricao.numero_inscricao} [{inscricao.get_status_display()}]
  Matrícula nº     : {matricula.pk} [{matricula.get_status_display()}]

  Notas por componente:
"""))
        for comp in componentes:
            m = medias_por_componente[comp.nome]
            self.stdout.write(self.style.SUCCESS(
                f"    {comp.nome:<38}  média: {str(m.quantize(Decimal('0.1'))):>5}"
            ))
        self.stdout.write(self.style.SUCCESS(f"""
  Média Final      : {consolidacao.media_final}
  Frequência       : {consolidacao.percentual_frequencia}%
  Situação Acad.   : {consolidacao.get_situacao_display()}

  Estágio          : {estagio.empresa} | {estagio.carga_horaria_total}h | {estagio.get_status_display()}
  Conselho Classe  : {conselho} [{conselho.get_status_display()}]
  Ata de Resultado : {ata.numero_ata}
  Histórico Final  : {historico.numero_protocolo}
  Certificado      : {certificado.numero_registro} [{certificado.get_status_display()}]
  Guarda Documental: {guarda.numero_registro} | {guarda.localizacao}
"""))
        self.stdout.write(self.style.SUCCESS(self.SEP))
        self.stdout.write(self.style.SUCCESS("  TODOS OS FLUXOS PERCORRIDOS COM SUCESSO!"))
        self.stdout.write(self.style.SUCCESS(self.SEP))

    # ── helpers ───────────────────────────────────────────────────────────────
    def _titulo(self, texto):
        self.stdout.write("")
        self.stdout.write(self.style.HTTP_INFO(self.SEP))
        self.stdout.write(self.style.HTTP_INFO(f"  {texto}"))
        self.stdout.write(self.style.HTTP_INFO(self.SEP))

    def _ok(self, msg):
        self.stdout.write(self.style.SUCCESS(f"  [OK] {msg}"))

    def _info(self, msg):
        self.stdout.write(f"       {msg}")
