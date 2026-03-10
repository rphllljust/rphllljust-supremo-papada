from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

from .models import LogAuditoria


@staff_member_required
def log_list(request):
    logs = LogAuditoria.objects.select_related("usuario").all()[:500]
    return render(request, "auditoria/log_list.html", {"logs": logs})
