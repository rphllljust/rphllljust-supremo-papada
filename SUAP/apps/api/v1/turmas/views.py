# python
# file: `apps/api/v1/turmas/views.py`
from django.http import JsonResponse


def turmas_list(request):
    return JsonResponse({"message": "Lista de turmas (exemplo)"})


def turmas_detail(request, pk):
    return JsonResponse({"message": f"Detalhe da turma {pk} (exemplo)"})
