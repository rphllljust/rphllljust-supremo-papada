from django.contrib import admin

from .models import (
    Candidato,
    DocumentoInscricao,
    Inscricao,
    ProcessoSeletivo,
    PublicacaoInscricao,
    RecursoInscricao,
)

admin.site.register(PublicacaoInscricao)
admin.site.register(Inscricao)
admin.site.register(DocumentoInscricao)
admin.site.register(ProcessoSeletivo)
admin.site.register(Candidato)
admin.site.register(RecursoInscricao)
