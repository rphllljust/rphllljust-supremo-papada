# Caso de uso completo - aluno teste Joao Pedro da Silva

## 1) Objetivo
Este documento descreve um fluxo completo, realista e implementavel para jornada academica de um aluno em sistema escolar institucional, cobrindo:
- pre-inscricao e inscricao
- analise documental e processo seletivo
- matricula e vida academica
- acompanhamento pedagogico e estagio
- conclusao, historico final, registro de diploma e entrega

Escopo pensado para operacao de Secretaria Escolar, Registro Academico, Coordenacao Pedagogica e Diplomacao.

---

## 2) Identidade do aluno teste
### 2.1 Dados solicitados no roteiro funcional
- Nome: Joao Pedro da Silva
- CPF (roteiro): 000.111.222-33
- Data de nascimento: 15/03/2004
- E-mail: joao.teste@exemplo.com
- Telefone: (69) 99999-0000
- Endereco: Rua das Acacias, 245, Bairro Nova Esperanca, Porto Velho/RO, CEP 76812-345
- RG: 1234567 SSP/RO
- Mae: Maria Aparecida da Silva
- Pai: Carlos Roberto da Silva

### 2.2 Regra tecnica importante
No backend atual, autenticacao por CPF usa validacao de digitos verificadores. Por isso o seed operacional usa:
- CPF valido no sistema: `000.111.222-85` (`00011122285`)
- CPF solicitado no roteiro: mantido apenas como referencia documental/narrativa.

---

## 3) Resumo visual do fluxo
```text
Portal/Candidato
  -> Pre-inscricao e inscricao
  -> Upload documental

Secretaria
  -> Triagem e validacao documental
  -> Homologacao e convocacao
  -> Fluxo P01 de matricula

Academico (docente + coordenacao)
  -> Diario, frequencia, notas, consolidacao
  -> Pedagogia, dependencia, aproveitamento
  -> Estagio e encerramento

Registro/Documentos
  -> Conselho e ata final
  -> Historico final
  -> Certificado/Diploma
  -> Registro institucional + codigo de validacao

Secretaria (encerramento)
  -> Disponibilizacao para retirada
  -> Entrega e trilha administrativa completa
```

---

## 4) Fluxo numerado ponta a ponta
1. Publicacao do edital de ingresso.
2. Cadastro inicial do candidato no portal e criacao da inscricao.
3. Upload de documentos obrigatorios (RG, CPF, comprovante, historico, foto).
4. Triagem da secretaria e validacao documental.
5. Homologacao da inscricao.
6. Processo seletivo (analise curricular), classificacao e convocacao.
7. Conversao para matricula institucional (P01).
8. Enturmacao e emissao de comprovante de matricula.
9. Abertura de diarios de classe e inicio da execucao letiva.
10. Lancamento de frequencia e notas por etapa avaliativa.
11. Consolidacao academica (media/frequencia/situacao).
12. Registro de dependencia e posterior cumprimento.
13. Registro de aproveitamento de estudos.
14. Acompanhamento pedagogico (plano de recuperacao e conclusao).
15. Registro completo de estagio (convenio, termo, acompanhamento, conclusao).
16. Conselho de classe e publicacao da ata de resultado.
17. Fluxo P02 para historico escolar final e entrega.
18. Emissao de historico digital com codigo de validacao.
19. Processo administrativo de diplomacao (conferencia -> validacao -> registro -> arquivamento).
20. Emissao e registro do diploma, disponibilidade e entrega ao aluno.

---

## 5) Estados e transicoes por modulo
### 5.1 Inscricoes
- PublicacaoInscricao.status: `RASCUNHO -> PUBLICADO -> ENCERRADO`
- Inscricao.status: `PENDENTE -> VALIDADA | INDEFERIDA`
- Inscricao.status_candidato: `INSCRITO -> HOMOLOGADO -> CLASSIFICADO -> CONVOCADO -> MATRICULADO`
- Candidato.situacao: `CONVOCADO`, `MATRICULADO`, `LISTA_ESPERA`, `DESISTENTE`, etc.

### 5.2 Fluxo de matricula (P01)
- `REQUERIMENTO_RECEBIDO`
- `DOCUMENTOS_CONFERIDOS`
- `PENDENCIA_ABERTA` (quando houver)
- `REQUISITOS_VALIDADOS`
- `MATRICULA_REGISTRADA`
- `ALUNO_ENTURMADO`
- `COMPROVANTE_EMITIDO`
- `ARQUIVADO`

### 5.3 Matricula
- Matricula.status: `ATIVA`, `TRANCADA`, `CANCELADA`, `CONCLUIDA`
- Transicoes validas:
  - `ATIVA -> TRANCADA | CANCELADA | CONCLUIDA`
  - `TRANCADA -> ATIVA | CANCELADA`

