from django.test import TestCase

from apps.api.v1.alunos.serializers import AlunoSerializer


class AlunoSerializerEmailValidationTests(TestCase):
    def test_rejects_invalid_email_format(self):
        serializer = AlunoSerializer(
            data={
                "nome_completo": "Aluno Teste",
                "email": "email-invalido",
                "cpf": "52998224725",
                "is_active": True,
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_rejects_overlong_full_name(self):
        serializer = AlunoSerializer(
            data={
                "nome_completo": "A" * 201,
                "email": "aluno@example.com",
                "cpf": "52998224725",
                "is_active": True,
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("nome_completo", serializer.errors)
