from django.shortcuts import redirect

def index(request):
    return redirect("cursos:cursos_list")
