from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class PerfilUsuario(models.TextChoices):
    ALUNO = "ALUNO", "Aluno"
    PROFESSOR = "PROFESSOR", "Professor"
    SECRETARIA = "SECRETARIA", "Secretaria"
    COORDENACAO = "COORDENACAO", "Coordenacao/Consulta"
    ADMIN = "ADMIN", "Administrador"

    @classmethod
    def autenticaveis(cls):
        return (cls.PROFESSOR, cls.SECRETARIA, cls.COORDENACAO, cls.ADMIN)

    @classmethod
    def autenticaveis_choices(cls):
        return [(perfil.value, perfil.label) for perfil in cls.autenticaveis()]


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
    cpf = models.CharField(max_length=11, unique=True)
    tipo = models.CharField(max_length=20, choices=PerfilUsuario)
    pessoa = models.OneToOneField(Pessoa, on_delete=models.SET_NULL, null=True, blank=True, related_name="usuario")
    setor = models.ForeignKey("setores.Setor", on_delete=models.SET_NULL, null=True, blank=True, related_name="servidores")

    def __str__(self):
        return f"{self.username} - {self.tipo}"


class ServidorPerfil(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name="perfil_servidor")
    matricula_servidor = models.CharField(max_length=20, unique=True)
    nome_usual = models.CharField(max_length=120, blank=True)
    email_institucional = models.EmailField(blank=True)
    email_siape = models.EmailField(blank=True)
    email_secundario_recuperacao = models.EmailField(blank=True)
    email_notificacoes = models.EmailField(blank=True)
    email_google_sala = models.EmailField(blank=True)
    telefones_institucionais = models.CharField(max_length=255, blank=True)
    telefones_pessoais = models.CharField(max_length=255, blank=True)
    em_pgd = models.BooleanField(default=False)
    nao_tem_impressao_digital = models.BooleanField(default=False)
    estado_civil = models.CharField(max_length=80, blank=True)
    naturalidade = models.CharField(max_length=120, blank=True)
    sexo = models.CharField(max_length=30, blank=True)
    grupo_sanguineo_rh = models.CharField(max_length=20, blank=True)
    dependentes_ir = models.PositiveSmallIntegerField(null=True, blank=True)
    raca_etnia = models.CharField(max_length=80, blank=True)
    nome_pai = models.CharField(max_length=200, blank=True)
    nome_mae = models.CharField(max_length=200, blank=True)
    pis_pasep = models.CharField(max_length=40, blank=True)
    titulacao = models.CharField(max_length=120, blank=True)
    escolaridade = models.CharField(max_length=120, blank=True)
    identidade = models.CharField(max_length=40, blank=True)
    orgao_expedidor = models.CharField(max_length=80, blank=True)
    uf_rg = models.CharField(max_length=2, blank=True)
    data_expedicao = models.DateField(null=True, blank=True)
    titulo_eleitor_numero = models.CharField(max_length=40, blank=True)
    titulo_eleitor_zona = models.CharField(max_length=20, blank=True)
    titulo_eleitor_secao = models.CharField(max_length=20, blank=True)
    titulo_eleitor_uf = models.CharField(max_length=2, blank=True)
    posicao_atual = models.CharField(max_length=120, blank=True)
    cargo_atual = models.CharField(max_length=120, blank=True)
    regime_trabalho = models.CharField(max_length=80, blank=True)
    jornada_trabalho = models.CharField(max_length=80, blank=True)
    classe_funcional = models.CharField(max_length=80, blank=True)
    nivel_funcional = models.CharField(max_length=80, blank=True)
    banco = models.CharField(max_length=120, blank=True)
    agencia = models.CharField(max_length=40, blank=True)
    conta_corrente = models.CharField(max_length=60, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["usuario__pessoa__nome_completo", "usuario__username"]

    def __str__(self):
        return f"{self.matricula_servidor} - {self.usuario}"


class ServidorOcorrenciaAfastamento(models.Model):
    TIPO_CHOICES = (
        ("OCORRENCIA", "Ocorrencia"),
        ("AFASTAMENTO", "Afastamento"),
        ("LICENCA", "Licenca"),
        ("CESSAO", "Cessao"),
    )
    SITUACAO_CHOICES = (
        ("ATIVO", "Ativo"),
        ("ENCERRADO", "Encerrado"),
        ("PROGRAMADO", "Programado"),
    )

    perfil = models.ForeignKey(ServidorPerfil, on_delete=models.CASCADE, related_name="ocorrencias_afastamentos")
    titulo = models.CharField(max_length=160)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default="OCORRENCIA")
    situacao = models.CharField(max_length=20, choices=SITUACAO_CHOICES, default="ATIVO")
    data_inicio = models.DateField(default=timezone.now)
    data_fim = models.DateField(null=True, blank=True)
    descricao = models.TextField(blank=True)

    class Meta:
        ordering = ["-data_inicio", "-id"]

    def __str__(self):
        return self.titulo


class ServidorSetorHistorico(models.Model):
    perfil = models.ForeignKey(ServidorPerfil, on_delete=models.CASCADE, related_name="setores_historico")
    setor = models.ForeignKey("setores.Setor", on_delete=models.CASCADE, related_name="historico_servidores")
    tipo_vinculo = models.CharField(max_length=120, blank=True)
    principal = models.BooleanField(default=False)
    data_inicio = models.DateField(default=timezone.now)
    data_fim = models.DateField(null=True, blank=True)
    observacao = models.TextField(blank=True)

    class Meta:
        ordering = ["-principal", "-data_inicio", "-id"]

    def __str__(self):
        return f"{self.setor} - {self.perfil}"


class ServidorHistoricoFuncional(models.Model):
    perfil = models.ForeignKey(ServidorPerfil, on_delete=models.CASCADE, related_name="historico_funcional")
    titulo = models.CharField(max_length=160)
    tipo_evento = models.CharField(max_length=80, blank=True)
    data_evento = models.DateField(default=timezone.now)
    descricao = models.TextField(blank=True)

    class Meta:
        ordering = ["-data_evento", "-id"]

    def __str__(self):
        return self.titulo


class ServidorFerias(models.Model):
    SITUACAO_CHOICES = (
        ("PROGRAMADA", "Programada"),
        ("EM_ANDAMENTO", "Em andamento"),
        ("GOZADA", "Gozada"),
    )

    perfil = models.ForeignKey(ServidorPerfil, on_delete=models.CASCADE, related_name="ferias")
    exercicio = models.CharField(max_length=9)
    periodo_inicio = models.DateField()
    periodo_fim = models.DateField()
    situacao = models.CharField(max_length=20, choices=SITUACAO_CHOICES, default="PROGRAMADA")
    observacao = models.TextField(blank=True)

    class Meta:
        ordering = ["-periodo_inicio", "-id"]

    def __str__(self):
        return f"Ferias {self.exercicio} - {self.perfil}"


class Aluno(models.Model):
    SITUACAO_CHOICES = (
        ("ATIVO", "Ativo"),
        ("INATIVO", "Inativo"),
    )

    pessoa = models.OneToOneField(Pessoa, on_delete=models.CASCADE, related_name="aluno")
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

