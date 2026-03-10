# file: apps/turmas/views.py
from django.shortcuts import redirect

def index(request):
    return redirect("turmas:turmas_list")
