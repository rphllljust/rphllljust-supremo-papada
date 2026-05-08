"""
Management command: seed_50_alunos
===================================
Popula o banco com 50 alunos de teste persistentes distribuídos entre as três
unidades (Sede, Rio Branco, Flora Calheiros) e as três modalidades de curso
(Técnico, Itinerante, Remoto/formacao_inicial).

Idempotência: detecta alunos já existentes por CPF antes de criar qualquer
registro. Re-execuções são seguras e não duplicam dados.

Uso:
    python manage.py seed_50_alunos
    python manage.py seed_50_alunos --reset   # remove os registros criados e recria
"""
from django.core.management.base import BaseCommand
from django.db import transaction


# ---------------------------------------------------------------------------
# Tabela principal: 50 alunos
#
# Campos por linha:
#   nome, cpf (11 dígitos), data_nascimento, email, telefone,
#   sigla_curso, nome_turma, status_matricula, turno
# ---------------------------------------------------------------------------
ALUNOS_SEED = [
    # CPFs com prefixo 80XXXXXXXX — não colidem com setup_qa.py nem seed_development_data
    # ─── TÉCNICO — SEDE (7) ─────────────────────────────────────────────────
    ("Ana Beatriz Cavalcante Souza",   "80000000101", "2005-03-12", "ana.cavalcante@seed.local",     "(82)987120001", "TEC-SEDE",  "TEC-SEDE-A",  "ATIVA",     "MANHA"),
    ("Bruno Henrique Ferreira Lima",   "80000000202", "2004-07-22", "bruno.ferreira@seed.local",     "(82)987120002", "TEC-SEDE",  "TEC-SEDE-A",  "ATIVA",     "TARDE"),
    ("Carla Renata Oliveira Mendes",   "80000000303", "2003-11-05", "carla.oliveira@seed.local",     "(82)987120003", "TEC-SEDE",  "TEC-SEDE-B",  "CONCLUIDA", "NOITE"),
    ("Diego Augusto Barbosa Neto",     "80000000404", "2006-01-18", "diego.barbosa@seed.local",      "(82)987120004", "TEC-SEDE",  "TEC-SEDE-B",  "ATIVA",     "MANHA"),
    ("Elaine Cristina Pereira Santos", "80000000505", "2005-09-30", "elaine.pereira@seed.local",     "(82)987120005", "TEC-SEDE",  "TEC-SEDE-A",  "TRANCADA",  "TARDE"),
    ("Felipe Rodrigues Almeida Costa", "80000000606", "2004-04-14", "felipe.almeida@seed.local",     "(82)987120006", "TEC-SEDE",  "TEC-SEDE-B",  "ATIVA",     "NOITE"),
    ("Gabriela Nascimento Teixeira",   "80000000707", "2005-06-08", "gabriela.nasc@seed.local",      "(82)987120007", "TEC-SEDE",  "TEC-SEDE-A",  "CANCELADA", "MANHA"),
    # ─── TÉCNICO — RIO BRANCO (6) ───────────────────────────────────────────
    ("Henrique Vieira Carvalho",       "80000000808", "2000-05-08", "henrique.vieira@seed.local",    "(68)987120008", "TEC-RB",    "TEC-RB-A",    "ATIVA",     "MANHA"),
    ("Isabela Monteiro Figueiredo",    "80000000909", "2003-08-15", "isabela.monteiro@seed.local",   "(68)987120009", "TEC-RB",    "TEC-RB-A",    "ATIVA",     "TARDE"),
    ("Joao Pedro Sousa Ramos",         "80000001010", "2005-02-27", "joao.sousa@seed.local",         "(68)987120010", "TEC-RB",    "TEC-RB-B",    "ATIVA",     "NOITE"),
    ("Karina Lopes Azevedo",           "80000001111", "2004-06-10", "karina.lopes@seed.local",       "(68)987120011", "TEC-RB",    "TEC-RB-B",    "TRANCADA",  "MANHA"),
    ("Leonardo Andrade Pinto",         "80000001212", "2002-10-03", "leonardo.andrade@seed.local",   "(68)987120012", "TEC-RB",    "TEC-RB-A",    "CONCLUIDA", "TARDE"),
    ("Mariana Cunha Brandao",          "80000001313", "2006-03-25", "mariana.cunha@seed.local",      "(68)987120013", "TEC-RB",    "TEC-RB-B",    "ATIVA",     "NOITE"),
    # ─── TÉCNICO — FLORA CALHEIROS (4) ──────────────────────────────────────
    ("Nathan Borges Queiroz",          "80000001414", "2005-11-11", "nathan.borges@seed.local",      "(82)987120014", "TEC-FC",    "TEC-FC-A",    "ATIVA",     "MANHA"),
    ("Olivia Souza Batista",           "80000001515", "2004-01-07", "olivia.souza@seed.local",       "(82)987120015", "TEC-FC",    "TEC-FC-A",    "ATIVA",     "TARDE"),
    ("Pedro Melo Cavalcante",          "80000001616", "2003-09-19", "pedro.melo@seed.local",         "(82)987120016", "TEC-FC",    "TEC-FC-A",    "CANCELADA", "NOITE"),
    ("Rafaela Duarte Mendonca",        "80000001717", "2005-07-04", "rafaela.duarte@seed.local",     "(82)987120017", "TEC-FC",    "TEC-FC-A",    "ATIVA",     "MANHA"),

    # ─── ITINERANTE — SEDE (6) ───────────────────────────────────────────────
    ("Samuel Gomes Rocha",             "80000001818", "2004-12-01", "samuel.gomes@seed.local",       "(82)987120018", "ITI-SEDE",  "ITI-SEDE-A",  "ATIVA",     "MANHA"),
    ("Tatiana Correia Vilaca",         "80000001919", "2003-04-29", "tatiana.correia@seed.local",    "(82)987120019", "ITI-SEDE",  "ITI-SEDE-A",  "ATIVA",     "TARDE"),
    ("Ulisses Barros Fontes",          "80000002020", "2005-08-08", "ulisses.barros@seed.local",     "(82)987120020", "ITI-SEDE",  "ITI-SEDE-B",  "TRANCADA",  "NOITE"),
    ("Vanessa Lima Guimaraes",         "80000002121", "2004-02-18", "vanessa.lima@seed.local",       "(82)987120021", "ITI-SEDE",  "ITI-SEDE-B",  "ATIVA",     "MANHA"),
    ("Wagner Pires de Souza",          "80000002222", "2002-06-30", "wagner.pires@seed.local",       "(82)987120022", "ITI-SEDE",  "ITI-SEDE-A",  "ATIVA",     "TARDE"),
    ("Ximena Castro Rezende",          "80000002323", "2006-10-16", "ximena.castro@seed.local",      "(82)987120023", "ITI-SEDE",  "ITI-SEDE-B",  "CONCLUIDA", "NOITE"),
    # ─── ITINERANTE — RIO BRANCO (5) ────────────────────────────────────────
    ("Yuri Alves Machado",             "80000002424", "2003-03-03", "yuri.alves@seed.local",         "(68)987120024", "ITI-RB",    "ITI-RB-A",    "ATIVA",     "MANHA"),
    ("Zara Ferreira Couto",            "80000002525", "2004-05-21", "zara.ferreira@seed.local",      "(68)987120025", "ITI-RB",    "ITI-RB-A",    "ATIVA",     "TARDE"),
    ("Artur Nascimento Faria",         "80000002626", "2001-11-14", "artur.nasc@seed.local",         "(68)987120026", "ITI-RB",    "ITI-RB-B",    "CANCELADA", "NOITE"),
    ("Brenda Marques Ribeiro",         "80000002727", "2005-01-28", "brenda.marques@seed.local",     "(68)987120027", "ITI-RB",    "ITI-RB-B",    "ATIVA",     "MANHA"),
    ("Cesar Eduardo Matos Leal",       "80000002828", "2003-07-07", "cesar.matos@seed.local",        "(68)987120028", "ITI-RB",    "ITI-RB-A",    "TRANCADA",  "TARDE"),
    # ─── ITINERANTE — FLORA CALHEIROS (6) ───────────────────────────────────
    ("Daniela Freitas Santana",        "80000002929", "2004-09-09", "daniela.freitas@seed.local",    "(82)987120029", "ITI-FC",    "ITI-FC-A",    "ATIVA",     "MANHA"),
    ("Evandro Soares Pimentel",        "80000003030", "2002-04-04", "evandro.soares@seed.local",     "(82)987120030", "ITI-FC",    "ITI-FC-A",    "ATIVA",     "TARDE"),
    ("Fabiana Rocha Coutinho",         "80000003131", "2005-12-12", "fabiana.rocha@seed.local",      "(82)987120031", "ITI-FC",    "ITI-FC-B",    "CONCLUIDA", "NOITE"),
    ("Gustavo Teles Maia",             "80000003232", "2003-06-17", "gustavo.teles@seed.local",      "(82)987120032", "ITI-FC",    "ITI-FC-B",    "ATIVA",     "MANHA"),
    ("Helena Pacheco Drummond",        "80000003333", "2004-08-23", "helena.pacheco@seed.local",     "(82)987120033", "ITI-FC",    "ITI-FC-A",    "ATIVA",     "TARDE"),
    ("Igor Cavalcanti Vasconcelos",    "80000003434", "2005-10-10", "igor.cavalcanti@seed.local",    "(82)987120034", "ITI-FC",    "ITI-FC-B",    "TRANCADA",  "NOITE"),

    # ─── REMOTO — SEDE (5) ───────────────────────────────────────────────────
    ("Julia Meirelles Bastos",         "80000003535", "2003-02-14", "julia.meirelles@seed.local",    "(82)987120035", "REM-SEDE",  "REM-SEDE-A",  "ATIVA",     "NOITE"),
    ("Kleber Romualdo Peixoto",        "80000003636", "2004-11-02", "kleber.romualdo@seed.local",    "(82)987120036", "REM-SEDE",  "REM-SEDE-A",  "ATIVA",     "NOITE"),
    ("Luciana Fonseca Tavares",        "80000003737", "2001-07-19", "luciana.fonseca@seed.local",    "(82)987120037", "REM-SEDE",  "REM-SEDE-A",  "TRANCADA",  "NOITE"),
    ("Marcelo Dias Novaes",            "80000003838", "2005-04-06", "marcelo.dias@seed.local",       "(82)987120038", "REM-SEDE",  "REM-SEDE-A",  "ATIVA",     "NOITE"),
    ("Natalia Prado Sepulveda",        "80000003939", "2006-09-13", "natalia.prado@seed.local",      "(82)987120039", "REM-SEDE",  "REM-SEDE-A",  "CONCLUIDA", "NOITE"),
    # ─── REMOTO — RIO BRANCO (6) ────────────────────────────────────────────
    ("Orlando Luz Medeiros",           "80000004040", "2003-12-26", "orlando.luz@seed.local",        "(68)987120040", "REM-RB",    "REM-RB-A",    "ATIVA",     "NOITE"),
    ("Priscila Aguiar Paiva",          "80000004141", "2004-03-31", "priscila.aguiar@seed.local",    "(68)987120041", "REM-RB",    "REM-RB-A",    "ATIVA",     "NOITE"),
    ("Quincy Batista Aragao",          "80000004242", "2002-08-08", "quincy.batista@seed.local",     "(68)987120042", "REM-RB",    "REM-RB-A",    "CONCLUIDA", "NOITE"),
    ("Rita Amorim Gadelha",            "80000004343", "2005-05-05", "rita.amorim@seed.local",        "(68)987120043", "REM-RB",    "REM-RB-A",    "ATIVA",     "NOITE"),
    ("Silas Mendonca Rios",            "80000004444", "2003-10-22", "silas.mendonca@seed.local",     "(68)987120044", "REM-RB",    "REM-RB-A",    "TRANCADA",  "NOITE"),
    ("Talita Vianna Azambuja",         "80000004545", "2004-07-15", "talita.vianna@seed.local",      "(68)987120045", "REM-RB",    "REM-RB-A",    "ATIVA",     "NOITE"),
    # ─── REMOTO — FLORA CALHEIROS (6) ───────────────────────────────────────
    ("Umberto Sales Viana",            "80000004646", "2002-01-25", "umberto.sales@seed.local",      "(82)987120046", "REM-FC",    "REM-FC-A",    "ATIVA",     "NOITE"),
    ("Viviane Mota Furtado",           "80000004747", "2005-06-06", "viviane.mota@seed.local",       "(82)987120047", "REM-FC",    "REM-FC-A",    "ATIVA",     "NOITE"),
    ("Wilson Rocha Leandro",           "80000004848", "2003-03-14", "wilson.rocha@seed.local",       "(82)987120048", "REM-FC",    "REM-FC-A",    "CANCELADA", "NOITE"),
    ("Yasmin Correa Pinheiro",         "80000004949", "2006-11-20", "yasmin.correa@seed.local",      "(82)987120049", "REM-FC",    "REM-FC-A",    "ATIVA",     "NOITE"),
    ("Zelio Camargo Torres",           "80000005050", "2004-08-29", "zelio.camargo@seed.local",      "(82)987120050", "REM-FC",    "REM-FC-A",    "TRANCADA",  "NOITE"),
]

