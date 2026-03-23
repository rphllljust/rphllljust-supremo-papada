# Historico Escolar Digital MEC (v1.05)

Este modulo amplia o legado do SUAP sem alterar estruturas existentes, adicionando a emissao digital institucional de historicos com:

- XML academico em namespace MEC
- validacao estrutural por XSD
- assinatura XMLDSig (quando habilitada)
- PDF institucional com chave de autenticacao
- QR Code para consulta de autenticidade
- segunda via com rastreabilidade ao documento original
- trilha de auditoria

## Arquitetura Aplicada

Camadas adicionadas:

- `apps.documentos.models.HistoricoEscolarDigital`
- `apps.documentos.services.*`
- `apps.api.v1.historicos_digitais.*`
- `schemas/mec/historico/*.xsd`

Nao houve remocao de tabelas, renomeacao de colunas nativas ou alteracao destrutiva.

## XSD Utilizado

Pasta de schemas:

- `schemas/mec/historico/documentoHistoricoEscolar_v1.05.xsd`
- `schemas/mec/historico/leiauteHistoricoEscolar_v1.05.xsd`

Namespaces:

- `https://portal.mec.gov.br/diplomadigital/arquivos-em-xsd`
- `https://www.w3.org/2000/09/xmldsig#`

## Variaveis de Ambiente

Adicionar no backend:

```env
DOCUMENTOS_MEC_XSD_ROOT=/app/schemas/mec/historico
DOCUMENTOS_VALIDATION_BASE_URL=https://seu-dominio/api/v1/historicos-digitais/validar-publico/
DOCUMENTOS_XMLDSIG_ENABLED=false
DOCUMENTOS_XMLDSIG_PRIVATE_KEY_PATH=/app/certs/private_key.pem
DOCUMENTOS_XMLDSIG_CERT_PATH=/app/certs/certificate.pem
DOCUMENTOS_XSD_STRICT_VALIDATION=false
```

## Endpoints

Base: `/api/v1/historicos-digitais/`

- `GET /` lista documentos digitais
- `GET /{id}/` detalha um documento digital
- `POST /emitir/{historico_id}/` emite documento digital
- `POST /{id}/revogar/` revoga documento
- `GET /validar-publico/?chave=...` valida autenticidade por chave/QR

Payload de emissao:

```json
{
  "tipo_documento": "PARCIAL",
  "assinar_xml": false,
  "forcar_reemissao": false,
  "referencia_original_id": null
}
```

Tipos aceitos:

- `PARCIAL`
- `FINAL`
- `SEGUNDA_VIA_NATO_FISICO`

## Regras de Negocio Implementadas

- apenas `SECRETARIA` e `ADMIN` podem emitir/revogar
- historico final exige matricula concluida e consolidacao aprovada
- segunda via exige vinculo a documento digital original
- cada emissao gera:
  - numero unico
  - versao
  - hash SHA-256
  - chave de autenticacao
  - XML
  - metadados de validacao e assinatura
  - PDF institucional
- todas as emissoes/revogacoes geram `LogAuditoria`

## Testes Automatizados

Arquivo:

- `apps/api/v1/historicos_digitais/tests.py`

Casos cobertos:

- emissao por secretaria
- bloqueio de emissao por professor
- validacao publica por chave
- bloqueio de historico final com inconsistencia academica
