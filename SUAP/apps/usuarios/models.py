from django.contrib.auth.models import AbstractUser
from django.db import models


class Pessoa(models.Model):
    nome_completo = models.CharField(max_length=200)
    cpf = models.CharField(max_length=11, unique=True)
    data_nascimento = models.DateField(null=True, blank=True)
    email = models.EmailField(blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome_completo"]

    def __str__(self):
        return self.nome_completo


class Endereco(models.Model):
    pessoa = models.ForeignKey(Pessoa, on_delete=models.CASCADE, related_name="enderecos")
    cep = models.CharField(max_length=8)
    logradouro = models.CharField(max_length=200)
    numero = models.CharField(max_length=20)
    complemento = models.CharField(max_length=120, blank=True)
    bairro = models.CharField(max_length=120)
    municipio = models.CharField(max_length=120)
    uf = models.CharField(max_length=2)
    principal = models.BooleanField(default=True)

    class Meta:
        ordering = ["-principal", "id"]

    def __str__(self):
        return f"{self.logradouro}, {self.numero} - {self.municipio}/{self.uf}"


class DocumentoPessoal(models.Model):
    TIPO_CHOICES = (
        ("RG", "RG"),
        ("CPF", "CPF"),
        ("CERTIDAO", "Certidao"),
        ("OUTRO", "Outro"),
    )

    pessoa = models.ForeignKey(Pessoa, on_delete=models.CASCADE, related_name="documentos_pessoais")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    numero = models.CharField(max_length=50)
    orgao_emissor = models.CharField(max_length=50, blank=True)
    uf_emissor = models.CharField(max_length=2, blank=True)

    class Meta:
        unique_together = ("pessoa", "tipo", "numero")
        ordering = ["tipo", "numero"]

    def __str__(self):
        return f"{self.tipo} - {self.numero}"


class Usuario(AbstractUser):
    TIPO_CHOICES = (
        ("ALUNO", "Aluno"),
        ("PROFESSOR", "Professor"),
        ("SECRETARIA", "Secretaria"),
        ("COORDENACAO", "Coordenacao/Consulta"),
        ("ADMIN", "Administrador"),
    )

    cpf = models.CharField(max_length=11, unique=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    pessoa = models.OneToOneField(Pessoa, on_delete=models.SET_NULL, null=True, blank=True, related_name="usuario")

    def __str__(self):
        return f"{self.username} - {self.tipo}"


class Aluno(models.Model):
    SITUACAO_CHOICES = (
        ("ATIVO", "Ativo"),
        ("INATIVO", "Inativo"),
    )

    pessoa = models.OneToOneField(Pessoa, on_delete=models.CASCADE, related_name="aluno")
    usuario = models.OneToOneField(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name="perfil_aluno")
    data_ingresso = models.DateField(auto_now_add=True)
    situacao = models.CharField(max_length=10, choices=SITUACAO_CHOICES, default="ATIVO")

    class Meta:
        ordering = ["pessoa__nome_completo"]

    def __str__(self):
        return self.pessoa.nome_completo


class Responsavel(models.Model):
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name="responsaveis")
    pessoa = models.ForeignKey(Pessoa, on_delete=models.CASCADE, related_name="responsabilidades")
    parentesco = models.CharField(max_length=50)
    responsavel_principal = models.BooleanField(default=False)
    contato_principal = models.CharField(max_length=120)

    class Meta:
        unique_together = ("aluno", "pessoa", "parentesco")

    def __str__(self):
        return f"{self.pessoa.nome_completo} ({self.parentesco})"

