from django.test import TestCase

from apps.api.v1.matriculas.serializers import MatriculaSerializer
from apps.cursos.models import Curso
from apps.matriculas.models import Matricula
from apps.turmas.models import Turma
from apps.unidades.models import Unidade
from apps.usuarios.models import Usuario


class MatriculaSerializerRequiredDocsTests(TestCase):
    def setUp(self):
        self.unidade, _ = Unidade.objects.get_or_create(codigo="sede", defaults={"nome": "Sede"})
        self.curso = Curso.objects.create(unidade=self.unidade, nome="Administracao", carga_horaria=1000)
        self.professor = Usuario.objects.create_user(
            username="prof_docs",
            cpf="32345678901",
            tipo="PROFESSOR",
            password="x",
        )
        self.aluno = Usuario.objects.create_user(
            username="aluno_docs",
            cpf="32345678902",
            tipo="ALUNO",
            password="x",
        )
        self.turma = Turma.objects.create(
            curso=self.curso,
            nome="ADM-DOCS",
            ano_letivo=2026,
            professor_responsavel=self.professor,
            status="ATIVA",
        )
        self.matricula = Matricula.objects.create(
            aluno=self.aluno,
            curso=self.curso,
            turma=self.turma,
            status="TRANCADA",
            tipo_matricula="NOVA",
        )

    def test_blocks_activate_without_required_docs_validated(self):
        serializer = MatriculaSerializer(
            instance=self.matricula,
            data={
                "aluno": self.aluno.id,
                "curso": self.curso.id,
                "turma": self.turma.id,
                "status": "ATIVA",
                "tipo_matricula": "NOVA",
                "turno": "",
                "version": self.matricula.version,
            },
            partial=True,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("status", serializer.errors)
