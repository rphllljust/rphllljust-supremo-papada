from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.access.api.permissions import CanAccessModule
from apps.api.v1.pagination import StandardResultsSetPagination
from apps.notificacoes.models import Notificacao, PreferenciaNotificacao
from apps.notificacoes.services import ensure_user_preferences

from .serializers import NotificacaoSerializer, PreferenciaNotificacaoSerializer


def _parse_bool(value):
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "sim", "yes", "on"}:
        return True
    if normalized in {"0", "false", "nao", "não", "no", "off"}:
        return False
    return None


class NotificationFilterMixin:
    def get_notification_queryset(self):
        ensure_user_preferences(self.request.user)
        queryset = Notificacao.objects.select_related("categoria").filter(usuario=self.request.user, ocultada_em__isnull=True)
        search = self.request.query_params.get("search", "").strip()
        categoria = self.request.query_params.get("categoria", "").strip()
        unread = _parse_bool(self.request.query_params.get("unread"))
        via_suap = _parse_bool(self.request.query_params.get("via_suap"))
        via_email = _parse_bool(self.request.query_params.get("via_email"))
        ano = self.request.query_params.get("ano", "").strip()
        mes = self.request.query_params.get("mes", "").strip()

        if search:
            queryset = queryset.filter(
                Q(titulo__icontains=search)
                | Q(resumo__icontains=search)
                | Q(mensagem__icontains=search)
                | Q(categoria__titulo__icontains=search)
            )

        if categoria:
            queryset = queryset.filter(Q(categoria__slug=categoria) | Q(categoria_id=categoria))

        if unread is True:
            queryset = queryset.filter(lida_em__isnull=True)
        elif unread is False:
            queryset = queryset.filter(lida_em__isnull=False)

        if via_suap is not None:
            queryset = queryset.filter(via_suap=via_suap)

        if via_email is not None:
            queryset = queryset.filter(via_email=via_email)

        if ano.isdigit():
            queryset = queryset.filter(data_evento__year=int(ano))

        if mes.isdigit():
            queryset = queryset.filter(data_evento__month=int(mes))

        return queryset.order_by("lida_em", "-data_evento", "-id").distinct()


class NotificacaoListApiView(NotificationFilterMixin, generics.ListAPIView):
    permission_classes = [CanAccessModule]
    module_name = "notificacoes"
    access_surface = "api"
    access_action = "view"
    serializer_class = NotificacaoSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return self.get_notification_queryset()


class NotificacaoDetailApiView(generics.RetrieveAPIView):
    permission_classes = [CanAccessModule]
    module_name = "notificacoes"
    access_surface = "api"
    access_action = "view"
    serializer_class = NotificacaoSerializer

    def get_queryset(self):
        ensure_user_preferences(self.request.user)
        return Notificacao.objects.select_related("categoria").filter(usuario=self.request.user, ocultada_em__isnull=True)


class NotificacaoMarcarLidaApiView(APIView):
    permission_classes = [CanAccessModule]
    module_name = "notificacoes"
    access_surface = "api"
    access_action = "view"

    def post(self, request, pk):
        ensure_user_preferences(request.user)
        notificacao = generics.get_object_or_404(Notificacao, pk=pk, usuario=request.user, ocultada_em__isnull=True)
        lida = _parse_bool(request.data.get("lida"))
        notificacao.lida_em = timezone.now() if lida is not False else None
        notificacao.save(update_fields=["lida_em", "atualizado_em"])
        return Response(NotificacaoSerializer(notificacao).data)


class NotificacaoOcultarApiView(APIView):
    permission_classes = [CanAccessModule]
    module_name = "notificacoes"
    access_surface = "api"
    access_action = "view"

    def post(self, request, pk):
        ensure_user_preferences(request.user)
        notificacao = generics.get_object_or_404(Notificacao, pk=pk, usuario=request.user, ocultada_em__isnull=True)
        notificacao.ocultada_em = timezone.now()
        notificacao.save(update_fields=["ocultada_em", "atualizado_em"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class NotificacaoMarcarTodasLidasApiView(NotificationFilterMixin, APIView):
    permission_classes = [CanAccessModule]
    module_name = "notificacoes"
    access_surface = "api"
    access_action = "view"

    def post(self, request):
        queryset = self.get_notification_queryset().filter(lida_em__isnull=True)
        updated = queryset.update(lida_em=timezone.now(), atualizado_em=timezone.now())
        return Response({"updated": updated})


class PreferenciaNotificacaoListApiView(generics.ListAPIView):
    permission_classes = [CanAccessModule]
    module_name = "notificacoes"
    access_surface = "api"
    access_action = "view"
    serializer_class = PreferenciaNotificacaoSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        ensure_user_preferences(self.request.user)
        queryset = PreferenciaNotificacao.objects.select_related("categoria").filter(usuario=self.request.user)
        search = self.request.query_params.get("search", "").strip()
        via_suap = _parse_bool(self.request.query_params.get("via_suap"))
        via_email = _parse_bool(self.request.query_params.get("via_email"))
        ano = self.request.query_params.get("ano", "").strip()

        if search:
            queryset = queryset.filter(
                Q(categoria__titulo__icontains=search)
                | Q(categoria__descricao__icontains=search)
                | Q(categoria__slug__icontains=search)
            )

        if via_suap is not None:
            queryset = queryset.filter(via_suap=via_suap)

        if via_email is not None:
            queryset = queryset.filter(via_email=via_email)

        if ano.isdigit():
            queryset = queryset.filter(atualizado_em__year=int(ano))

        return queryset.order_by("categoria__ordem", "categoria__titulo")


class PreferenciaNotificacaoUpdateApiView(generics.UpdateAPIView):
    permission_classes = [CanAccessModule]
    module_name = "notificacoes"
    access_surface = "api"
    access_action = "view"
    serializer_class = PreferenciaNotificacaoSerializer

    def get_queryset(self):
        ensure_user_preferences(self.request.user)
        return PreferenciaNotificacao.objects.select_related("categoria").filter(usuario=self.request.user)


class PreferenciaBulkSerializer(serializers.Serializer):
    canal = serializers.ChoiceField(choices=("via_suap", "via_email"))
    enabled = serializers.BooleanField()
    ids = serializers.ListField(child=serializers.IntegerField(min_value=1), required=False, allow_empty=True)


class PreferenciaNotificacaoBulkUpdateApiView(APIView):
    permission_classes = [CanAccessModule]
    module_name = "notificacoes"
    access_surface = "api"
    access_action = "view"

    def post(self, request):
        ensure_user_preferences(request.user)
        serializer = PreferenciaBulkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        channel = serializer.validated_data["canal"]
        enabled = serializer.validated_data["enabled"]
        ids = serializer.validated_data.get("ids") or []

        queryset = PreferenciaNotificacao.objects.filter(usuario=request.user)
        if ids:
            queryset = queryset.filter(id__in=ids)

        updated = queryset.update(**{channel: enabled, "atualizado_em": timezone.now()})
        return Response({"updated": updated})
