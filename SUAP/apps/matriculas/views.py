# file: apps/matriculas/views.py
from django.shortcuts import redirect

def index(request):
    return redirect("matriculas:matriculas_list")
