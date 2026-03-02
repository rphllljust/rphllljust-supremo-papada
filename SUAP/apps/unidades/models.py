from django.db import models


class Unidade(models.Model):
    nome = models.CharField(max_length=200)
    codigo = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.nome