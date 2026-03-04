from django.shortcuts import redirect


def index(request):
    return redirect("notas:notas_list")

