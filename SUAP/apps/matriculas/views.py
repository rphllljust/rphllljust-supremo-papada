# file: apps/matriculas/views.py
from django.http import HttpResponse

def index(request):
    return HttpResponse("Página inicial de matrículas")