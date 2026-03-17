from datetime import date, datetime, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone


SEED_USER_DEFINITIONS = [
    {
        "username": "admin.dev",
        "password": "admin123",
        "cpf": "90000000001",
        "tipo": "ADMIN",
        "first_name": "Administrador",
        "last_name": "Dev",
        "email": "admin.dev@idep.local",
        "is_staff": True,
        "is_superuser": True,
        "matricula": "DEV0001",
    },
    {
        "username": "secretaria.dev",
        "password": "secretaria123",
        "cpf": "90000000002",
        "tipo": "SECRETARIA",
        "first_name": "Sara",
        "last_name": "Secretaria",
        "email": "secretaria.dev@idep.local",
        "matricula": "DEV0002",
    },
    {
        "username": "coordenacao.dev",
        "password": "coordenacao123",
        "cpf": "90000000004",
        "tipo": "COORDENACAO",
        "first_name": "Carla",
        "last_name": "Coordenadora",
        "email": "coordenacao.dev@idep.local",
        "matricula": "DEV0004",
    },
    {
        "username": "professor.dev",
        "password": "professor123",
        "cpf": "90000000003",
        "tipo": "PROFESSOR",
        "first_name": "Paulo",
        "last_name": "Professor",
        "email": "professor.dev@idep.local",
        "matricula": "DEV0003",
    },
    {
        "username": "professor.dev.2",
        "password": "professor123",
        "cpf": "90000000005",
        "tipo": "PROFESSOR",
        "first_name": "Patricia",
        "last_name": "Formadora",
        "email": "professor2.dev@idep.local",
        "matricula": "DEV0005",
    },
    {
        "username": "aluno.dev.1",
        "password": "aluno123",
        "cpf": "90000000011",
        "tipo": "ALUNO",
        "first_name": "Ana",
        "last_name": "Souza",
        "email": "ana.dev@idep.local",
    },
    {
        "username": "aluno.dev.2",
        "password": "aluno123",
        "cpf": "90000000012",
        "tipo": "ALUNO",
        "first_name": "Bruno",
        "last_name": "Lima",
        "email": "bruno.dev@idep.local",
    },
    {
        "username": "aluno.dev.3",
        "password": "aluno123",
        "cpf": "90000000013",
        "tipo": "ALUNO",
        "first_name": "Camila",
        "last_name": "Rocha",
        "email": "camila.dev@idep.local",
    },
    {
        "username": "aluno.dev.4",
        "password": "aluno123",
        "cpf": "90000000014",
        "tipo": "ALUNO",
        "first_name": "Diego",
        "last_name": "Mendes",
        "email": "diego.dev@idep.local",
    },
]

SEED_COMPONENTS = [
    {"nome": "Fundamentos de Informática", "abreviatura": "INFO", "ordem": 1, "carga_horaria": 40},
    {"nome": "Lógica de Programação", "abreviatura": "LOG", "ordem": 2, "carga_horaria": 60},
    {"nome": "Banco de Dados", "abreviatura": "BD", "ordem": 3, "carga_horaria": 60},
]

SEED_FIC_COMPONENTS = [
    {"nome": "Inclusão Digital", "abreviatura": "IDIG", "ordem": 1, "carga_horaria": 40},
    {"nome": "Ferramentas de Escritório", "abreviatura": "OFF", "ordem": 2, "carga_horaria": 60},
    {"nome": "Projeto de Vida e Trabalho", "abreviatura": "PVT", "ordem": 3, "carga_horaria": 60},
]


