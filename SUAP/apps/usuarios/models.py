from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    TIPO_CHOICES = (
        ('ALUNO', 'Aluno'),
        ('PROFESSOR', 'Professor'),
        ('SECRETARIA', 'Secretaria'),
        ('ADMIN', 'Administrador'),
    )

    cpf = models.CharField(max_length=11, unique=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)

    def __str__(self):
        return f"{self.username} - {self.tipo}"