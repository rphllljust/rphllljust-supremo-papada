
# python
# file: `apps/api/v1/usuarios/views.py`
from django.http import JsonResponse

def usuario_list(request):
    return JsonResponse({"message": "Lista de usuários (exemplo)"})

def usuario_detail(request, pk):
    return JsonResponse({"message": f"Detalhe do usuário {pk} (exemplo)"})