from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ConsultaCodigoValidacaoForm
from .models import HistoricoEscolarTecnico as HistoricoEscolar
from .services.pdf_export import gerar_pdf_historico
from .services.xml_export import gerar_xml_historico


def exportar_historico_xml(request, pk):
    historico = get_object_or_404(HistoricoEscolar, pk=pk)
    xml_bytes = gerar_xml_historico(historico)

    response = HttpResponse(xml_bytes, content_type="application/xml; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="historico_{historico.pk}.xml"'
    return response


def exportar_historico_pdf(request, pk):
    historico = get_object_or_404(HistoricoEscolar, pk=pk)
    pdf_bytes = gerar_pdf_historico(historico, request)

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="historico_{historico.pk}.pdf"'
    return response


def consulta_publica_historico(request):
    form = ConsultaCodigoValidacaoForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        codigo = form.cleaned_data["codigo_validacao"]
        return redirect("historico_digital:validar_historico_publico", codigo=codigo)

    return render(
        request,
        "historico_digital/consulta_publica.html",
        {"form": form},
    )


def validar_historico_publico(request, codigo):
    historico = get_object_or_404(HistoricoEscolar, codigo_validacao=codigo)

    return render(
        request,
        "historico_digital/resultado_validacao.html",
        {"historico": historico},
    )
