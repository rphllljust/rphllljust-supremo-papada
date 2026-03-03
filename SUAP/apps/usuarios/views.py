# python
# file: apps/usuarios/views.py
from django.http import HttpResponse

def index(request):
    return HttpResponse("Página inicial de usuários")