class Command(BaseCommand):
    help = "Popula o banco configurado com dados acadêmicos de desenvolvimento idempotentes."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Remove antes os registros de desenvolvimento criados por este comando.",
        )

    def handle(self, *args, **options):
        from apps.agenda.models import EventoAgenda
        from apps.cursos.models import AreaCurso, CalendarioLetivo, ComponenteCurricular, Curso, EixoTecnologico
        from apps.frequencia.models import Frequencia
        from apps.inscricoes.models import Candidato, DocumentoInscricao, Inscricao, ProcessoSeletivo, PublicacaoInscricao
        from apps.matriculas.models import Matricula
        from apps.notas.models import Nota
        from apps.processos.models import Processo, Tramitacao
        from apps.setores.models import Setor
        from apps.turmas.models import DiarioAcademico, DiarioMaterialAula, DiarioOcorrencia, Turma
        from apps.unidades.models import Unidade
        from apps.usuarios.models import Aluno, Pessoa, ServidorPerfil, Usuario

        self.models = {
            "EventoAgenda": EventoAgenda,
            "AreaCurso": AreaCurso,
            "CalendarioLetivo": CalendarioLetivo,
            "ComponenteCurricular": ComponenteCurricular,
            "Curso": Curso,
            "EixoTecnologico": EixoTecnologico,
            "Frequencia": Frequencia,
            "Candidato": Candidato,
            "DocumentoInscricao": DocumentoInscricao,
            "Inscricao": Inscricao,
            "ProcessoSeletivo": ProcessoSeletivo,
            "PublicacaoInscricao": PublicacaoInscricao,
            "Matricula": Matricula,
            "Nota": Nota,
            "Processo": Processo,
            "Tramitacao": Tramitacao,
            "Setor": Setor,
            "DiarioAcademico": DiarioAcademico,
            "DiarioMaterialAula": DiarioMaterialAula,
            "DiarioOcorrencia": DiarioOcorrencia,
            "Turma": Turma,
            "Unidade": Unidade,
            "Aluno": Aluno,
            "Pessoa": Pessoa,
            "ServidorPerfil": ServidorPerfil,
            "Usuario": Usuario,
        }

        with transaction.atomic():
            if options["reset"]:
                self._reset_seed_data()

            unidade = Unidade.objects.get(codigo="sede")
            setor = self._seed_setor()
            users = self._seed_users(setor)
            area_curso, eixo = self._seed_catalogs()
            cursos, turmas = self._seed_course_structure(unidade, area_curso, eixo, users)
            matriculas_por_turma = self._seed_students(cursos, turmas, users)
            self._seed_academic_records(turmas, matriculas_por_turma, users)
            self._seed_selection_flow(cursos["TDSDEV"], users["secretaria.dev"], users["aluno.dev.1"])
            self._seed_process_flow(users["aluno.dev.1"], users["secretaria.dev"])

        self.stdout.write(self.style.SUCCESS("Dados de desenvolvimento disponíveis no banco configurado."))
        self.stdout.write("Usuários criados:")
        for definition in SEED_USER_DEFINITIONS:
            self.stdout.write(f"- {definition['username']} / {definition['password']}")

    def _reset_seed_data(self):
        usernames = [definition["username"] for definition in SEED_USER_DEFINITIONS]
        cpfs = [definition["cpf"] for definition in SEED_USER_DEFINITIONS]

        self.models["Processo"].objects.filter(assunto__startswith="DEV ").delete()
        self.models["PublicacaoInscricao"].objects.filter(titulo__startswith="Edital DEV ").delete()
        self.models["Turma"].objects.filter(nome__startswith="DEV-").delete()
        self.models["Curso"].objects.filter(sigla__in=["TDSDEV", "FICDEV"]).delete()
        self.models["AreaCurso"].objects.filter(descricao="Cursos de Tecnologia DEV").delete()
        self.models["EixoTecnologico"].objects.filter(descricao="Informação e Comunicação").delete()
        self.models["Setor"].objects.filter(codigo="DEV-ACADEMICO").delete()
        self.models["Usuario"].objects.filter(username__in=usernames).delete()
        self.models["Pessoa"].objects.filter(cpf__in=cpfs).delete()

        self.stdout.write(self.style.WARNING("Registros DEV anteriores removidos."))

    def _seed_setor(self):
        setor, _ = self.models["Setor"].objects.update_or_create(
            codigo="DEV-ACADEMICO",
            defaults={
                "nome": "Setor Acadêmico DEV",
                "sigla": "SDEV",
                "ativo": True,
            },
        )
        return setor

    def _seed_users(self, setor):
        users = {}

        for definition in SEED_USER_DEFINITIONS:
            pessoa, _ = self.models["Pessoa"].objects.update_or_create(
                cpf=definition["cpf"],
                defaults={
                    "nome_completo": f"{definition['first_name']} {definition['last_name']}".strip(),
                    "email": definition["email"],
                    "telefone": "65999990000",
                    "ativo": True,
                },
            )

            user, _ = self.models["Usuario"].objects.update_or_create(
                username=definition["username"],
                defaults={
                    "cpf": definition["cpf"],
                    "tipo": definition["tipo"],
                    "first_name": definition["first_name"],
                    "last_name": definition["last_name"],
                    "email": definition["email"],
                    "pessoa": pessoa,
                    "setor": setor if definition["tipo"] != "ALUNO" else None,
                    "is_staff": definition.get("is_staff", False),
                    "is_superuser": definition.get("is_superuser", False),
                    "is_active": True,
                },
            )
            user.set_password(definition["password"])
            user.save()

            if definition["tipo"] == "ALUNO":
                self.models["Aluno"].objects.update_or_create(
                    pessoa=pessoa,
                    defaults={"situacao": "ATIVO"},
                )
            else:
                self.models["ServidorPerfil"].objects.update_or_create(
                    usuario=user,
                    defaults={
                        "matricula_servidor": definition["matricula"],
                        "nome_usual": definition["first_name"],
                        "email_institucional": definition["email"],
                        "cargo_atual": user.get_tipo_display(),
                    },
                )

            users[definition["username"]] = user

        return users

    def _seed_catalogs(self):
        area_curso, _ = self.models["AreaCurso"].objects.update_or_create(
            descricao="Cursos de Tecnologia DEV",
            defaults={
                "codigo_cine": "0613",
                "cine": "Desenvolvimento e análise de software e aplicações",
                "area_detalhada": "Desenvolvimento de software",
                "area_especifica": "Tecnologia da informação",
                "area_geral": "Computação",
            },
        )
        eixo, _ = self.models["EixoTecnologico"].objects.update_or_create(
            descricao="Informação e Comunicação"
        )
        return area_curso, eixo

    def _seed_course_structure(self, unidade, area_curso, eixo, professor):
        curso_tecnico, _ = self.models["Curso"].objects.update_or_create(
            sigla="TDSDEV",
            defaults={
                "unidade": unidade,
                "area_curso": area_curso,
                "nome": "Técnico em Desenvolvimento de Sistemas DEV",
                "eixo_tecnologico": eixo.descricao,
                "carga_horaria": 1200,
            },
        )

        curso_fic, _ = self.models["Curso"].objects.update_or_create(
            sigla="FICDEV",
            defaults={
                "unidade": unidade,
                "area_curso": area_curso,
                "nome": "Curso Itinerante DEV de Inclusão Digital",
                "eixo_tecnologico": eixo.descricao,
                "carga_horaria": 160,
            },
        )

        for component in SEED_COMPONENTS:
            self.models["ComponenteCurricular"].objects.update_or_create(
                curso=curso_tecnico,
                nome=component["nome"],
                defaults={
                    "abreviatura": component["abreviatura"],
                    "sigla": component["abreviatura"],
                    "tipo_componente": "Obrigatório",
                    "nivel_ensino": "Técnico",
                    "grupo_atuacao": "Base tecnológica",
                    "carga_horaria": component["carga_horaria"],
                    "hora_aula": component["carga_horaria"],
                    "qtd_creditos": 4,
                    "ordem": component["ordem"],
                    "ativo": True,
                },
            )

        for component in SEED_FIC_COMPONENTS:
            self.models["ComponenteCurricular"].objects.update_or_create(
                curso=curso_fic,
                nome=component["nome"],
                defaults={
                    "abreviatura": component["abreviatura"],
                    "sigla": component["abreviatura"],
                    "tipo_componente": "Obrigatório",
                    "nivel_ensino": "Formação Inicial e Continuada",
                    "grupo_atuacao": "Qualificação profissional",
                    "carga_horaria": component["carga_horaria"],
                    "hora_aula": component["carga_horaria"],
                    "qtd_creditos": 2,
                    "ordem": component["ordem"],
                    "ativo": True,
                },
            )

        self.models["CalendarioLetivo"].objects.update_or_create(
            ano_letivo="2026/1",
            curso=curso_tecnico,
            defaults={
                "data_inicio": date(2026, 2, 2),
                "data_fim": date(2026, 12, 18),
                "dias_letivos": 200,
                "status": "VIGENTE",
                "descricao": "Calendário de desenvolvimento gerado automaticamente.",
            },
        )

        self.models["CalendarioLetivo"].objects.update_or_create(
            ano_letivo="2026/1",
            curso=curso_fic,
            defaults={
                "data_inicio": date(2026, 2, 10),
                "data_fim": date(2026, 5, 30),
                "dias_letivos": 80,
                "status": "VIGENTE",
                "descricao": "Calendário FIC de desenvolvimento gerado automaticamente.",
            },
        )

        turma_tecnico, _ = self.models["Turma"].objects.update_or_create(
            curso=curso_tecnico,
            nome="DEV-TDS-2026-1",
            defaults={
                "ano_letivo": 2026,
                "status": "ATIVA",
                "professor_responsavel": professor["professor.dev"],
            },
        )

        turma_fic, _ = self.models["Turma"].objects.update_or_create(
            curso=curso_fic,
            nome="DEV-FIC-2026-1",
            defaults={
                "ano_letivo": 2026,
                "status": "ATIVA",
                "professor_responsavel": professor["professor.dev.2"],
            },
        )

        return {"TDSDEV": curso_tecnico, "FICDEV": curso_fic}, {
            "DEV-TDS-2026-1": turma_tecnico,
            "DEV-FIC-2026-1": turma_fic,
        }

    def _seed_students(self, cursos, turmas, users):
        matriculas_por_turma = {}
        distribuicao = [
            ("DEV-TDS-2026-1", cursos["TDSDEV"], ["aluno.dev.1", "aluno.dev.2"], "MANHA"),
            ("DEV-FIC-2026-1", cursos["FICDEV"], ["aluno.dev.3", "aluno.dev.4"], "NOITE"),
        ]

        for turma_nome, curso, student_usernames, turno in distribuicao:
            turma = turmas[turma_nome]
            matriculas = []

            for username in student_usernames:
                matricula, _ = self.models["Matricula"].objects.get_or_create(
                    aluno=users[username],
                    curso=curso,
                    turma=turma,
                    defaults={
                        "status": "ATIVA",
                        "tipo_matricula": "NOVA",
                        "turno": turno,
                    },
                )
                matricula.status = "ATIVA"
                matricula.tipo_matricula = "NOVA"
                matricula.turno = turno
                matricula.save()
                matriculas.append(matricula)

                self.stdout.write(
                    f"Matrícula DEV pronta para {users[username].get_full_name()} ({matricula.numero_matricula})."
                )

            matriculas_por_turma[turma_nome] = matriculas

        return matriculas_por_turma

    def _seed_academic_records(self, turmas, matriculas_por_turma, users):
        all_matriculas = [matricula for matriculas in matriculas_por_turma.values() for matricula in matriculas]

        self.models["Nota"].objects.filter(matricula__in=all_matriculas, descricao__startswith="DEV ").delete()
        self.models["Frequencia"].objects.filter(matricula__in=all_matriculas, observacao__startswith="DEV ").delete()

        cenarios = {
            "DEV-TDS-2026-1": {
                "component": "Lógica de Programação",
                "reference_dates": [date(2026, 3, 3), date(2026, 3, 10), date(2026, 3, 17)],
                "notes": [
                    ("DEV Avaliação Diagnóstica", Decimal("8.50"), Decimal("1.00"), date(2026, 3, 20)),
                    ("DEV Projeto Integrador", Decimal("9.00"), Decimal("2.00"), date(2026, 4, 5)),
                ],
                "event_title": "DEV Aula inaugural do módulo técnico",
                "event_start": datetime(2026, 3, 25, 19, 0, 0),
                "event_description": "Evento criado pelo seed de desenvolvimento.",
                "diary_status": "ABERTO",
                "diary_observations": "DEV Diário aberto para lançamento de aulas, materiais e ocorrências.",
                "materials": [
                    {
                        "titulo": "DEV Plano de aula - Algoritmos introdutórios",
                        "descricao": "Plano base para as três primeiras aulas do módulo técnico.",
                        "url_material": "https://idep.local/dev/tds/plano-aula-algoritmos.pdf",
                        "data_referencia": date(2026, 3, 3),
                    },
                    {
                        "titulo": "DEV Lista de exercícios - Estruturas condicionais",
                        "descricao": "Exercícios usados no laboratório de programação.",
                        "url_material": "https://idep.local/dev/tds/lista-condicionais.pdf",
                        "data_referencia": date(2026, 3, 10),
                    },
                ],
                "occurrences": [
                    {
                        "tipo": "OCORRENCIA",
                        "titulo": "DEV Participação destacada em laboratório",
                        "descricao": "Turma engajada na resolução prática dos exercícios iniciais.",
                        "data_ocorrencia": date(2026, 3, 10),
                    }
                ],
            },
            "DEV-FIC-2026-1": {
                "component": "Inclusão Digital",
                "reference_dates": [date(2026, 3, 5), date(2026, 3, 12), date(2026, 3, 19)],
                "notes": [
                    ("DEV Produção Guiada em Laboratório", Decimal("8.00"), Decimal("1.00"), date(2026, 3, 21)),
                    ("DEV Apresentação Final", Decimal("9.25"), Decimal("2.00"), date(2026, 4, 2)),
                ],
                "event_title": "DEV Oficina de cidadania digital",
                "event_start": datetime(2026, 3, 26, 18, 30, 0),
                "event_description": "Evento FIC criado pelo seed de desenvolvimento.",
                "diary_status": "REVISAO",
                "diary_observations": "DEV Diário em revisão para simular fluxo de conferência pedagógica.",
                "materials": [
                    {
                        "titulo": "DEV Guia rápido de navegação segura",
                        "descricao": "Material introdutório usado na turma FIC.",
                        "url_material": "https://idep.local/dev/fic/cartilha-seguranca.pdf",
                        "data_referencia": date(2026, 3, 5),
                    }
                ],
                "occurrences": [
                    {
                        "tipo": "OCORRENCIA",
                        "titulo": "DEV Ajuste de cronograma por atividade externa",
                        "descricao": "A turma precisou remanejar a prática do laboratório para a semana seguinte.",
                        "data_ocorrencia": date(2026, 3, 12),
                    },
                    {
                        "tipo": "SUSPENSAO",
                        "titulo": "DEV Suspensão de aula por manutenção elétrica",
                        "descricao": "Registro de suspensão para alimentar a visualização de ocorrências especiais no diário.",
                        "data_ocorrencia": date(2026, 3, 19),
                    },
                ],
            },
        }

        for turma_nome, configuracao in cenarios.items():
            matriculas = matriculas_por_turma[turma_nome]
            turma = turmas[turma_nome]

            for index, matricula in enumerate(matriculas, start=1):
                for descricao, valor_base, peso, data_lancamento in configuracao["notes"]:
                    self.models["Nota"].objects.create(
                        matricula=matricula,
                        descricao=descricao,
                        valor=valor_base - Decimal(index - 1) / Decimal("4"),
                        peso=peso,
                        data_lancamento=data_lancamento,
                    )

                for offset, lesson_date in enumerate(configuracao["reference_dates"]):
                    self.models["Frequencia"].objects.update_or_create(
                        matricula=matricula,
                        data=lesson_date,
                        defaults={
                            "presente": not (index == len(matriculas) and offset == 1),
                            "observacao": "DEV Presença lançada automaticamente",
                        },
                    )

            start = timezone.make_aware(configuracao["event_start"])
            self.models["EventoAgenda"].objects.update_or_create(
                turma=turma,
                titulo=configuracao["event_title"],
                defaults={
                    "descricao": configuracao["event_description"],
                    "inicio": start,
                    "fim": start + timedelta(hours=2),
                },
            )

            diario_defaults = {
                "componente_curricular": configuracao["component"],
                "status": configuracao["diary_status"],
                "observacoes": configuracao["diary_observations"],
                "aberto_por": turma.professor_responsavel or users["coordenacao.dev"],
                "fechado_por": users["coordenacao.dev"] if configuracao["diary_status"] == "FECHADO" else None,
                "data_fechamento": date(2026, 4, 10) if configuracao["diary_status"] == "FECHADO" else None,
            }
            diario, _ = self.models["DiarioAcademico"].objects.update_or_create(
                turma=turma,
                periodo="2026/1",
                defaults=diario_defaults,
            )

            self.models["DiarioMaterialAula"].objects.filter(diario=diario, titulo__startswith="DEV ").delete()
            self.models["DiarioOcorrencia"].objects.filter(diario=diario, titulo__startswith="DEV ").delete()

            for material in configuracao["materials"]:
                self.models["DiarioMaterialAula"].objects.create(
                    diario=diario,
                    criado_por=turma.professor_responsavel or users["coordenacao.dev"],
                    **material,
                )

            for ocorrencia in configuracao["occurrences"]:
                self.models["DiarioOcorrencia"].objects.create(
                    diario=diario,
                    registrado_por=users["coordenacao.dev"] if ocorrencia["tipo"] == "SUSPENSAO" else turma.professor_responsavel,
                    **ocorrencia,
                )

    def _seed_selection_flow(self, curso, secretaria, aluno):
        publicacao, _ = self.models["PublicacaoInscricao"].objects.update_or_create(
            curso=curso,
            titulo="Edital DEV 2026/1 - Técnico em Desenvolvimento de Sistemas",
            defaults={
                "descricao": "Edital de demonstração para o ambiente local.",
                "vagas": 30,
                "data_inicio": date(2026, 1, 10),
                "data_fim": date(2026, 2, 10),
                "status": "PUBLICADO",
                "publicado_por": secretaria,
            },
        )

        inscricao = self.models["Inscricao"].objects.filter(publicacao=publicacao, cpf=aluno.cpf).first()
        if inscricao is None:
            inscricao = self.models["Inscricao"].objects.create(
                publicacao=publicacao,
                nome_candidato=aluno.get_full_name(),
                cpf=aluno.cpf,
                email=aluno.email,
                telefone="65999990001",
                data_nascimento=date(2001, 6, 15),
                status="VALIDADA",
                usuario=aluno,
                observacao="Registro DEV carregado automaticamente.",
            )
        else:
            inscricao.status = "VALIDADA"
            inscricao.usuario = aluno
            inscricao.observacao = "Registro DEV carregado automaticamente."
            inscricao.save()

        for tipo in ["RG", "CPF", "HISTORICO_ESCOLAR"]:
            self.models["DocumentoInscricao"].objects.update_or_create(
                inscricao=inscricao,
                tipo=tipo,
                defaults={
                    "entregue": True,
                    "data_entrega": date(2026, 1, 15),
                    "observacao": "Documento DEV",
                },
            )

        processo, _ = self.models["ProcessoSeletivo"].objects.update_or_create(
            publicacao=publicacao,
            defaults={
                "modalidade": "DEMANDA_ESPONTANEA",
                "data_realizacao": date(2026, 2, 12),
                "data_resultado": date(2026, 2, 14),
                "status": "CONCLUIDO",
                "criterios": "Classificação por ordem de inscrição.",
                "resultado": "Ambiente DEV com um candidato convocado.",
                "responsavel": secretaria,
            },
        )

        self.models["Candidato"].objects.update_or_create(
            processo=processo,
            inscricao=inscricao,
            defaults={
                "classificacao": 1,
                "pontuacao": Decimal("10.00"),
                "situacao": "CONVOCADO",
                "data_convocacao": date(2026, 2, 14),
                "observacao": "Candidato DEV convocado.",
            },
        )

    def _seed_process_flow(self, aluno, secretaria):
        processo = self.models["Processo"].objects.filter(assunto="DEV Solicitação de declaração de matrícula").first()
        if processo is None:
            processo = self.models["Processo"].objects.create(
                tipo="SOLICITACAO",
                requerente=aluno,
                assunto="DEV Solicitação de declaração de matrícula",
                descricao="Processo de desenvolvimento gerado automaticamente.",
                status="EM_TRAMITACAO",
            )
        else:
            processo.requerente = aluno
            processo.descricao = "Processo de desenvolvimento gerado automaticamente."
            processo.status = "EM_TRAMITACAO"
            processo.save()

        self.models["Tramitacao"].objects.filter(processo=processo).delete()
        self.models["Tramitacao"].objects.create(
            processo=processo,
            responsavel=secretaria,
            setor_destino="Secretaria Acadêmica",
            acao="RECEBIDO",
            observacao="Recebimento DEV da solicitação.",
        )
        self.models["Tramitacao"].objects.create(
            processo=processo,
            responsavel=secretaria,
            setor_destino="Coordenação",
            acao="ENCAMINHADO",
            observacao="Encaminhamento DEV para análise.",
        )