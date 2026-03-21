from rest_framework import serializers

from apps.integracao_moodle.models import MoodleCategory, MoodleCourse


class LinkedCursoMirrorSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    nome = serializers.CharField(read_only=True)
    sigla = serializers.CharField(read_only=True)
    unidade_nome = serializers.CharField(source="unidade.nome", read_only=True)
    area_curso_nome = serializers.CharField(source="area_curso.descricao", read_only=True)
    eixo_tecnologico = serializers.CharField(read_only=True)
    carga_horaria = serializers.IntegerField(read_only=True)
    moodle_course_id = serializers.IntegerField(read_only=True)
    moodle_shortname = serializers.CharField(read_only=True)


class MoodleCategoryMirrorSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="moodle_category_id", read_only=True)
    name = serializers.CharField(source="nome", read_only=True)
    idnumber = serializers.CharField(read_only=True)
    description = serializers.CharField(source="descricao", read_only=True)
    descriptionformat = serializers.IntegerField(source="descricao_formato", read_only=True)
    parent = serializers.SerializerMethodField()
    sortorder = serializers.IntegerField(read_only=True)
    coursecount = serializers.IntegerField(read_only=True)
    visible = serializers.BooleanField(read_only=True)
    depth = serializers.IntegerField(read_only=True)
    path = serializers.CharField(read_only=True)
    timemodified = serializers.IntegerField(read_only=True, allow_null=True)

    class Meta:
        model = MoodleCategory
        fields = [
            "id",
            "name",
            "idnumber",
            "description",
            "descriptionformat",
            "parent",
            "sortorder",
            "coursecount",
            "visible",
            "depth",
            "path",
            "timemodified",
        ]

    def get_parent(self, obj):
        return obj.parent.moodle_category_id if obj.parent_id else 0


class MoodleCourseMirrorSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="moodle_course_id", read_only=True)
    categoryid = serializers.SerializerMethodField()
    curso_id = serializers.SerializerMethodField()
    curso = LinkedCursoMirrorSerializer(read_only=True)
    categoryname = serializers.CharField(source="categoria.nome", read_only=True)
    displayname = serializers.SerializerMethodField()

    class Meta:
        model = MoodleCourse
        fields = [
            "id",
            "shortname",
            "categoryid",
            "categoryname",
            "fullname",
            "displayname",
            "idnumber",
            "summary",
            "summaryformat",
            "format",
            "visible",
            "startdate",
            "enddate",
            "timecreated",
            "timemodified",
            "enablecompletion",
            "showactivitydates",
            "showcompletionconditions",
            "courseformatoptions",
            "curso_id",
            "curso",
        ]

    def get_categoryid(self, obj):
        return obj.categoria.moodle_category_id if obj.categoria_id else None

    def get_curso_id(self, obj):
        return obj.curso_id

    def get_displayname(self, obj):
        return obj.displayname or obj.fullname
