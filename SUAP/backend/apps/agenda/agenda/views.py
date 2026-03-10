from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from apps.agenda.models import EventoAgenda
from .forms import EventoAgendaForm


def agenda_list(request):
    eventos = EventoAgenda.objects.select_related("turma", "turma__curso").all()
    return render(request, "agenda/agenda_list.html", {"eventos": eventos})


def agenda_create(request):
    form = EventoAgendaForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Evento cadastrado com sucesso.")
        return redirect("agenda:agenda_list")
    return render(request, "agenda/agenda_form.html", {"form": form, "page_title": "Novo evento"})


def agenda_update(request, pk):
    evento = get_object_or_404(EventoAgenda, pk=pk)
    form = EventoAgendaForm(request.POST or None, instance=evento)
    if form.is_valid():
        form.save()
        messages.success(request, "Evento atualizado com sucesso.")
        return redirect("agenda:agenda_list")
    return render(request, "agenda/agenda_form.html", {"form": form, "page_title": "Editar evento"})


def agenda_delete(request, pk):
    evento = get_object_or_404(EventoAgenda, pk=pk)
    if request.method == "POST":
        evento.delete()
        messages.success(request, "Evento removido com sucesso.")
        return redirect("agenda:agenda_list")
    return render(request, "agenda/agenda_confirm_delete.html", {"evento": evento})