### 5.4 Diario e execucao letiva
- DiarioAcademico.status: `ABERTO -> FECHADO` (ou `REVISAO`)

### 5.5 Consolidacao academica
- ConsolidacaoAcademica.situacao:
  - `PENDENTE`
  - `APROVADO`
  - `REPROVADO_NOTA`
  - `REPROVADO_FREQUENCIA`
  - `REPROVADO_AMBOS`
  - `EM_RECUPERACAO`

### 5.6 Pedagogia e estagio
- AtendimentoPedagogico.status: risco/evasao/recuperacao/psicopedagogico/concluido
- Estagio.status: `PREVISTO`, `EM_ANDAMENTO`, `CONCLUIDO`, `CANCELADO`, `INTERROMPIDO`

### 5.7 Diplomacao
- CertificadoDiploma.status: `PENDENTE -> EMITIDO -> ENTREGUE`
- Status operacional complementar (negocio):
  - diploma em preparacao
  - diploma registrado
  - diploma disponivel para retirada
  - diploma entregue

---

## 6) Tabela consolidada de status do processo
| Fase | Status de negocio | Estado tecnico principal | Setor responsavel |
|---|---|---|---|
| Pre-inscricao | Rascunho | cadastro inicial | Aluno |
| Inscricao enviada | Em analise | Inscricao `PENDENTE` | Secretaria |
| Validacao documental | Deferida | Inscricao `VALIDADA` | Secretaria |
| Processo seletivo | Aprovado para matricula | Candidato `CONVOCADO` | Comissao/Secretaria |
| Matricula | Matriculado | Matricula `ATIVA` | Secretaria |
| Vida academica | Cursando | Diario/Notas/Frequencia ativos | Docente/Coord |
| Acompanhamento | Recuperacao/dependencia (quando houver) | registros pedagogicos/academicos | Pedagogia/Coord |
| Conclusao | Concluinte -> Formado | Consolidacao `APROVADO`, Matricula `CONCLUIDA` | Conselho/Registro |
| Diplomacao | Emissao e registro | Certificado/Diploma + processo administrativo | Secretaria/Registro |
| Encerramento | Diploma entregue | Certificado `ENTREGUE` | Secretaria |

---

## 7) Exemplo de dados por modulo
### 7.1 Secretaria / inscricao
- Edital: `EDT-2026-JPS-01`
- Inscricao: `INS-2026-0001`
- Curso escolhido: Tecnico em Administracao - CASE-JPS-2026

### 7.2 Matricula
- Numero de matricula: `2026-TAD-000001`
- Turma: `TAD-2026-JPS-A`
- Turno: NOITE

### 7.3 Academico
- Media final consolidada: `8.21`
- Frequencia final: `90.00%`
- Situacao: `APROVADO`

### 7.4 Estagio
- Status: `CONCLUIDO`
- Carga horaria: `200h`

### 7.5 Documentos finais
- Ata de resultado: `ATA-2026-0001`
- Historico final: `DOC-2026-0002`
- Registro diploma: `DIP-2026-0001`

---

## 8) Exemplo dos documentos gerados
- Declaracao de matricula (protocolo)
- Historico escolar final (protocolo)
- Historico escolar digital (xml + status assinado + codigo de validacao)
- Ata de resultado
- Ata escolar de conclusao
- Registro de diploma (numero do diploma + codigo de verificacao)

Campos essenciais no diploma:
- nome completo, data/local de nascimento, CPF, RG
- nome do curso/habilitacao, carga horaria, periodo
- media final
- unidade e municipio/UF
- diretor, secretario escolar, data de emissao
- numero do diploma e codigo de verificacao

---

## 9) Exemplo de registros internos da secretaria (trilha)
| Ordem | Registro | Responsavel |
|---|---|---|
| 1 | Conferencia inicial de diplomacao | Secretaria |
| 2 | Validacao academica dos requisitos | Coordenacao/Registro |
| 3 | Registro institucional (livro/folha/termo) | Registro Academico |
| 4 | Arquivamento do processo de diploma | Secretaria |
| 5 | Entrega do diploma ao aluno | Secretaria |

---

## 10) Telas/modulos do sistema envolvidos
### Front-end (React)
- `/inscricoes`, `/inscricoes/nova`
- `/matriculas`
- `/turmas`
- `/diarios`
- `/notas`
- `/frequencia`
- `/pedagogia`
- `/estagio`
- `/documentos/historicos`
- `/documentos/historicos-digitais`
- `/processos`
- `/arquivo`

### Back-end (Django)
- `apps.inscricoes`
- `apps.matriculas`
- `apps.turmas`
- `apps.notas`
- `apps.frequencia`
- `apps.pedagogia`
- `apps.estagio`
- `apps.documentos`
- `apps.processos`
- `apps.arquivo`

---

