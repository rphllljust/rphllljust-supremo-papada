from django import forms

from apps.agenda.models import EventoAgenda


class EventoAgendaForm(forms.ModelForm):
    class Meta:
        model = EventoAgenda
        fields = ["titulo", "descricao", "turma", "inicio", "fim"]

