# Evolucao Compatível - Modulo de Inscricoes

Este documento descreve como evoluir o modulo de processos seletivos sem quebrar o fluxo atual.

## O que foi adicionado (sem remover legado)

- Novos campos opcionais em `PublicacaoInscricao`, `Inscricao`, `DocumentoInscricao` e `ProcessoSeletivo`.
- Novas entidades para crescimento futuro:
  - `CotaProcessoSeletivo`
  - `ChamadaProcessoSeletivo`
  - `ConvocacaoCandidato`
- Novos endpoints API para processos, candidatos, cotas, chamadas e convocacoes.
- Upload de arquivo digital para documentos de inscricao.

## Garantias de compatibilidade

- Nenhum endpoint antigo foi removido.
- Nenhum campo antigo foi removido/renomeado.
- Todos os campos novos foram criados com `default` ou `null/blank` para nao impactar dados existentes.

## Estrategia para mudancas futuras

- Criar toda regra nova como campo/entidade adicional, evitando substituir o legado.
- Versionar regras de cotas por processo e vigencia de edital.
- Executar rollout por etapas: cadastro -> chamadas -> convocacoes -> matricula.
- Validar sempre com `manage.py check` e testes de regressao antes de publicar.

## Endpoints novos

- `GET/POST /api/v1/inscricoes/processos/`
- `GET/PATCH/DELETE /api/v1/inscricoes/processos/{id}/`
- `GET/POST /api/v1/inscricoes/candidatos/`
- `GET/PATCH/DELETE /api/v1/inscricoes/candidatos/{id}/`
- `GET/POST /api/v1/inscricoes/cotas/`
- `GET/PATCH/DELETE /api/v1/inscricoes/cotas/{id}/`
- `GET/POST /api/v1/inscricoes/chamadas/`
- `GET/PATCH/DELETE /api/v1/inscricoes/chamadas/{id}/`
- `GET/POST /api/v1/inscricoes/convocacoes/`
- `GET/PATCH/DELETE /api/v1/inscricoes/convocacoes/{id}/`
