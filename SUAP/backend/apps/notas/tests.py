from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.cursos.models import Curso
from apps.matriculas.models import Matricula
from apps.turmas.models import Turma
from apps.unidades.models import Unidade
from apps.usuarios.models import Usuario

from .models import Nota


def gerar_cpf(seed: int) -> str:
    base = f"{seed:09d}"[-9:]

    def dv(parcial: str) -> str:
        peso_inicial = len(parcial) + 1
        total = sum(int(digito) * (peso_inicial - indice) for indice, digito in enumerate(parcial))
        resto = 11 - (total % 11)
        return "0" if resto >= 10 else str(resto)

    d1 = dv(base)
    d2 = dv(base + d1)
    return f"{base}{d1}{d2}"


class NotaCrudTests(TestCase):
    def setUp(self):
        self.unidade, _ = Unidade.objects.get_or_create(codigo="sede", defaults={"nome": "Sede"})
        self.curso = Curso.objects.create(unidade=self.unidade, nome="Informatica", carga_horaria=1200)
        self.professor = Usuario.objects.create_user(
            username="prof_notas",
            cpf="42345678901",
            tipo="PROFESSOR",
            password="x",
        )
        self.aluno = Usuario.objects.create_user(
            username="aluno_notas",
            cpf="42345678902",
            tipo="ALUNO",
            password="x",
        )
        self.turma = Turma.objects.create(
            curso=self.curso,
            nome="INFO-1",
            ano_letivo=2026,
            professor_responsavel=self.professor,
        )
        self.matricula = Matricula.objects.create(
            aluno=self.aluno,
            curso=self.curso,
            turma=self.turma,
            status="ATIVA",
        )

    def test_create_nota(self):
        response = self.client.post(
            reverse("notas:notas_create"),
            {
                "matricula": self.matricula.pk,
                "descricao": "Prova 1",
                "valor": "8.50",
                "peso": "1.00",
                "data_lancamento": "2026-03-01",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Nota.objects.filter(matricula=self.matricula, descricao="Prova 1").exists())

    def test_list_notas(self):
        Nota.objects.create(
            matricula=self.matricula,
            descricao="Trabalho",
            valor=Decimal("9.00"),
            peso=Decimal("1.00"),
            data_lancamento=date(2026, 3, 2),
        )

        response = self.client.get(reverse("notas:notas_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Trabalho")

    def test_delete_nota(self):
        nota = Nota.objects.create(
            matricula=self.matricula,
            descricao="Seminario",
            valor=Decimal("7.50"),
            peso=Decimal("1.00"),
            data_lancamento=date(2026, 3, 3),
        )

        response = self.client.post(reverse("notas:notas_delete", args=[nota.pk]), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Nota.objects.filter(pk=nota.pk).exists())


class NotaApiFiltersTests(TestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.unidade, _ = Unidade.objects.get_or_create(codigo="sede", defaults={"nome": "Sede"})
        self.professor = Usuario.objects.create_user(
            username="prof_api_notas",
            cpf=gerar_cpf(623456780),
            tipo="PROFESSOR",
            password="senha123",
            first_name="Paulo",
            last_name="Professor",
        )
        self.outro_professor = Usuario.objects.create_user(
            username="prof_api_notas_2",
            cpf=gerar_cpf(623456781),
            tipo="PROFESSOR",
            password="senha123",
            first_name="Carla",
            last_name="Docente",
        )
        self.aluno = Usuario.objects.create_user(
            username="aluno_api_notas",
            cpf=gerar_cpf(623456782),
            tipo="ALUNO",
            password="x",
        )
        self.curso = Curso.objects.create(unidade=self.unidade, nome="Informatica", carga_horaria=1200)
        self.outro_curso = Curso.objects.create(unidade=self.unidade, nome="Administracao", carga_horaria=1000)
        self.turma = Turma.objects.create(curso=self.curso, nome="INFO-API", ano_letivo=2026, professor_responsavel=self.professor)
        self.outra_turma = Turma.objects.create(curso=self.outro_curso, nome="ADM-API", ano_letivo=2026, professor_responsavel=self.outro_professor)
        self.matricula = Matricula.objects.create(aluno=self.aluno, curso=self.curso, turma=self.turma, status="ATIVA")
        self.outra_matricula = Matricula.objects.create(aluno=self.aluno, curso=self.outro_curso, turma=self.outra_turma, status="ATIVA")
        self.nota = Nota.objects.create(matricula=self.matricula, descricao="Prova API", valor=Decimal("8.00"), peso=Decimal("1.00"), data_lancamento=date(2026, 3, 10))
        Nota.objects.create(matricula=self.outra_matricula, descricao="Trabalho API", valor=Decimal("7.00"), peso=Decimal("1.00"), data_lancamento=date(2026, 3, 11))

        token_response = self.api_client.post(
            reverse("api_v1_auth:token_obtain_pair"),
            {
                "cpf": self.professor.cpf,
                "password": "senha123",
                "perfil": "PROFESSOR",
            },
            format="json",
        )
        self.assertEqual(token_response.status_code, 200)
        self.api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}")

    def test_list_filters_by_curso_turma_and_professor(self):
        response = self.api_client.get(
            reverse("api_v1_notas:list"),
            {
                "curso": self.curso.id,
                "turma": self.turma.id,
                "professor": self.professor.id,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.nota.id)
        self.assertEqual(response.data["results"][0]["professor_nome"], "Paulo Professor")

    def test_professor_scope_hides_notes_from_other_professors_without_filters(self):
        response = self.api_client.get(reverse("api_v1_notas:list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.nota.id)
