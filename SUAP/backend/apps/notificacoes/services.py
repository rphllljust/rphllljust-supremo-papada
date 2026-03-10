from django.utils import timezone

from .models import Notificacao, NotificacaoCategoria, PreferenciaNotificacao


DEFAULT_NOTIFICATION_CATEGORIES = [
    {
        "slug": "alerta-dispositivo",
        "titulo": "Alerta de dispositivo desconhecido",
        "descricao": "Notificações de acesso a partir de dispositivo ou IP não reconhecido.",
        "icone": "shield-alert",
        "ordem": 10,
    },
    {
        "slug": "processos",
        "titulo": "Processos e requerimentos",
        "descricao": "Atualizações sobre abertura, tramitação e conclusão de processos.",
        "icone": "file-stack",
        "ordem": 20,
    },
    {
        "slug": "documentos",
        "titulo": "Documentos acadêmicos",
        "descricao": "Emissão, disponibilidade e andamento de documentos institucionais.",
        "icone": "file-text",
        "ordem": 30,
    },
    {
        "slug": "sistema",
        "titulo": "Sistema e segurança",
        "descricao": "Avisos gerais do sistema, autenticação e manutenção.",
        "icone": "bell-ring",
        "ordem": 40,
    },
    {
        "slug": "rh",
        "titulo": "Gestão de Pessoas",
        "descricao": "Comunicados funcionais, férias, afastamentos e atualizações cadastrais.",
        "icone": "users",
        "ordem": 50,
    },
]


def ensure_default_categories():
    for payload in DEFAULT_NOTIFICATION_CATEGORIES:
        NotificacaoCategoria.objects.update_or_create(
            slug=payload["slug"],
            defaults=payload,
        )


def ensure_user_preferences(usuario):
    ensure_default_categories()
    categorias = NotificacaoCategoria.objects.filter(ativa=True)
    for categoria in categorias:
        PreferenciaNotificacao.objects.get_or_create(
            usuario=usuario,
            categoria=categoria,
            defaults={"via_suap": True, "via_email": True},
        )


def create_notification(*, usuario, categoria_slug, titulo, mensagem, resumo="", tipo="INFO", link="", link_label="", via_suap=True, via_email=False, data_evento=None, metadados=None):
    ensure_user_preferences(usuario)
    categoria = NotificacaoCategoria.objects.get(slug=categoria_slug)
    preferencia = PreferenciaNotificacao.objects.get(usuario=usuario, categoria=categoria)
    return Notificacao.objects.create(
        usuario=usuario,
        categoria=categoria,
        titulo=titulo,
        resumo=resumo,
        mensagem=mensagem,
        tipo=tipo,
        link=link,
        link_label=link_label,
        via_suap=via_suap and preferencia.via_suap,
        via_email=via_email and preferencia.via_email,
        data_evento=data_evento or timezone.now(),
        metadados=metadados or {},
    )
