from xml.etree import ElementTree as ET


def _add_text(parent, tag, value):
    node = ET.SubElement(parent, tag)
    node.text = "" if value is None else str(value)
    return node


def gerar_xml_historico(historico):
    root = ET.Element("HistoricoEscolarDigital")
    root.set("versao", str(getattr(historico, "versao", "1.05")))

    aluno = getattr(historico, "aluno", None)
    pessoa = getattr(aluno, "pessoa", None) if aluno else None
    curso = getattr(historico, "curso", None)
    instituicao = getattr(historico, "instituicao", None)

    dados_gerais = ET.SubElement(root, "DadosGerais")
    _add_text(dados_gerais, "CodigoValidacao", getattr(historico, "codigo_validacao", ""))
    _add_text(dados_gerais, "Ambiente", getattr(historico, "ambiente", ""))
    _add_text(dados_gerais, "DataEmissao", getattr(historico, "data_emissao_historico", ""))
    _add_text(dados_gerais, "HoraEmissao", getattr(historico, "hora_emissao_historico", ""))
    _add_text(dados_gerais, "FormaAcesso", getattr(historico, "forma_acesso", ""))

    dados_aluno = ET.SubElement(root, "Aluno")
    _add_text(
        dados_aluno,
        "Nome",
        getattr(aluno, "nome", None)
        or (getattr(pessoa, "nome_completo", None) if pessoa else None)
        or "",
    )
    _add_text(
        dados_aluno,
        "CPF",
        getattr(aluno, "cpf", None)
        or (getattr(pessoa, "cpf", None) if pessoa else None)
        or "",
    )
    _add_text(dados_aluno, "DataIngresso", getattr(historico, "data_ingresso", ""))

    dados_curso = ET.SubElement(root, "Curso")
    _add_text(dados_curso, "Nome", getattr(curso, "nome", ""))
    _add_text(dados_curso, "CargaHorariaCurso", getattr(historico, "carga_horaria_curso", ""))
    _add_text(dados_curso, "CargaHorariaIntegralizada", getattr(historico, "carga_horaria_integralizada", ""))

    dados_instituicao = ET.SubElement(root, "Instituicao")
    _add_text(dados_instituicao, "Nome", getattr(instituicao, "nome", ""))

    situacao_final = ET.SubElement(root, "SituacaoFinal")
    _add_text(situacao_final, "DataConclusaoCurso", getattr(historico, "data_conclusao_curso", ""))
    _add_text(situacao_final, "DataColacaoGrau", getattr(historico, "data_colacao_grau", ""))
    _add_text(situacao_final, "DataExpedicaoDiploma", getattr(historico, "data_expedicao_diploma", ""))

    _add_text(root, "InformacoesAdicionais", getattr(historico, "informacoes_adicionais", ""))

    xml_bytes = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    return xml_bytes
