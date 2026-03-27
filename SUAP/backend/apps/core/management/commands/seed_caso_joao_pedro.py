"""
Seed command for a full academic case:
Joao Pedro da Silva from enrollment to diploma issuance.

Usage:
    python manage.py seed_caso_joao_pedro --reset
"""

from __future__ import annotations

from datetime import date, time, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone


class Command(BaseCommand):
    help = (
        "Create a complete and realistic student flow (enrollment -> "
        "academic life -> completion -> diploma) for Joao Pedro da Silva."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete previous records from this seeded case before creating new ones.",
        )
        parser.add_argument(
            "--year",
            type=int,
            default=timezone.now().year,
            help="Reference school year for the generated case.",
        )
        parser.add_argument(
            "--cpf",
            default="00011122285",
            help=(
                "CPF used in system records (must be valid if login/auth is required). "
                "Default: 00011122285"
            ),
        )
        parser.add_argument(
            "--requested-cpf",
            default="00011122233",
            help="Original CPF requested for scenario documentation (can be invalid).",
        )
        parser.add_argument(
            "--password",
            default="Aluno@123",
            help="Password for student login account in this seeded scenario.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        year = options["year"]
        cpf = options["cpf"]
        requested_cpf = options["requested_cpf"]
        password = options["password"]
        tag = f"CASE-JPS-{year}"

        self.stdout.write(self.style.HTTP_INFO(f"Seeding scenario tag: {tag}"))

        if options["reset"]:
            self._reset_case_data(tag=tag, cpf=cpf, year=year)

        (
            unidade,
            curso,
            turma,
            _secretaria,
            _coordenacao,
            _professor,
            aluno_user,
            _aluno_model,
            _publicacao,
            inscricao,
            processo_seletivo,
            candidato,
            matricula,
            consolidacao,
            estagio,
            ata_resultado,
            historico_emitido,
            certificado_diploma,
            diploma_escolar,
            processo_diploma,
        ) = self._build_case(
            tag=tag,
            year=year,
            cpf=cpf,
            requested_cpf=requested_cpf,
            password=password,
        )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 84))
        self.stdout.write(self.style.SUCCESS("CASE READY - JOAO PEDRO DA SILVA"))
        self.stdout.write(self.style.SUCCESS("=" * 84))
        self.stdout.write(self.style.SUCCESS(f"Tag: {tag}"))
        self.stdout.write(self.style.SUCCESS(f"Unidade: {unidade.nome} ({unidade.codigo})"))
        self.stdout.write(self.style.SUCCESS(f"Curso: {curso.nome}"))
        self.stdout.write(self.style.SUCCESS(f"Turma: {turma.nome}"))
        self.stdout.write(self.style.SUCCESS(f"Aluno (usuario): {aluno_user.username}"))
        self.stdout.write(self.style.SUCCESS(f"Aluno (CPF no sistema): {cpf}"))
        self.stdout.write(self.style.SUCCESS(f"CPF solicitado no roteiro: {requested_cpf}"))
        self.stdout.write(self.style.SUCCESS(f"Inscricao: {inscricao.numero_inscricao} [{inscricao.status}]"))
        self.stdout.write(self.style.SUCCESS(f"Processo seletivo: {processo_seletivo.id} [{processo_seletivo.status}]"))
        self.stdout.write(self.style.SUCCESS(f"Candidato situacao: {candidato.situacao}"))
        self.stdout.write(self.style.SUCCESS(f"Matricula: {matricula.numero_matricula} [{matricula.status}]"))
        self.stdout.write(
            self.style.SUCCESS(
                f"Consolidacao: media={consolidacao.media_final} freq={consolidacao.percentual_frequencia}% "
                f"situacao={consolidacao.situacao}"
            )
        )
        self.stdout.write(self.style.SUCCESS(f"Estagio: {estagio.status} ({estagio.empresa})"))
        self.stdout.write(self.style.SUCCESS(f"Ata de resultado: {ata_resultado.numero_ata}"))
        self.stdout.write(self.style.SUCCESS(f"Historico final (DOC): {historico_emitido.numero_protocolo}"))
        self.stdout.write(
            self.style.SUCCESS(
                f"Diploma registro: {certificado_diploma.numero_registro} "
                f"(status={certificado_diploma.status})"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Diploma escolar: {diploma_escolar.numero_diploma} / "
                f"codigo={diploma_escolar.codigo_verificacao}"
            )
        )
        self.stdout.write(self.style.SUCCESS(f"Processo diploma: {processo_diploma.numero} [{processo_diploma.status}]"))
        self.stdout.write(self.style.SUCCESS("=" * 84))

        self.stdout.write("")
        self.stdout.write(
            self.style.WARNING(
                "Note: CPF 000.111.222-33 from the original text is invalid. "
                "Seed uses a valid CPF so authentication can work."
            )
        )

    def _reset_case_data(self, *, tag: str, cpf: str, year: int):
        from apps.cursos.models import Curso
        from apps.inscricoes.models import PublicacaoInscricao
        from apps.processos.models import Processo
        from apps.usuarios.models import Usuario

        usernames = [
            f"joao.pedro.{year}",
            f"secretaria.jps.{year}",
            f"coordenacao.jps.{year}",
            f"professor.jps.{year}",
        ]

        PublicacaoInscricao.objects.filter(titulo__icontains=tag).delete()
        Processo.objects.filter(assunto__icontains=tag).delete()
        Curso.objects.filter(nome__icontains=tag).delete()
        Usuario.objects.filter(username__in=usernames).delete()
        Usuario.objects.filter(cpf=cpf).delete()

        self.stdout.write(self.style.WARNING(f"Reset completed for tag {tag}."))

    def _build_case(self, *, tag: str, year: int, cpf: str, requested_cpf: str, password: str):
        from apps.arquivo.models import GuardaDocumental, PlanoClassificacao
        from apps.cursos.models import CalendarioLetivo, ComponenteCurricular, Curso, MatrizCurricular
        from apps.documentos.models import HistoricoEscolar, HistoricoEscolarDigital
        from apps.estagio.models import AcompanhamentoEstagio, Convenio, Estagio, TermoCompromisso
        from apps.frequencia.models import Frequencia
        from apps.inscricoes.models import (
            Candidato,
            ChamadaProcessoSeletivo,
            ConvocacaoCandidato,
            DocumentoInscricao,
            Inscricao,
            ProcessoSeletivo,
            PublicacaoInscricao,
        )
        from apps.matriculas.models import (
            AproveitamentoComponente,
            AtaEscolar,
            AtaResultado,
            CertificadoDiploma,
            ConselhoClasse,
            ConsolidacaoAcademica,
            DependenciaAcademica,
            DiplomaEscolar,
            DocumentoEmitido,
            DocumentoMatricula,
            EtapaFluxo,
            EtapaFluxoEmissao,
            FluxoEmissaoDocumento,
            FluxoMatricula,
            Matricula,
            RegraAcademica,
        )
        from apps.notas.models import Nota
        from apps.pedagogia.models import AtendimentoPedagogico
        from apps.processos.models import Processo, Tramitacao
        from apps.turmas.models import DiarioAcademico, Turma
        from apps.unidades.models import Unidade
        from apps.usuarios.models import Aluno, PerfilUsuario, Pessoa, Usuario

        start_date = date(year, 2, 10)
        course_end_date = date(year + 1, 6, 30)

        unidade, _ = Unidade.objects.get_or_create(
            codigo="sede",
            defaults={
                "nome": "Sede",
                "endereco": "Av. Principal, 1000",
                "cidade": "Porto Velho",
                "uf": "RO",
            },
        )
        unidade.endereco = "Av. Principal, 1000"
        unidade.cidade = "Porto Velho"
        unidade.uf = "RO"
        unidade.save(update_fields=["endereco", "cidade", "uf"])

        curso, _ = Curso.objects.get_or_create(
            unidade=unidade,
            nome=f"Tecnico em Administracao - {tag}",
            defaults={
                "tipo_curso": "tecnico",
                "sigla": "TAD",
                "eixo_tecnologico": "Gestao e Negocios",
                "carga_horaria": 1200,
            },
        )
        curso.tipo_curso = "tecnico"
        curso.sigla = "TAD"
        curso.eixo_tecnologico = "Gestao e Negocios"
        curso.carga_horaria = 1200
        curso.save(update_fields=["tipo_curso", "sigla", "eixo_tecnologico", "carga_horaria"])

        matriz, _ = MatrizCurricular.objects.get_or_create(
            curso_base=curso,
            ano_referencia=year,
            versao="1.0",
            defaults={
                "nome": f"Matriz {tag}",
                "status": "VIGENTE",
                "ativa": True,
                "descricao": "Matriz curricular criada para caso de uso completo.",
            },
        )
        matriz.nome = f"Matriz {tag}"
        matriz.status = "VIGENTE"
        matriz.ativa = True
        matriz.descricao = "Matriz curricular criada para caso de uso completo."
        matriz.save(update_fields=["nome", "status", "ativa", "descricao", "updated_at"])

        curso.matriz_curricular = matriz
        curso.save(update_fields=["matriz_curricular"])

        components = [
            ("Fundamentos da Administracao", 200, 1, "Modulo 1", 1),
            ("Gestao de Pessoas", 220, 1, "Modulo 1", 2),
            ("Processos Administrativos", 260, 2, "Modulo 2", 1),
            ("Empreendedorismo e Projeto Integrador", 260, 2, "Modulo 2", 2),
        ]
        componente_objs = []
        for order, (name, workload, module_number, module_name, order_in_module) in enumerate(components, start=1):
            component, _ = ComponenteCurricular.objects.get_or_create(
                matriz_curricular=matriz,
                nome=name,
                defaults={
                    "curso": curso,
                    "carga_horaria": workload,
                    "ordem": order,
                    "tipo_componente": "Disciplina",
                    "nivel_ensino": "Tecnico",
                    "modulo_numero": module_number,
                    "modulo_nome": module_name,
                    "ordem_no_modulo": order_in_module,
                },
            )
            component.curso = curso
            component.carga_horaria = workload
            component.ordem = order
            component.tipo_componente = "Disciplina"
            component.nivel_ensino = "Tecnico"
            component.modulo_numero = module_number
            component.modulo_nome = module_name
            component.ordem_no_modulo = order_in_module
            component.save()
            componente_objs.append(component)

        CalendarioLetivo.objects.update_or_create(
            ano_letivo=f"{year}/1",
            curso=curso,
            defaults={
                "data_inicio": start_date,
                "data_fim": date(year, 12, 10),
                "dias_letivos": 200,
                "status": "VIGENTE",
                "descricao": f"Calendario do caso {tag}",
            },
        )
        RegraAcademica.objects.update_or_create(
            curso=curso,
            defaults={"media_minima": Decimal("6.0"), "frequencia_minima": Decimal("75.0")},
        )

        secretaria = self._ensure_user(
            username=f"secretaria.jps.{year}",
            cpf=f"9500000{year % 100:02d}01",
            tipo=PerfilUsuario.SECRETARIA,
            first_name="Mariana",
            last_name="Souza",
            password="Sec@12345",
        )
        coordenacao = self._ensure_user(
            username=f"coordenacao.jps.{year}",
            cpf=f"9500000{year % 100:02d}02",
            tipo=PerfilUsuario.COORDENACAO,
            first_name="Rafael",
            last_name="Almeida",
            password="Coord@12345",
        )
        professor = self._ensure_user(
            username=f"professor.jps.{year}",
            cpf=f"9500000{year % 100:02d}03",
            tipo=PerfilUsuario.PROFESSOR,
            first_name="Carla",
            last_name="Mendonca",
            password="Prof@12345",
        )

        aluno_user = self._ensure_user(
            username=f"joao.pedro.{year}",
            cpf=cpf,
            tipo=PerfilUsuario.ALUNO,
            first_name="Joao Pedro",
            last_name="da Silva",
            password=password,
            email="joao.teste@exemplo.com",
        )

        pessoa, _ = Pessoa.objects.update_or_create(
            cpf=cpf,
            defaults={
                "nome_completo": "Joao Pedro da Silva",
                "data_nascimento": date(2004, 3, 15),
                "email": "joao.teste@exemplo.com",
                "telefone": "(69) 99999-0000",
                "ativo": True,
            },
        )
        aluno_user.pessoa = pessoa
        aluno_user.save(update_fields=["pessoa"])
        aluno_model, _ = Aluno.objects.get_or_create(pessoa=pessoa, defaults={"situacao": "ATIVO"})

        turma, _ = Turma.objects.get_or_create(
            curso=curso,
            nome=f"TAD-{year}-JPS-A",
            ano_letivo=year,
            defaults={"status": "ATIVA", "professor_responsavel": professor},
        )
        if turma.professor_responsavel_id != professor.id:
            turma.professor_responsavel = professor
            turma.save(update_fields=["professor_responsavel"])

        publicacao = PublicacaoInscricao.objects.create(
            curso=curso,
            codigo_edital=f"EDT-{year}-JPS-01",
            titulo=f"Edital de Ingresso {tag}",
            descricao=(
                "Processo seletivo para curso tecnico. "
                f"CPF solicitado no roteiro: {requested_cpf}. CPF operacional: {cpf}."
            ),
            vagas=40,
            modalidade_ingresso="PROCESSO_SELETIVO",
            data_inicio=date(year, 1, 5),
            data_fim=date(year, 1, 31),
            status="PUBLICADO",
            publicado_por=secretaria,
        )

        inscricao = Inscricao.objects.create(
            publicacao=publicacao,
            nome_candidato="Joao Pedro da Silva",
            cpf=cpf,
            email="joao.teste@exemplo.com",
            telefone="(69) 99999-0000",
            data_nascimento=date(2004, 3, 15),
            status="PENDENTE",
            modalidade_concorrencia="AMPLA",
            status_candidato="INSCRITO",
            observacao="Endereco: Rua das Acacias, 245, Nova Esperanca, Porto Velho/RO, CEP 76812-345.",
            usuario=aluno_user,
        )

        for doc_type in ["RG", "CPF", "COMPROVANTE_RESIDENCIA", "HISTORICO_ESCOLAR", "FOTO"]:
            DocumentoInscricao.objects.create(
                inscricao=inscricao,
                tipo=doc_type,
                entregue=True,
                status_validacao="VALIDO",
                validado_por=secretaria,
                data_validacao=date(year, 2, 2),
                justificativa_validacao="Documento conferido e aceito.",
                data_entrega=date(year, 1, 20),
                observacao="Arquivo de teste.",
            )

        inscricao.status = "VALIDADA"
        inscricao.status_candidato = "HOMOLOGADO"
        inscricao.save(update_fields=["status", "status_candidato"])

        processo_seletivo = ProcessoSeletivo.objects.create(
            publicacao=publicacao,
            modalidade="ANALISE_CURRICULO",
            data_realizacao=date(year, 2, 3),
            data_resultado=date(year, 2, 5),
            status="CONCLUIDO",
            nota_corte=Decimal("6.00"),
            criterios="Classificacao por analise documental e requisitos do edital.",
            resultado="Candidato apto para matricula.",
            responsavel=coordenacao,
        )

        candidato = Candidato.objects.create(
            processo=processo_seletivo,
            inscricao=inscricao,
            classificacao=1,
            pontuacao=Decimal("9.40"),
            modalidade_vaga="AMPLA",
            situacao="CONVOCADO",
            data_convocacao=date(year, 2, 7),
            observacao="Aprovado para matricula na 1a chamada.",
        )
        chamada = ChamadaProcessoSeletivo.objects.create(
            processo=processo_seletivo,
            numero=1,
            tipo="REGULAR",
            data_publicacao=date(year, 2, 6),
            prazo_matricula_inicio=date(year, 2, 8),
            prazo_matricula_fim=date(year, 2, 20),
            status="PUBLICADA",
            observacao="Chamada principal do processo seletivo.",
        )

        ConvocacaoCandidato.objects.create(
            chamada=chamada,
            candidato=candidato,
            modalidade_vaga="AMPLA",
            classificacao_na_chamada=1,
            status="MATRICULADO",
            data_status=date(year, 2, 15),
            observacao="Convocado apresentou documentacao e efetivou matricula.",
        )

        inscricao.status_candidato = "MATRICULADO"
        inscricao.save(update_fields=["status_candidato"])

        fluxo_matricula = FluxoMatricula.objects.create(
            aluno=aluno_user,
            tipo_matricula="NOVA",
            etapa_atual="REQUERIMENTO_RECEBIDO",
            observacoes="Fluxo principal de matricula do caso Joao Pedro.",
        )
        EtapaFluxo.objects.create(
            fluxo=fluxo_matricula,
            etapa="REQUERIMENTO_RECEBIDO",
            responsavel=secretaria,
            observacao="Requerimento recebido pelo portal.",
        )

        matricula = Matricula.objects.create(
            aluno=aluno_user,
            curso=curso,
            turma=turma,
            status="ATIVA",
            tipo_matricula="NOVA",
            turno="NOITE",
        )
        fluxo_matricula.matricula = matricula
        fluxo_matricula.save(update_fields=["matricula"])

        required_docs = [
            "RG",
            "CPF",
            "COMPROVANTE_RESIDENCIA",
            "HISTORICO_ESCOLAR",
            "FOTO",
            "CERTIDAO_NASCIMENTO",
        ]
        for doc_type in required_docs:
            DocumentoMatricula.objects.create(
                matricula=matricula,
                tipo_documento=doc_type,
                status="VALIDADO",
                data_recebimento=date(year, 2, 14),
                validado_por=secretaria,
                data_validacao=date(year, 2, 14),
                observacao="Documento validado no ato da matricula.",
            )

        self._advance_fluxo_matricula(fluxo_matricula, "DOCUMENTOS_CONFERIDOS", secretaria, "Checklist documental concluido.")
        self._advance_fluxo_matricula(fluxo_matricula, "REQUISITOS_VALIDADOS", coordenacao, "Requisitos academicos validados.")
        self._advance_fluxo_matricula(fluxo_matricula, "MATRICULA_REGISTRADA", secretaria, "Matricula institucional registrada.")
        self._advance_fluxo_matricula(fluxo_matricula, "ALUNO_ENTURMADO", secretaria, "Aluno vinculado a turma e turno.")

        comprovante_matricula = DocumentoEmitido.objects.create(
            matricula=matricula,
            tipo="DECLARACAO_MATRICULA",
            observacao="Comprovante de matricula emitido automaticamente.",
            validado=True,
            data_validacao=date(year, 2, 15),
            validado_por=secretaria,
            entregue=True,
            data_entrega=date(year, 2, 15),
            recebido_por="Joao Pedro da Silva",
        )
        fluxo_matricula.documento_comprovante = comprovante_matricula
        fluxo_matricula.save(update_fields=["documento_comprovante"])
        self._advance_fluxo_matricula(fluxo_matricula, "COMPROVANTE_EMITIDO", secretaria, f"Documento {comprovante_matricula.numero_protocolo}")
        self._advance_fluxo_matricula(fluxo_matricula, "ARQUIVADO", secretaria, "Pasta academica classificada e indexada.")

        plano_pasta, _ = PlanoClassificacao.objects.get_or_create(
            codigo="PASTA-ALUNO-JPS",
            defaults={
                "descricao": "Pasta academica do caso Joao Pedro",
                "prazo_guarda_anos": 50,
                "destinacao": "GUARDA_PERMANENTE",
            },
        )
        GuardaDocumental.objects.create(
            tipo_documento="PASTA_ALUNO",
            descricao=f"Dossie academico - {tag}",
            numero_caixa=f"CX-{year}-JPS-01",
            localizacao="Arquivo Central / Estante B / Prateleira 2",
            status="ATIVO",
            plano_classificacao=plano_pasta,
            responsavel=secretaria,
            matricula=matricula,
        )

        for index, component in enumerate(componente_objs, start=1):
            DiarioAcademico.objects.create(
                turma=turma,
                periodo=f"{year}/1-M{index}-{matricula.id}",
                componente_curricular=component.nome,
                status="FECHADO",
                data_fechamento=date(year + 1, 6, 20),
                observacoes="Diario encerrado apos consolidacao final.",
                aberto_por=professor,
                fechado_por=coordenacao,
            )

        eval_date = date(year, 3, 10)
        grade_map = {
            "Fundamentos da Administracao": [Decimal("8.0"), Decimal("8.5"), Decimal("9.0")],
            "Gestao de Pessoas": [Decimal("7.5"), Decimal("8.0"), Decimal("8.5")],
            "Processos Administrativos": [Decimal("7.0"), Decimal("7.5"), Decimal("8.0")],
            "Empreendedorismo e Projeto Integrador": [Decimal("8.5"), Decimal("9.0"), Decimal("9.0")],
        }
        for component_name, grades in grade_map.items():
            for idx, grade in enumerate(grades, start=1):
                Nota.objects.create(
                    matricula=matricula,
                    descricao=f"[{component_name}] Avaliacao {idx}",
                    valor=grade,
                    peso=Decimal("1.0"),
                    data_lancamento=eval_date + timedelta(days=30 * idx),
                )

        for idx in range(60):
            Frequencia.objects.create(
                matricula=matricula,
                data=start_date + timedelta(days=idx * 3),
                presente=idx not in {8, 13, 21, 34, 42, 57},
                observacao="Falta justificada" if idx in {13, 42} else "",
            )

        consolidacao, _ = ConsolidacaoAcademica.objects.get_or_create(matricula=matricula)
        consolidacao.consolidar()

        dependencia = DependenciaAcademica.objects.create(
            matricula=matricula,
            componente="Processos Administrativos",
            periodo_referencia=f"{year}/2",
            motivo="NOTA",
            nota_obtida=Decimal("5.80"),
            frequencia_percentual=Decimal("84.00"),
            status="ATIVA",
            observacao="Dependencia registrada em avaliacao parcial.",
        )
        dependencia.status = "CUMPRIDA"
        dependencia.data_resolucao = date(year + 1, 4, 10)
        dependencia.observacao = "Dependencia cumprida apos recuperacao paralela."
        dependencia.save(update_fields=["status", "data_resolucao", "observacao"])

        AproveitamentoComponente.objects.create(
            matricula=matricula,
            componente_origem="Informatica Basica",
            instituicao_origem="Escola Profissional Teste",
            carga_horaria=40,
            componente_destino="Empreendedorismo e Projeto Integrador",
            status="APROVADO",
            data_decisao=date(year, 8, 1),
            decisao_por=coordenacao,
            justificativa="Equivalencia deferida pela coordenacao academica.",
        )

        AtendimentoPedagogico.objects.create(
            aluno=aluno_user,
            pedagogia_responsavel=coordenacao,
            data_atendimento=date(year, 9, 10),
            diagnostico="Risco moderado em gestao de processos.",
            plano_acao="Monitoria semanal e plano de recuperacao orientado.",
            status="PLANO_RECUPERACAO",
        )
        AtendimentoPedagogico.objects.create(
            aluno=aluno_user,
            pedagogia_responsavel=coordenacao,
            data_atendimento=date(year + 1, 4, 12),
            diagnostico="Objetivos do plano de recuperacao atingidos.",
            plano_acao="Encerrar acompanhamento pedagogico especifico.",
            status="CONCLUIDO",
        )

        convenio = Convenio.objects.create(
            empresa=f"Empresa Escola {tag}",
            cnpj="12.345.678/0001-99",
            responsavel_empresa="Ana Paula Ribeiro",
            email_empresa="rh@empresaescola.exemplo.com",
            telefone_empresa="(69) 3222-0000",
            data_assinatura=date(year, 6, 1),
            data_vencimento=date(year + 1, 12, 31),
            status="VIGENTE",
            objeto="Oferta de vagas de estagio para curso tecnico.",
            responsavel_idep=secretaria,
        )

        estagio = Estagio.objects.create(
            matricula=matricula,
            convenio=convenio,
            modalidade="OBRIGATORIO",
            empresa=f"Empresa Escola {tag}",
            supervisor_empresa="Ana Paula Ribeiro",
            orientador_idep=professor,
            carga_horaria_total=200,
            carga_horaria_semanal=20,
            data_inicio=date(year + 1, 1, 15),
            data_fim_prevista=date(year + 1, 4, 30),
            data_fim_real=date(year + 1, 4, 28),
            status="CONCLUIDO",
            bolsa_mensal=Decimal("800.00"),
            seguro_numero="SEG-2026-0099",
            observacao="Estagio concluido com relatorio final aprovado.",
        )
        termo = TermoCompromisso.objects.create(
            estagio=estagio,
            data_assinatura=date(year + 1, 1, 10),
            status="ASSINADO",
            assinado_aluno=True,
            assinado_empresa=True,
            assinado_idep=True,
            observacao="TCE assinado por todas as partes.",
        )
        termo.status = "ENCERRADO"
        termo.save(update_fields=["status"])

        AcompanhamentoEstagio.objects.create(
            estagio=estagio,
            tipo="VISITA",
            data=date(year + 1, 2, 10),
            descricao="Visita tecnica realizada com desempenho satisfatorio.",
            registrado_por=professor,
        )
        AcompanhamentoEstagio.objects.create(
            estagio=estagio,
            tipo="RELATORIO",
            data=date(year + 1, 4, 25),
            descricao="Relatorio final entregue e validado.",
            registrado_por=professor,
        )

        conselho = ConselhoClasse.objects.create(
            turma=turma,
            periodo=f"{year}/{year + 1}",
            data_reuniao=course_end_date,
            status="REALIZADO",
            pauta="Apreciacao final do desempenho academico e validacao para conclusao.",
            ata="Conselho aprova conclusao e emissao de documentacao final.",
            responsavel=coordenacao,
        )
        ata_resultado = AtaResultado.objects.create(
            conselho=conselho,
            data_publicacao=course_end_date + timedelta(days=2),
            conteudo=(
                "Aluno Joao Pedro da Silva aprovado em todos os requisitos. "
                "Apto para emissao de historico final e diploma."
            ),
            publicado_por=secretaria,
        )
        AtaEscolar.objects.create(
            conselho=conselho,
            tipo="RESULTADO_FINAL",
            titulo=f"Ata de conclusao - {tag}",
            unidade_nome=unidade.nome,
            local_reuniao="Sala de reunioes da Secretaria Academica",
            data_reuniao=course_end_date,
            hora_inicio=time(14, 0),
            hora_fim=time(16, 0),
            presidente=coordenacao,
            secretario=secretaria,
            membros_presentes=(
                f"{coordenacao.get_full_name()} - Coordenacao\n"
                f"{secretaria.get_full_name()} - Secretaria\n"
                f"{professor.get_full_name()} - Docente"
            ),
            abertura="Reuniao iniciada para deliberacao final da turma.",
            deliberacoes="Aluno Joao Pedro aprovado para certificacao e diplomacao.",
            encerramento="Nada mais havendo, encerra-se a sessao.",
            assinado=True,
            data_assinatura=course_end_date + timedelta(days=1),
        )

        fluxo_emissao = FluxoEmissaoDocumento.objects.create(
            solicitante=aluno_user,
            matricula=matricula,
            tipo_documento="HISTORICO_ESCOLAR",
            etapa_atual="PROTOCOLO_ABERTO",
            observacoes="Solicitacao de historico final para diplomacao.",
        )
        processo_historico = Processo.objects.create(
            tipo="REQUERIMENTO",
            requerente=aluno_user,
            assunto=f"Historico escolar final - {tag}",
            descricao="Solicitacao de emissao de historico apos conclusao.",
            status="ABERTO",
        )
        fluxo_emissao.processo = processo_historico
        fluxo_emissao.save(update_fields=["processo"])
        EtapaFluxoEmissao.objects.create(
            fluxo=fluxo_emissao,
            etapa="PROTOCOLO_ABERTO",
            responsavel=secretaria,
            observacao=f"Processo {processo_historico.numero}",
        )

        fluxo_emissao.verificar_elegibilidade()
        self._advance_fluxo_emissao(fluxo_emissao, "ELEGIBILIDADE_VERIFICADA", coordenacao, "Aluno elegivel para historico final.")

        historico_emitido = DocumentoEmitido.objects.create(
            matricula=matricula,
            tipo="HISTORICO_ESCOLAR",
            observacao="Historico final consolidado.",
            validado=True,
            data_validacao=course_end_date + timedelta(days=3),
            validado_por=secretaria,
            entregue=True,
            data_entrega=course_end_date + timedelta(days=4),
            recebido_por="Joao Pedro da Silva",
        )
        fluxo_emissao.documento_emitido = historico_emitido
        fluxo_emissao.save(update_fields=["documento_emitido"])
        self._advance_fluxo_emissao(fluxo_emissao, "DOCUMENTO_GERADO", secretaria, historico_emitido.numero_protocolo)
        self._advance_fluxo_emissao(fluxo_emissao, "DOCUMENTO_VALIDADO", secretaria, "Documento conferido e assinado.")
        self._advance_fluxo_emissao(fluxo_emissao, "ENTREGA_REGISTRADA", secretaria, "Entrega registrada ao aluno.")
        self._advance_fluxo_emissao(fluxo_emissao, "ARQUIVADO", secretaria, "Fluxo de emissao concluido.")

        historico_base = HistoricoEscolar.objects.create(
            assunto=f"Historico escolar final {tag}",
            emitido_por=secretaria,
            matricula=matricula,
            tipo="COMPLETO",
            periodo_ref=f"{year}/{year + 1}",
            observacao="Documento oficial para arquivo e validacao institucional.",
        )
        HistoricoEscolarDigital.objects.create(
            historico=historico_base,
            tipo_documento="FINAL",
            status="ASSINADO",
            versao=1,
            hash_documento="a" * 64,
            xml_conteudo="<historico><aluno>Joao Pedro da Silva</aluno></historico>",
            xml_assinado_conteudo="<signed>true</signed>",
            validacao_xsd_ok=True,
            assinado_digitalmente=True,
            assinatura_metadados={"issuer": "Secretaria", "algorithm": "XMLDSig"},
            qr_payload_url="https://idep.exemplo/validacao/HED",
            qr_code_data_uri="data:image/png;base64,QR-CODE-PLACEHOLDER",
            emitido_por=secretaria,
        )

        processo_diploma = Processo.objects.create(
            tipo="REQUERIMENTO",
            requerente=aluno_user,
            assunto=f"Diplomacao institucional - {tag}",
            descricao=(
                "Processo administrativo completo de emissao de diploma: "
                "conferencia secretaria, validacao academica, registro, assinatura e entrega."
            ),
            status="ABERTO",
        )
        Tramitacao.objects.create(
            processo=processo_diploma,
            responsavel=secretaria,
            setor_destino="Secretaria Escolar",
            acao="RECEBIDO",
            observacao="Conferencia inicial da secretaria.",
        )
        Tramitacao.objects.create(
            processo=processo_diploma,
            responsavel=coordenacao,
            setor_destino="Registro Academico",
            acao="ENCAMINHADO",
            observacao="Validacao dos requisitos de conclusao.",
        )
        Tramitacao.objects.create(
            processo=processo_diploma,
            responsavel=coordenacao,
            setor_destino="Registro Institucional",
            acao="RESPONDIDO",
            observacao="Registro institucional (livro, folha, termo).",
        )
        Tramitacao.objects.create(
            processo=processo_diploma,
            responsavel=secretaria,
            setor_destino="Secretaria Escolar",
            acao="ARQUIVADO",
            observacao="Documento final gerado e validado.",
        )
        processo_diploma.status = "ARQUIVADO"
        processo_diploma.data_conclusao = course_end_date + timedelta(days=20)
        processo_diploma.save(update_fields=["status", "data_conclusao"])

        certificado_diploma = CertificadoDiploma.objects.create(
            matricula=matricula,
            tipo="DIPLOMA",
            status="PENDENTE",
            emitido_por=secretaria,
            observacao=(
                "Status operacional: em preparacao -> registrado -> disponivel para retirada -> entregue."
            ),
        )
        certificado_diploma.status = "EMITIDO"
        certificado_diploma.data_emissao = course_end_date + timedelta(days=15)
        certificado_diploma.save(update_fields=["status", "data_emissao"])

        diploma_escolar = DiplomaEscolar.objects.create(
            certificado=certificado_diploma,
            nome_completo="Joao Pedro da Silva",
            data_nascimento=date(2004, 3, 15),
            local_nascimento="Porto Velho/RO",
            nome_pai="Carlos Roberto da Silva",
            nome_mae="Maria Aparecida da Silva",
            cpf=cpf,
            rg="1234567 SSP/RO",
            curso_nome=curso.nome,
            habilitacao="Tecnico em Administracao",
            carga_horaria=curso.carga_horaria,
            data_inicio_curso=start_date,
            data_conclusao=course_end_date,
            media_final=consolidacao.media_final,
            unidade_nome=unidade.nome,
            municipio_uf=f"{unidade.cidade}/{unidade.uf}",
            diretor_nome="Diretora Institucional de Teste",
            diretor_cargo="Diretora Geral",
            secretario_nome=secretaria.get_full_name(),
            data_emissao=course_end_date + timedelta(days=15),
        )

        certificado_diploma.status = "ENTREGUE"
        certificado_diploma.data_entrega = course_end_date + timedelta(days=25)
        certificado_diploma.observacao = (
            f"Entregue ao aluno. Diploma {diploma_escolar.numero_diploma} "
            f"com codigo {diploma_escolar.codigo_verificacao}."
        )
        certificado_diploma.save(update_fields=["status", "data_entrega", "observacao"])

        matricula.status = "CONCLUIDA"
        matricula.save(update_fields=["status"])

        aluno_model.situacao = "ATIVO"
        aluno_model.save(update_fields=["situacao"])

        return (
            unidade,
            curso,
            turma,
            secretaria,
            coordenacao,
            professor,
            aluno_user,
            aluno_model,
            publicacao,
            inscricao,
            processo_seletivo,
            candidato,
            matricula,
            consolidacao,
            estagio,
            ata_resultado,
            historico_emitido,
            certificado_diploma,
            diploma_escolar,
            processo_diploma,
        )

    def _ensure_user(self, *, username: str, cpf: str, tipo: str, first_name: str, last_name: str, password: str, email: str = ""):
        from apps.usuarios.models import Usuario

        user = Usuario.objects.filter(username=username).first()
        if user is None:
            return Usuario.objects.create_user(
                username=username,
                cpf=cpf,
                tipo=tipo,
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=password,
            )

        user.cpf = cpf
        user.tipo = tipo
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.is_active = True
        user.set_password(password)
        user.save()
        return user

    def _advance_fluxo_matricula(self, fluxo, etapa: str, responsavel, observacao: str):
        from apps.matriculas.models import EtapaFluxo

        fluxo.avancar(etapa)
        EtapaFluxo.objects.create(
            fluxo=fluxo,
            etapa=etapa,
            responsavel=responsavel,
            observacao=observacao,
        )

    def _advance_fluxo_emissao(self, fluxo, etapa: str, responsavel, observacao: str):
        from apps.matriculas.models import EtapaFluxoEmissao

        fluxo.avancar(etapa)
        EtapaFluxoEmissao.objects.create(
            fluxo=fluxo,
            etapa=etapa,
            responsavel=responsavel,
            observacao=observacao,
        )