# Identificador exclusivo nos assuntos de processo seed (para reset seletivo)
SEED_TAG = "SEED50 "


class Command(BaseCommand):
    help = (
        "Popula o banco com 50 alunos persistentes de teste. "
        "Idempotente: detecta registros existentes por CPF antes de criar."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Remove os registros criados por este seed antes de recriar.",
        )

    def handle(self, *args, **options):
        from apps.cursos.models import AreaCurso, Curso
        from apps.matriculas.models import Matricula
        from apps.turmas.models import Polo, Turma
        from apps.unidades.models import Unidade
        from apps.usuarios.models import Aluno, Pessoa, Usuario

        with transaction.atomic():
            if options["reset"]:
                self._reset(Usuario, Pessoa, Aluno, Matricula, Turma, Curso, Polo)

            unidades = self._seed_unidades(Unidade)
            polos = self._seed_polos(Polo, unidades)
            area_curso = self._seed_area_curso(AreaCurso)
            cursos = self._seed_cursos(Curso, unidades, area_curso)
            turmas = self._seed_turmas(Turma, cursos, polos)
            criados, pulados = self._seed_alunos(
                Pessoa, Usuario, Aluno, Matricula, cursos, turmas
            )
            self._seed_processos(Usuario)

        self.stdout.write(
            self.style.SUCCESS(
                f"seed_50_alunos concluído — criados: {criados}, já existiam: {pulados}."
            )
        )
        self.stdout.write("Senha padrão de todos os alunos seed: 123mudar")

    # ── Reset ─────────────────────────────────────────────────────────────────

    def _reset(self, Usuario, Pessoa, Aluno, Matricula, Turma, Curso, Polo):
        from apps.processos.models import Processo
        cpfs = [row[1] for row in ALUNOS_SEED]
        Processo.objects.filter(assunto__startswith="SEED50 ", requerente__cpf__in=cpfs).delete()
        Matricula.objects.filter(aluno__cpf__in=cpfs).delete()
        Usuario.objects.filter(cpf__in=cpfs).delete()
        Pessoa.objects.filter(cpf__in=cpfs).delete()
        # Remover turmas/cursos seed apenas se não houver matrículas de outros alunos
        for sigla in [
            "TEC-SEDE", "TEC-RB", "TEC-FC",
            "ITI-SEDE", "ITI-RB", "ITI-FC",
            "REM-SEDE", "REM-RB", "REM-FC",
        ]:
            curso = Curso.objects.filter(sigla=sigla).first()
            if curso and not curso.matriculas.exclude(aluno__cpf__in=cpfs).exists():
                Turma.objects.filter(curso=curso).delete()
                curso.delete()
        self.stdout.write(self.style.WARNING("Registros seed anteriores removidos."))

    # ── Unidades ──────────────────────────────────────────────────────────────

    def _seed_unidades(self, Unidade):
        unidades = {}
        especificacoes = [
            ("sede",           "Sede",           "Av. Principal, 1000", "Porto Velho",   "RO"),
            ("rio_branco",     "Rio Branco",     "Av. Brasil, 999",     "Rio Branco",    "AC"),
            ("flora_calheiros","Flora Calheiros", "Rua das Flores, 55", "União dos Palmares", "AL"),
        ]
        for codigo, nome, endereco, cidade, uf in especificacoes:
            obj, created = Unidade.objects.get_or_create(
                codigo=codigo,
                defaults={"nome": nome, "endereco": endereco, "cidade": cidade, "uf": uf},
            )
            unidades[codigo] = obj
            if created:
                self.stdout.write(f"  Unidade criada: {obj}")
        return unidades

    # ── Polos ─────────────────────────────────────────────────────────────────

    def _seed_polos(self, Polo, unidades):
        polos = {}
        especificacoes = [
            ("Sede",           "Porto Velho",        "RO"),
            ("Rio Branco",     "Rio Branco",         "AC"),
            ("Flora Calheiros","União dos Palmares",  "AL"),
        ]
        for nome, municipio, uf in especificacoes:
            obj, _ = Polo.objects.get_or_create(
                nome=nome,
                municipio=municipio,
                defaults={"uf": uf, "ativo": True},
            )
            polos[nome] = obj
        return polos

    # ── Área de curso ─────────────────────────────────────────────────────────

    def _seed_area_curso(self, AreaCurso):
        area, _ = AreaCurso.objects.get_or_create(
            descricao="Formação Profissional Técnica SEED50",
            defaults={
                "codigo_cine": "0613",
                "cine": "Desenvolvimento de software e aplicações",
                "area_detalhada": "Tecnologia da informação",
                "area_especifica": "Informática",
                "area_geral": "Computação",
            },
        )
        return area

    # ── Cursos ────────────────────────────────────────────────────────────────

    def _seed_cursos(self, Curso, unidades, area_curso):
        """
        Cria 9 cursos — um por combinação (modalidade × unidade).

        sigla_interna → (unidade_codigo, tipo_curso, nome, carga_horaria)
        """
        especificacoes = {
            "TEC-SEDE": ("sede",            "tecnico",          "Tecnico em Informatica — Sede",           1200),
            "TEC-RB":   ("rio_branco",      "tecnico",          "Tecnico em Administracao — Rio Branco",   1200),
            "TEC-FC":   ("flora_calheiros", "tecnico",          "Tecnico em Enfermagem — Flora Calheiros", 1200),
            "ITI-SEDE": ("sede",            "itinerante",       "Qualificacao Itinerante — Sede",           800),
            "ITI-RB":   ("rio_branco",      "itinerante",       "Qualificacao Itinerante — Rio Branco",     800),
            "ITI-FC":   ("flora_calheiros", "itinerante",       "Qualificacao Itinerante — Flora Calheiros",800),
            "REM-SEDE": ("sede",            "formacao_inicial", "Formacao Remota — Sede",                   600),
            "REM-RB":   ("rio_branco",      "formacao_inicial", "Formacao Remota — Rio Branco",             600),
            "REM-FC":   ("flora_calheiros", "formacao_inicial", "Formacao Remota — Flora Calheiros",        600),
        }
        cursos = {}
        for sigla, (unidade_codigo, tipo, nome, ch) in especificacoes.items():
            obj, created = Curso.objects.get_or_create(
                sigla=sigla,
                defaults={
                    "nome": nome,
                    "tipo_curso": tipo,
                    "carga_horaria": ch,
                    "unidade": unidades[unidade_codigo],
                    "area_curso": area_curso,
                },
            )
            cursos[sigla] = obj
            if created:
                self.stdout.write(f"  Curso criado: {obj}")
        return cursos

    # ── Turmas ────────────────────────────────────────────────────────────────

    def _seed_turmas(self, Turma, cursos, polos):
        """
        Cria turmas necessárias. Turmas itinerantes precisam de polo.
        Turmas remotas usam modalidade REMOTO.
        """
        _POLO_MAP = {
            "ITI-SEDE": polos["Sede"],
            "ITI-RB":   polos["Rio Branco"],
            "ITI-FC":   polos["Flora Calheiros"],
        }
        _MODALIDADE_MAP = {
            "TEC-SEDE": "PRESENCIAL", "TEC-RB":   "PRESENCIAL", "TEC-FC":   "PRESENCIAL",
            "ITI-SEDE": "ITINERANTE", "ITI-RB":   "ITINERANTE", "ITI-FC":   "ITINERANTE",
            "REM-SEDE": "REMOTO",     "REM-RB":   "REMOTO",     "REM-FC":   "REMOTO",
        }

        # Coleta os nomes de turma que precisam existir
        turmas_necessarias = {}
        for row in ALUNOS_SEED:
            sigla_curso = row[5]
            nome_turma  = row[6]
            if nome_turma not in turmas_necessarias:
                turmas_necessarias[nome_turma] = sigla_curso

        turmas = {}
        for nome_turma, sigla_curso in turmas_necessarias.items():
            curso    = cursos[sigla_curso]
            polo     = _POLO_MAP.get(sigla_curso)
            modal    = _MODALIDADE_MAP[sigla_curso]
            obj, created = Turma.objects.get_or_create(
                nome=nome_turma,
                curso=curso,
                defaults={
                    "ano_letivo":         2025,
                    "status":             "ATIVA",
                    "modalidade":         modal,
                    "capacidade_maxima":  30,
                    "polo":               polo,
                },
            )
            turmas[nome_turma] = obj
            if created:
                self.stdout.write(f"  Turma criada: {obj}")
        return turmas

    # ── Alunos ────────────────────────────────────────────────────────────────

    def _seed_alunos(self, Pessoa, Usuario, Aluno, Matricula, cursos, turmas):
        criados = 0
        pulados = 0

        for (nome, cpf, nasc, email, tel,
             sigla_curso, nome_turma, status_mat, turno) in ALUNOS_SEED:

            if Usuario.objects.filter(cpf=cpf).exists():
                pulados += 1
                continue

            # Pessoa
            primeiro = nome.split()[0]
            sobrenome = " ".join(nome.split()[1:])
            pessoa, _ = Pessoa.objects.get_or_create(
                cpf=cpf,
                defaults={
                    "nome_completo": nome,
                    "email":         email,
                    "telefone":      tel,
                    "data_nascimento": nasc,
                    "ativo":         True,
                },
            )

            # Usuário aluno
            usuario = Usuario.objects.create_user(
                username=cpf,
                cpf=cpf,
                tipo="ALUNO",
                first_name=primeiro,
                last_name=sobrenome,
                email=email,
                is_active=True,
                pessoa=pessoa,
            )
            usuario.set_password("123mudar")
            usuario.save()

            # Perfil Aluno
            Aluno.objects.get_or_create(
                pessoa=pessoa,
                defaults={"situacao": "ATIVO"},
            )

            # Matrícula
            curso = cursos[sigla_curso]
            turma = turmas[nome_turma]
            Matricula.objects.create(
                aluno=usuario,
                curso=curso,
                turma=turma,
                status=status_mat,
                tipo_matricula="NOVA",
                turno=turno,
            )

            criados += 1
            self.stdout.write(f"  + {nome} ({cpf})")

        return criados, pulados

    # ── Processos ─────────────────────────────────────────────────────────────

    def _seed_processos(self, Usuario):
        """Cria um processo seed para cada aluno para popular /processos."""
        from apps.processos.models import Processo, Tramitacao

        # Modelos de processo variados para cobrir todos os tipos e status
        _TIPOS = [
            "REQUERIMENTO", "RECURSO", "TRANSFERENCIA", "SOLICITACAO", "OUTROS",
        ]
        _STATUS = [
            "ABERTO", "EM_TRAMITACAO", "CONCLUIDO", "ARQUIVADO",
        ]
        _ASSUNTOS = [
            "Solicitacao de declaracao de matricula",
            "Recurso de nota — 1 bimestre",
            "Transferencia externa para outra unidade",
            "Solicitacao de aproveitamento de componente",
            "Pedido de segunda chamada de avaliacao",
            "Revisao de frequencia — ausencias justificadas",
            "Solicitacao de trancamento de matricula",
            "Requerimento de emissao de historico escolar",
            "Recurso de indeferimento de inscricao",
            "Outros requerimentos academicos",
        ]

        cpfs = [row[1] for row in ALUNOS_SEED]
        alunos = list(Usuario.objects.filter(cpf__in=cpfs))

        criados_proc = 0
        for idx, aluno in enumerate(alunos):
            tipo   = _TIPOS[idx % len(_TIPOS)]
            status = _STATUS[idx % len(_STATUS)]
            assunto = _ASSUNTOS[idx % len(_ASSUNTOS)]
            tag_assunto = f"SEED50 {assunto}"

            if Processo.objects.filter(requerente=aluno, assunto=tag_assunto).exists():
                continue

            processo = Processo.objects.create(
                tipo=tipo,
                requerente=aluno,
                assunto=tag_assunto,
                descricao=(
                    f"Processo de teste gerado automaticamente para {aluno.get_full_name()}. "
                    "Nao requer acao real."
                ),
                status=status,
            )

            # Adiciona ao menos uma tramitação para cobrir listagens de tramitações
            Tramitacao.objects.create(
                processo=processo,
                responsavel=aluno,
                setor_destino="Secretaria Academica",
                acao="RECEBIDO",
                observacao="Protocolo recebido automaticamente pelo seed de teste.",
            )
            criados_proc += 1

        if criados_proc:
            self.stdout.write(f"  Processos seed criados: {criados_proc}")
        else:
            self.stdout.write("  Processos seed ja existiam — nenhum criado.")
