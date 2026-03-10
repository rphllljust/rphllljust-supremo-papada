from django.shortcuts import redirect


def index(request):
    return redirect("frequencia:frequencia_list")

