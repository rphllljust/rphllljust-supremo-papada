from rest_framework import serializers

from apps.matriculas.models import DocumentoMatricula, DocumentoObrigatorioCurso, Matricula
from apps.turmas.models import Turma
class MatriculaSerializer(serializers.ModelSerializer):
    DOCUMENTOS_OBRIGATORIOS_FALLBACK = {
        "RG",
        "CPF",
        "COMPROVANTE_RESIDENCIA",
    }
    aluno_username = serializers.CharField(source="aluno.username", read_only=True)
    curso_nome = serializers.CharField(source="curso.nome", read_only=True)
    turma_nome = serializers.CharField(source="turma.nome", read_only=True)
    professor_nome = serializers.SerializerMethodField(read_only=True)
    periodo = serializers.SerializerMethodField(read_only=True)
    aluno_nome = serializers.SerializerMethodField(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    tipo_matricula_display = serializers.CharField(source="get_tipo_matricula_display", read_only=True)
    turno_display = serializers.CharField(source="get_turno_display", read_only=True)
    situacao_academica = serializers.SerializerMethodField(read_only=True)

    # T107: versioning para controle de concorrência otimista
    version = serializers.IntegerField(required=False, default=0)

    class Meta:
        model = Matricula
        fields = [
            "id",
            "numero_matricula",
            "aluno",
            "aluno_nome",
            "aluno_username",
            "curso",
            "curso_nome",
            "turma",
            "turma_nome",
            "professor_nome",
            "periodo",
            "data_matricula",
            "status",
            "status_display",
            "tipo_matricula",
            "tipo_matricula_display",
            "turno",
            "turno_display",
            "situacao_academica",
            "version",
        ]
        read_only_fields = ["data_matricula"]

    def validate_aluno(self, aluno):
        # T035: aluno inativo não pode ser matriculado sem reativação prévia
        aluno_obj = getattr(getattr(aluno, "pessoa", None), "aluno", None)
        if aluno_obj and aluno_obj.situacao == "INATIVO":
            raise serializers.ValidationError(
                "Aluno inativo nao pode ser matriculado. Reative o cadastro antes de prosseguir."
            )
        return aluno

    def validate_turma(self, turma):
        # T024: validar capacidade máxima da turma
        capacidade = getattr(turma, "capacidade_maxima", None)
        if capacidade is not None:
            vagas_ocupadas = Matricula.objects.filter(
                turma=turma, status="ATIVA"
            ).count()
            # Desconta a própria matrícula em caso de edição
            instance = getattr(self, "instance", None)
            if instance and instance.turma_id == turma.pk and instance.status == "ATIVA":
                vagas_ocupadas -= 1
            if vagas_ocupadas >= capacidade:
                raise serializers.ValidationError(
                    f"Turma sem vagas disponíveis. Capacidade maxima: {capacidade}."
                )
        return turma

    def validate(self, attrs):
        attrs = super().validate(attrs)

        # Verificação de versão para edições (não para criação)
        instance = getattr(self, "instance", None)
        if instance is not None:
            client_version = attrs.get("version")
            if client_version is not None and client_version != instance.version:
                raise serializers.ValidationError(
                    {
                        "version": (
                            "Conflito de edição: este registro foi alterado por outro usuário. "
                            "Recarregue e tente novamente."
                        )
                    }
                )

        turma = attrs.get("turma") or (self.instance.turma if self.instance else None)
        aluno = attrs.get("aluno") or (self.instance.aluno if self.instance else None)
        curso = attrs.get("curso") or (self.instance.curso if self.instance else None)
        status = attrs.get("status") or (self.instance.status if self.instance else "ATIVA")

        # T049: bloquear vínculo de aluno remoto com turma presencial
        if turma and aluno:
            modalidade_turma = getattr(turma, "modalidade", None)
            modalidade_aluno = self._modalidade_aluno(aluno)
            if modalidade_turma and modalidade_aluno and modalidade_turma != modalidade_aluno:
                raise serializers.ValidationError(
                    {
                        "turma": (
                            f"Incompatibilidade de modalidade: aluno '{modalidade_aluno}' "
                            f"nao pode ser vinculado a turma '{modalidade_turma}'."
                        )
                    }
                )

        # Regra de negócio: aluno não pode ter matrícula ATIVA em outro curso.
        if aluno and curso and status == "ATIVA":
            ativos_outro_curso = Matricula.objects.filter(aluno=aluno, status="ATIVA").exclude(curso=curso)
            if self.instance:
                ativos_outro_curso = ativos_outro_curso.exclude(pk=self.instance.pk)
            if ativos_outro_curso.exists():
                raise serializers.ValidationError(
                    {
                        "aluno": (
                            "Aluno ja possui matricula ativa em outro curso. "
                            "Finalize, cancele ou tranque a matricula ativa antes de continuar."
                        )
                    }
                )

        # Regra de negócio: matrícula ATIVA exige documentos obrigatórios validados.
        if status == "ATIVA":
            matricula_ref = self.instance
            if matricula_ref is None:
                raise serializers.ValidationError(
                    {
                        "status": (
                            "Nao e possivel criar matricula diretamente como ATIVA sem conferência documental. "
                            "Cadastre como TRANCADA e ative após validar os documentos obrigatorios."
                        )
                    }
                )

            docs_validos = set(
                DocumentoMatricula.objects.filter(
                    matricula=matricula_ref,
                    status="VALIDADO",
                ).values_list("tipo_documento", flat=True)
            )
            docs_obrigatorios = self._documentos_obrigatorios_por_curso(matricula_ref.curso)
            faltantes = sorted(docs_obrigatorios - docs_validos)
            if faltantes:
                raise serializers.ValidationError(
                    {
                        "status": (
                            "Nao e possivel manter a matricula ATIVA sem documentos obrigatorios validados. "
                            f"Faltando: {', '.join(faltantes)}."
                        )
                    }
                )

        if turma and curso:
            tipo_curso = (getattr(curso, "tipo_curso", "") or "").strip().lower()
            modalidade_turma = (getattr(turma, "modalidade", "") or "").strip().upper()
            unidade_codigo = (getattr(getattr(curso, "unidade", None), "codigo", "") or "").strip().lower()

            if tipo_curso == "itinerante" and modalidade_turma != "ITINERANTE":
                raise serializers.ValidationError(
                    {"turma": "Curso itinerante deve ser vinculado somente a turmas com modalidade ITINERANTE."}
                )
            if tipo_curso == "itinerante" and not getattr(turma, "polo_id", None):
                raise serializers.ValidationError(
                    {"turma": "Turma itinerante deve possuir polo/localidade obrigatoria."}
                )
            if modalidade_turma == "REMOTO" and unidade_codigo != "sede":
                raise serializers.ValidationError(
                    {"turma": "Turmas remotas devem estar vinculadas a cursos da unidade Sede."}
                )

        return attrs

    def _documentos_obrigatorios_por_curso(self, curso):
        documentos = set(
            DocumentoObrigatorioCurso.objects.filter(
                curso=curso,
                ativo=True,
            ).values_list("tipo_documento", flat=True)
        )
        return documentos or set(self.DOCUMENTOS_OBRIGATORIOS_FALLBACK)

    @staticmethod
    def _modalidade_aluno(aluno):
        """Retorna a modalidade do curso da matrícula mais recente ativa do aluno."""
        ultima = (
            Matricula.objects.filter(aluno=aluno, status="ATIVA")
            .select_related("turma")
            .order_by("-data_matricula")
            .first()
        )
        if ultima:
            return getattr(ultima.turma, "modalidade", None)
        return None

    def get_aluno_nome(self, obj):
        if getattr(obj.aluno, "pessoa", None) and obj.aluno.pessoa.nome_completo:
            return obj.aluno.pessoa.nome_completo

        full_name = obj.aluno.get_full_name().strip()
        return full_name or obj.aluno.username

    def get_professor_nome(self, obj):
        professor = getattr(obj.turma, "professor_responsavel", None)
        if not professor:
            return None
        full_name = professor.get_full_name().strip()
        return full_name or professor.username

    def get_periodo(self, obj):
        diario = obj.turma.diarios.order_by("-id").first()
        if diario and diario.periodo:
            return diario.periodo
        return str(obj.turma.ano_letivo)

    def get_situacao_academica(self, obj):
        consolidacao = getattr(obj, "consolidacao", None)
        if consolidacao:
            return consolidacao.get_situacao_display()
        return obj.get_status_display()
