# file: apps/unidades/views.py
from django.shortcuts import redirect

def index(request):
    return redirect("unidades:unidades_list")
