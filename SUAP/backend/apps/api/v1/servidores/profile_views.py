from django.db import transaction
from django.utils import timezone
from rest_framework import generics
from rest_framework.exceptions import NotFound

from apps.access.api.permissions import CanAccessModule
from apps.usuarios.models import (
    PerfilUsuario,
    ServidorHistoricoFuncional,
    ServidorPerfil,
    ServidorSetorHistorico,
)

from .profile_serializers import ServidorProfileSerializer


def _build_default_matricula(user):
    username = (user.username or "").strip()
    if username.isdigit():
        return username
    return str(user.id).zfill(7)


@transaction.atomic
def ensure_servidor_profile(usuario, matricula_servidor=None):
    defaults = {
        "matricula_servidor": matricula_servidor or _build_default_matricula(usuario),
        "nome_usual": (usuario.first_name or "").strip() or ((getattr(usuario, "pessoa", None) and usuario.pessoa.nome_completo.split()[0]) if getattr(usuario, "pessoa", None) and usuario.pessoa.nome_completo else usuario.username),
        "email_institucional": usuario.email or "",
        "nao_tem_impressao_digital": False,
        "cargo_atual": usuario.get_tipo_display(),
        "posicao_atual": "Em exercicio",
    }
    perfil, created = ServidorPerfil.objects.get_or_create(usuario=usuario, defaults=defaults)

    if matricula_servidor and perfil.matricula_servidor != matricula_servidor and not perfil.matricula_servidor:
        perfil.matricula_servidor = matricula_servidor
        perfil.save(update_fields=["matricula_servidor", "atualizado_em"])

    if usuario.setor_id and not perfil.setores_historico.exists():
        ServidorSetorHistorico.objects.create(
            perfil=perfil,
            setor=usuario.setor,
            tipo_vinculo="Lotacao principal",
            principal=True,
            data_inicio=timezone.now().date(),
        )

    if created and not perfil.historico_funcional.exists():
        ServidorHistoricoFuncional.objects.create(
            perfil=perfil,
            titulo="Cadastro funcional inicial",
            tipo_evento="CADASTRO",
            data_evento=timezone.now().date(),
            descricao="Perfil funcional criado automaticamente para uso no frontend RH.",
        )

    return perfil


class ServidorProfileByMatriculaApiView(generics.RetrieveAPIView):
    permission_classes = [CanAccessModule]
    module_name = "servidores"
    access_surface = "api"
    access_action = "view"
    serializer_class = ServidorProfileSerializer

    def get_object(self):
        matricula_servidor = self.kwargs["matricula_servidor"].strip()
        queryset = ServidorPerfil.objects.select_related("usuario__pessoa", "usuario__setor")
        perfil = queryset.filter(matricula_servidor=matricula_servidor).first()
        if perfil:
            return perfil

        usuario = self.request.user
        if usuario.tipo == PerfilUsuario.ALUNO:
            raise NotFound("Perfil de servidor nao encontrado.")
        return ensure_servidor_profile(usuario, matricula_servidor=matricula_servidor)


class ServidorProfileByIdApiView(generics.RetrieveAPIView):
    permission_classes = [CanAccessModule]
    module_name = "servidores"
    access_surface = "api"
    access_action = "view"
    serializer_class = ServidorProfileSerializer

    def get_object(self):
        usuario_id = self.kwargs["pk"]
        queryset = ServidorPerfil.objects.select_related("usuario__pessoa", "usuario__setor")
        perfil = queryset.filter(usuario_id=usuario_id).first()
        if perfil:
            return perfil

        if str(self.request.user.id) != str(usuario_id):
            raise NotFound("Perfil de servidor nao encontrado.")
        return ensure_servidor_profile(self.request.user)


class ServidorMyProfileApiView(generics.RetrieveAPIView):
    permission_classes = [CanAccessModule]
    module_name = "servidores"
    access_surface = "api"
    access_action = "view"
    serializer_class = ServidorProfileSerializer

    def get_object(self):
        usuario = self.request.user
        if usuario.tipo == PerfilUsuario.ALUNO:
            raise NotFound("Perfil de servidor nao encontrado.")
        return ensure_servidor_profile(usuario)