from django.contrib import admin

from .models import AcompanhamentoEstagio, Convenio, Estagio, TermoCompromisso

admin.site.register(Convenio)
admin.site.register(Estagio)
admin.site.register(TermoCompromisso)
admin.site.register(AcompanhamentoEstagio)
