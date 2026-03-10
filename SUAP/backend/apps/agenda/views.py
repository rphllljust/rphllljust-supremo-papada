from django.shortcuts import redirect


def index(request):
    return redirect("agenda:agenda_list")

