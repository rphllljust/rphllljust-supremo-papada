from datetime import date

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.cursos.models import Curso
from apps.matriculas.models import Matricula
from apps.turmas.models import Turma
from apps.unidades.models import Unidade
from apps.usuarios.models import Usuario

from .models import Frequencia


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


class FrequenciaCrudTests(TestCase):
    def setUp(self):
        self.unidade, _ = Unidade.objects.get_or_create(codigo="sede", defaults={"nome": "Sede"})
        self.curso = Curso.objects.create(unidade=self.unidade, nome="Administracao", carga_horaria=1000, tipo_curso="tecnico")
        self.professor = Usuario.objects.create_user(
            username="prof_freq",
            cpf="52345678901",
            tipo="PROFESSOR",
            password="x",
        )
        self.aluno = Usuario.objects.create_user(
            username="aluno_freq",
            cpf="52345678902",
            tipo="ALUNO",
            password="x",
        )
        self.turma = Turma.objects.create(
            curso=self.curso,
            nome="ADM-2",
            ano_letivo=2026,
            professor_responsavel=self.professor,
        )
        self.matricula = Matricula.objects.create(
            aluno=self.aluno,
            curso=self.curso,
            turma=self.turma,
            status="ATIVA",
            turno="MANHA",
        )

    def test_create_frequencia(self):
        response = self.client.post(
            reverse("frequencia:frequencia_create"),
            {
                "matricula": self.matricula.pk,
                "data": "2026-03-01",
                "presente": "on",
                "observacao": "Chegou no horario.",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Frequencia.objects.filter(matricula=self.matricula, data=date(2026, 3, 1)).exists())

    def test_list_frequencia(self):
        Frequencia.objects.create(matricula=self.matricula, data=date(2026, 3, 2), presente=True)

        response = self.client.get(reverse("frequencia:frequencia_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "02/03/2026")

    def test_delete_frequencia(self):
        registro = Frequencia.objects.create(
            matricula=self.matricula,
            data=date(2026, 3, 3),
            presente=False,
            observacao="Falta justificada.",
        )

        response = self.client.post(reverse("frequencia:frequencia_delete", args=[registro.pk]), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Frequencia.objects.filter(pk=registro.pk).exists())


class FrequenciaApiFiltersTests(TestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.unidade, _ = Unidade.objects.get_or_create(codigo="sede", defaults={"nome": "Sede"})
        self.professor = Usuario.objects.create_user(
            username="prof_api_freq",
            cpf=gerar_cpf(723456780),
            tipo="PROFESSOR",
            password="senha123",
            first_name="Marina",
            last_name="Frequencia",
        )
        self.outro_professor = Usuario.objects.create_user(
            username="prof_api_freq_2",
            cpf=gerar_cpf(723456781),
            tipo="PROFESSOR",
            password="senha123",
            first_name="Rafael",
            last_name="Chamada",
        )
        self.aluno = Usuario.objects.create_user(
            username="aluno_api_freq",
            cpf=gerar_cpf(723456782),
            tipo="ALUNO",
            password="x",
        )
        self.outro_aluno = Usuario.objects.create_user(
            username="aluno_api_freq_2",
            cpf=gerar_cpf(723456783),
            tipo="ALUNO",
            password="x",
        )
        self.curso = Curso.objects.create(unidade=self.unidade, nome="Logistica", carga_horaria=900, tipo_curso="tecnico")
        self.outro_curso = Curso.objects.create(unidade=self.unidade, nome="Financas", carga_horaria=800, tipo_curso="tecnico")
        self.turma = Turma.objects.create(curso=self.curso, nome="LOG-API", ano_letivo=2026, professor_responsavel=self.professor)
        self.outra_turma = Turma.objects.create(curso=self.outro_curso, nome="FIN-API", ano_letivo=2026, professor_responsavel=self.outro_professor)
        self.matricula = Matricula.objects.create(aluno=self.aluno, curso=self.curso, turma=self.turma, status="ATIVA", turno="MANHA")
        self.outra_matricula = Matricula.objects.create(aluno=self.outro_aluno, curso=self.outro_curso, turma=self.outra_turma, status="ATIVA", turno="TARDE")
        self.frequencia = Frequencia.objects.create(matricula=self.matricula, data=date(2026, 3, 12), presente=True)
        Frequencia.objects.create(matricula=self.outra_matricula, data=date(2026, 3, 13), presente=False)

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
            reverse("api_v1_frequencias:list"),
            {
                "curso": self.curso.id,
                "turma": self.turma.id,
                "professor": self.professor.id,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.frequencia.id)
        self.assertEqual(response.data["results"][0]["professor_nome"], "Marina Frequencia")

    def test_professor_scope_hides_frequency_from_other_professors_without_filters(self):
        response = self.api_client.get(reverse("api_v1_frequencias:list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.frequencia.id)