## 11) Regras de negocio e validacoes obrigatorias
- CPF de autenticacao deve ser valido quando houver login por CPF.
- Matricula so deve concluir apos consolidacao academica apta.
- Conclusao exige, no minimo:
  - carga horaria integralizada
  - media/frequencia em conformidade
  - estagio (quando exigido) concluido
  - documentacao regular
- Emissao de historico e diploma exige trilha administrativa auditavel.
- Documento final deve ter numeracao unica e rastreabilidade de emissao/entrega.

---

## 12) Mapeamento tecnico de status solicitados no roteiro
| Status do roteiro | Status tecnico principal |
|---|---|
| rascunho | `PublicacaoInscricao.RASCUNHO` |
| enviada | `Inscricao.PENDENTE` |
| em analise | documentos em `PENDENTE/VALIDO/INVALIDO` |
| deferida | `Inscricao.VALIDADA` |
| indeferida | `Inscricao.INDEFERIDA` |
| aprovado para matricula | `Candidato.CONVOCADO` |
| cursando | `Matricula.ATIVA` |
| trancado | `Matricula.TRANCADA` |
| transferido | `Transferencia.CONCLUIDA` |
| desistente | `Candidato.DESISTENTE` ou matricula cancelada |
| reprovado | `Consolidacao.REPROVADO_*` |
| aprovado | `Consolidacao.APROVADO` |
| concluinte/formado | consolidacao apta + `Matricula.CONCLUIDA` |
| diploma entregue | `CertificadoDiploma.ENTREGUE` |

---

## 13) Implementacao executavel no projeto
Comando criado para materializar todo o caso no banco:

```bash
python manage.py seed_caso_joao_pedro --reset
```

Em ambiente Docker do projeto:

```bash
docker compose -p suap-dev -f docker-compose.yml -f docker-compose.development.yml exec -T backend python manage.py seed_caso_joao_pedro --reset
```

Arquivo do comando:
- `SUAP/backend/apps/core/management/commands/seed_caso_joao_pedro.py`

---

## 14) Resultado esperado para homologacao funcional
Ao final da execucao, o sistema deve ter:
- inscricao deferida e historico completo do ingresso
- matricula concluida com trilha P01
- vida academica com notas/frequencia/consolidacao
- registros pedagogicos e de estagio
- conselho/ata final
- historico final + historico digital
- processo administrativo de diplomacao
- diploma registrado e entregue com codigo de verificacao

---

## 15) Payloads de API (exemplos para Django + React)
### 15.1 Criar inscricao
`POST /api/v1/inscricoes/`

```json
{
  "publicacao": 1,
  "nome_candidato": "Joao Pedro da Silva",
  "cpf": "00011122285",
  "email": "joao.teste@exemplo.com",
  "telefone": "(69) 99999-0000",
  "data_nascimento": "2004-03-15",
  "modalidade_concorrencia": "AMPLA",
  "status": "PENDENTE",
  "status_candidato": "INSCRITO"
}
```

### 15.2 Criar matricula
`POST /api/v1/matriculas/`

```json
{
  "aluno": 101,
  "curso": 5,
  "turma": 9,
  "tipo_matricula": "NOVA",
  "status": "ATIVA",
  "turno": "NOITE"
}
```

### 15.3 Lancar nota
`POST /api/v1/notas/`

```json
{
  "matricula": 33,
  "descricao": "[Fundamentos da Administracao] Avaliacao 1",
  "valor": "8.0",
  "peso": "1.0",
  "data_lancamento": "2026-03-10"
}
```

### 15.4 Lancar frequencia
`POST /api/v1/frequencias/`

```json
{
  "matricula": 33,
  "data": "2026-03-12",
  "presente": true,
  "observacao": ""
}
```

### 15.5 Abrir processo administrativo
`POST /api/v1/processos/`

```json
{
  "tipo": "REQUERIMENTO",
  "requerente": 101,
  "assunto": "Diplomacao institucional - CASE-JPS-2026",
  "descricao": "Fluxo completo de emissao e registro do diploma",
  "status": "ABERTO"
}
```

### 15.6 Tramitar processo
`POST /api/v1/processos/{id}/tramitar/`

```json
{
  "setor_destino": "Registro Academico",
  "acao": "ENCAMINHADO",
  "observacao": "Validacao final para registro do diploma"
}
```

---

## 16) Visao de implementacao (back-end, front-end e administrativo)
### Back-end
- regra de dominio em modelos Django (status, transicoes, validacoes)
- servicos de emissao documental e assinaturas
- trilha de auditoria por logs de fluxo e tramitacao

### Front-end
- telas de secretaria para inscricoes, matriculas, processos e documentos
- telas academicas para diario, notas, frequencia e acompanhamento
- paines de consulta/entrega de historico e diploma

### Administrativo
- pontos de aprovacao com responsabilidade por setor
- checkpoints obrigatorios antes de concluir diplomacao
- registro institucional e guarda documental
