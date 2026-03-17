from django.db import models

from apps.cursos.models import Curso


class MoodleCategory(models.Model):
	moodle_category_id = models.PositiveIntegerField(unique=True, verbose_name="ID da Categoria no Moodle")
	nome = models.CharField(max_length=255, verbose_name="Nome")
	idnumber = models.CharField(max_length=100, blank=True, default="", verbose_name="ID Number")
	descricao = models.TextField(blank=True, default="", verbose_name="Descrição")
	descricao_formato = models.PositiveSmallIntegerField(default=0, verbose_name="Formato da Descrição")
	parent = models.ForeignKey(
		"self",
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="filhas",
		verbose_name="Categoria Pai",
	)
	sortorder = models.IntegerField(default=0, verbose_name="Ordem")
	coursecount = models.PositiveIntegerField(default=0, verbose_name="Quantidade de Cursos")
	visible = models.BooleanField(default=True, verbose_name="Visível")
	depth = models.PositiveIntegerField(default=0, verbose_name="Profundidade")
	path = models.CharField(max_length=255, blank=True, default="", verbose_name="Path")
	timemodified = models.BigIntegerField(null=True, blank=True, verbose_name="Timestamp de Modificação")
	raw_payload = models.JSONField(default=dict, blank=True, verbose_name="Payload Bruto")
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		verbose_name = "Categoria Moodle"
		verbose_name_plural = "Categorias Moodle"
		ordering = ["nome"]

	def __str__(self):
		return self.nome


class MoodleCourse(models.Model):
	moodle_course_id = models.PositiveIntegerField(unique=True, verbose_name="ID do Curso no Moodle")
	curso = models.OneToOneField(
		Curso,
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="registro_moodle",
		verbose_name="Curso Interno Vinculado",
	)
	categoria = models.ForeignKey(
		MoodleCategory,
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="cursos",
		verbose_name="Categoria Moodle",
	)
	shortname = models.CharField(max_length=100, blank=True, default="", verbose_name="Shortname")
	fullname = models.CharField(max_length=255, verbose_name="Nome Completo")
	displayname = models.CharField(max_length=255, blank=True, default="", verbose_name="Nome de Exibição")
	idnumber = models.CharField(max_length=100, blank=True, default="", verbose_name="ID Number")
	summary = models.TextField(blank=True, default="", verbose_name="Resumo")
	summaryformat = models.PositiveSmallIntegerField(default=0, verbose_name="Formato do Resumo")
	format = models.CharField(max_length=50, blank=True, default="", verbose_name="Formato")
	visible = models.BooleanField(default=True, verbose_name="Visível")
	startdate = models.BigIntegerField(null=True, blank=True, verbose_name="Timestamp de Início")
	enddate = models.BigIntegerField(null=True, blank=True, verbose_name="Timestamp de Fim")
	timecreated = models.BigIntegerField(null=True, blank=True, verbose_name="Timestamp de Criação")
	timemodified = models.BigIntegerField(null=True, blank=True, verbose_name="Timestamp de Modificação")
	enablecompletion = models.BooleanField(default=False, verbose_name="Acompanhamento de Conclusão")
	showactivitydates = models.BooleanField(default=False, verbose_name="Exibir Datas de Atividades")
	showcompletionconditions = models.BooleanField(default=False, verbose_name="Exibir Condições de Conclusão")
	courseformatoptions = models.JSONField(default=list, blank=True, verbose_name="Opções de Formato")
	raw_payload = models.JSONField(default=dict, blank=True, verbose_name="Payload Bruto")
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		verbose_name = "Curso Moodle"
		verbose_name_plural = "Cursos Moodle"
		ordering = ["fullname"]

	def __str__(self):
		return self.fullname


class MoodleGradeSnapshot(models.Model):
	SNAPSHOT_TYPE_CHOICES = (
		("grade_tree", "Árvore de Notas"),
		("gradeitems", "Itens de Nota"),
		("user_grade_items", "Itens de Nota por Usuário"),
		("user_grades_table", "Tabela de Notas por Usuário"),
	)

	snapshot_type = models.CharField(max_length=40, choices=SNAPSHOT_TYPE_CHOICES, verbose_name="Tipo do Snapshot")
	wsfunction = models.CharField(max_length=100, verbose_name="Função Moodle")
	curso = models.ForeignKey(
		MoodleCourse,
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="grade_snapshots",
		verbose_name="Curso Moodle",
	)
	moodle_course_id = models.PositiveIntegerField(null=True, blank=True, verbose_name="ID do Curso no Moodle")
	moodle_user_id = models.PositiveIntegerField(null=True, blank=True, verbose_name="ID do Usuário no Moodle")
	request_payload = models.JSONField(default=dict, blank=True, verbose_name="Payload de Requisição")
	response_payload = models.JSONField(null=True, blank=True, verbose_name="Payload de Resposta")
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		verbose_name = "Snapshot de Notas do Moodle"
		verbose_name_plural = "Snapshots de Notas do Moodle"
		ordering = ["-created_at"]


class MoodleWritebackLog(models.Model):
	STATUS_CHOICES = (
		("success", "Sucesso"),
		("error", "Erro"),
	)

	wsfunction = models.CharField(max_length=100, verbose_name="Função Moodle")
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="success", verbose_name="Status")
	moodle_course_id = models.PositiveIntegerField(null=True, blank=True, verbose_name="ID do Curso no Moodle")
	moodle_assignment_id = models.PositiveIntegerField(null=True, blank=True, verbose_name="ID da Atividade no Moodle")
	moodle_user_id = models.PositiveIntegerField(null=True, blank=True, verbose_name="ID do Usuário no Moodle")
	request_payload = models.JSONField(default=dict, blank=True, verbose_name="Payload de Requisição")
	response_payload = models.JSONField(null=True, blank=True, verbose_name="Payload de Resposta")
	error_message = models.TextField(blank=True, default="", verbose_name="Mensagem de Erro")
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		verbose_name = "Log de Escrita no Moodle"
		verbose_name_plural = "Logs de Escrita no Moodle"
		ordering = ["-created_at"]
