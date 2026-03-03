# python
# file: apps/usuarios/views.py
from django.shortcuts import redirect


def index(request):
    return redirect("usuarios:alunos_list")
