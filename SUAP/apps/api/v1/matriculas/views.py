# python
# file: `apps/api/v1/matriculas/views.py`
from django.http import JsonResponse


def matriculas_list(request):
    return JsonResponse({"message": "Lista de matrículas (exemplo)"})


def matriculas_detail(request, pk):
    return JsonResponse({"message": f"Detalhe da matrícula {pk} (exemplo)"})
