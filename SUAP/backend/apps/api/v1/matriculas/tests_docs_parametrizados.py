from django.test import TestCase

from apps.api.v1.matriculas.serializers import MatriculaSerializer
from apps.cursos.models import Curso
from apps.matriculas.models import DocumentoObrigatorioCurso, Matricula
from apps.turmas.models import Turma
from apps.unidades.models import Unidade
from apps.usuarios.models import Usuario


class MatriculaDocumentosParametrizadosTests(TestCase):
    def setUp(self):
        self.unidade, _ = Unidade.objects.get_or_create(codigo="sede", defaults={"nome": "Sede"})
        self.curso = Curso.objects.create(unidade=self.unidade, nome="Administracao", carga_horaria=1000)
        self.professor = Usuario.objects.create_user(
            username="prof_docs_param",
            cpf="90000010101",
            tipo="PROFESSOR",
            password="x",
        )
        self.aluno = Usuario.objects.create_user(
            username="aluno_docs_param",
            cpf="90000010102",
            tipo="ALUNO",
            password="x",
        )
        self.turma = Turma.objects.create(curso=self.curso, nome="ADM-PARAM", ano_letivo=2026, status="ATIVA")
        self.matricula = Matricula.objects.create(
            aluno=self.aluno,
            curso=self.curso,
            turma=self.turma,
            status="TRANCADA",
            tipo_matricula="NOVA",
        )

    def test_uses_course_document_configuration_when_present(self):
        DocumentoObrigatorioCurso.objects.create(curso=self.curso, tipo_documento="HISTORICO_ESCOLAR", ativo=True)

        serializer = MatriculaSerializer(
            instance=self.matricula,
            data={"status": "ATIVA", "version": self.matricula.version},
            partial=True,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("status", serializer.errors)
        self.assertIn("HISTORICO_ESCOLAR", str(serializer.errors["status"]))
