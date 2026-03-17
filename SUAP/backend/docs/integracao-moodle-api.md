# Integracao com a API REST do Moodle

## Visao geral

O Moodle expoe um unico endpoint REST para web services:

```text
/webservice/rest/server.php
```

No SUAP, a integracao inicial foi centralizada no app `apps.integracao_moodle`, com uma camada reutilizavel de client e service para evitar chamadas HTTP espalhadas pelo codigo.

## Configuracao por variaveis de ambiente

As credenciais e a URL base do Moodle devem vir do ambiente. O token nunca deve ser hardcoded no codigo-fonte.

```text
MOODLE_BASE_URL=https://moodle.exemplo.edu.br
MOODLE_WS_TOKEN=SEU_TOKEN
MOODLE_REST_FORMAT=json
MOODLE_TIMEOUT=30
MOODLE_VERIFY_SSL=True
```

Observacoes:

- `MOODLE_BASE_URL` deve apontar para a raiz do Moodle, sem incluir obrigatoriamente o endpoint REST.
- O endpoint efetivo usado pelo backend e montado como `MOODLE_BASE_URL + /webservice/rest/server.php`.
- `MOODLE_REST_FORMAT` deve permanecer como `json`.
- `MOODLE_TIMEOUT` define o timeout das chamadas HTTP em segundos.
- O projeto ainda aceita as variaveis antigas `MOODLE_API_*` como alias de compatibilidade.

## Parametros padrao enviados ao Moodle

Toda chamada REST enviada pelo SUAP inclui os seguintes query params:

- `wstoken`: token de autenticacao do web service
- `wsfunction`: nome da funcao Moodle a executar
- `moodlewsrestformat`: formato da resposta, atualmente `json`

Exemplo conceitual:

```http
GET /webservice/rest/server.php?wstoken=SEU_TOKEN&wsfunction=core_course_get_courses&moodlewsrestformat=json
```

## Funcoes aprovadas nesta fase

O client do SUAP agora bloqueia qualquer `wsfunction` fora da lista abaixo. Isso evita expandir a integracao de forma acidental antes de fechar as regras de negocio.

| Funcao | Uso previsto |
| --- | --- |
| `core_course_get_categories` | Consultar detalhes de categorias |
| `core_course_get_courses` | Consultar detalhes de cursos |
| `core_grades_get_grade_tree` | Consultar a estrutura de notas de um curso |
| `core_grades_get_gradeitems` | Consultar itens de nota |
| `core_grades_update_grades` | Atualizar item de nota e notas associadas |
| `gradereport_user_get_grade_items` | Obter a lista completa de grade items por usuario |
| `gradereport_user_get_grades_table` | Obter a tabela de notas de usuarios em um curso |
| `mod_assign_save_grade` | Salvar nota de um aluno em uma atividade |
| `mod_assign_save_grades` | Salvar notas em lote para uma atividade |

## Primeira funcao integrada: `core_course_get_courses`

A primeira funcao suportada pela base atual e:

```text
core_course_get_courses
```

Ela retorna uma lista JSON com os cursos disponiveis no Moodle.

### Exemplo de requisicao

```bash
curl "https://moodle.exemplo.edu.br/webservice/rest/server.php?wstoken=SEU_TOKEN&wsfunction=core_course_get_courses&moodlewsrestformat=json"
```

### Exemplo de resposta

```json
[
    {
        "id": 12,
        "shortname": "TEC-INFO-2026",
        "categoryid": 5,
        "fullname": "Tecnico em Informatica 2026",
        "displayname": "Tecnico em Informatica 2026",
        "idnumber": "CURSO-TEC-INFO-2026",
        "summary": "<p>Curso tecnico integrado</p>",
        "summaryformat": 1,
        "format": "topics",
        "visible": 1,
        "startdate": 1767222000,
        "enddate": 1798758000,
        "timecreated": 1764626400,
        "timemodified": 1764712800,
        "enablecompletion": 1,
        "showactivitydates": 1,
        "showcompletionconditions": 1,
        "courseformatoptions": [
            {
                "name": "numsections",
                "value": 12
            }
        ]
    }
]
```

## Campos relevantes da resposta

- `id`: identificador do curso no Moodle
- `shortname`: nome curto, normalmente util para referencias tecnicas
- `categoryid`: categoria Moodle onde o curso esta vinculado
- `fullname`: nome completo do curso
- `displayname`: nome de exibicao
- `idnumber`: identificador externo do curso, quando configurado
- `summary`: resumo do curso; pode vir em HTML
- `summaryformat`: formato do resumo
- `format`: formato estrutural do curso no Moodle
- `visible`: indica visibilidade do curso
- `startdate` e `enddate`: datas em timestamp Unix
- `timecreated` e `timemodified`: timestamps Unix de criacao e ultima alteracao
- `enablecompletion`: indica se o acompanhamento de conclusao esta habilitado
- `showactivitydates`: indica se datas de atividades sao exibidas
- `showcompletionconditions`: indica se condicoes de conclusao sao exibidas
- `courseformatoptions`: opcoes adicionais do formato do curso

## Observacoes importantes sobre os dados

- `summary` pode conter HTML retornado pelo Moodle e hoje e preservado sem sanitizacao ou conversao.
- Datas e horarios vindos do Moodle permanecem em timestamp Unix nesta primeira etapa.
- `visible` e tratado como status logico de visibilidade do curso.
- Cursos com `format = "site"` podem representar o curso institucional principal do Moodle e talvez precisem ser ignorados em regras futuras de sincronizacao.

## Organizacao interna no backend

Arquitetura inicial implementada:

- `apps.integracao_moodle.client.MoodleApiClient`: encapsula a comunicacao HTTP com o Moodle
- `apps.integracao_moodle.services.get_moodle_api_client()`: fabrica do client a partir do `settings`
- `apps.integracao_moodle.services.get_moodle_categories()`: consulta categorias do Moodle
- `apps.integracao_moodle.services.get_moodle_courses()`: caso de uso inicial para obter cursos
- `apps.integracao_moodle.services.sync_moodle_categories_data()`: persiste o espelho local de categorias Moodle
- `apps.integracao_moodle.services.sync_moodle_catalog_data()`: persiste o espelho local de categorias e cursos Moodle, vinculando curso a categoria
- `apps.integracao_moodle.services.import_moodle_courses_to_formacao_inicial()`: integra os cursos vindos do Moodle ao modelo interno `Curso`
- `apps.integracao_moodle.normalizers`: normalizacao defensiva dos cursos retornados pela API
- `apps.integracao_moodle.exceptions`: hierarquia de erros especificos da integracao

Persistencia local introduzida nesta etapa:

- `apps.integracao_moodle.MoodleCategory`: espelho local das categorias retornadas por `core_course_get_categories`
- `apps.integracao_moodle.MoodleCourse`: espelho local dos cursos retornados por `core_course_get_courses`, com vinculo para a categoria Moodle e para o `Curso` interno quando existir
- `apps.integracao_moodle.MoodleGradeSnapshot`: snapshots locais das consultas de notas
- `apps.integracao_moodle.MoodleWritebackLog`: log local das operacoes de escrita em notas e assignments

Comportamentos atuais do client:

- usa o endpoint REST padrao do Moodle
- envia `wstoken`, `wsfunction` e `moodlewsrestformat` automaticamente
- aceita apenas as `wsfunction` aprovadas para esta fase da integracao
- suporta parametros extras dentro desse conjunto aprovado
- usa `GET` para consultas e `POST` para operacoes de escrita
- achata payloads aninhados em notacao esperada pelo REST do Moodle, como `grades[0][userid]`
- registra logs sem expor o token
- trata timeout, falha de conexao, HTTP inesperado, JSON invalido e erros do proprio Moodle

## Endpoint interno de teste

Para validacao administrativa, o backend expoe:

```text
GET /api/v1/integracoes/moodle/categorias/
POST /api/v1/integracoes/moodle/categorias/
```

```text
GET /api/v1/integracoes/moodle/cursos/
POST /api/v1/integracoes/moodle/cursos/
```

```text
POST /api/v1/integracoes/moodle/notas/
POST /api/v1/integracoes/moodle/assignments/
```

Esses endpoints:

- reutiliza a mesma camada de servico usada pelo restante da integracao
- exige autenticacao
- reutiliza a permissao `CanExportToAva`
- nao expoe token nem detalhes sensiveis da configuracao

### Categorias

- `GET /api/v1/integracoes/moodle/categorias/` consulta as categorias diretamente no Moodle
- `POST /api/v1/integracoes/moodle/categorias/` persiste o espelho local das categorias no banco do SUAP

Payload opcional:

```json
{
    "criteria": {
        "addsubcategories": 0
    }
}
```

### Cursos

Para armazenar cursos do Moodle localmente e opcionalmente integrá-los ao catálogo interno já existente no SUAP, o endpoint de cursos aceita `POST`:

```text
POST /api/v1/integracoes/moodle/cursos/
```

Payload opcional:

```json
{
    "unidade_codigo": "sede",
    "integrar_catalogo_interno": true
}
```

Comportamento atual:

- sempre consulta `core_course_get_categories` e `core_course_get_courses` para garantir o vinculo curso → categoria Moodle
- persiste categorias e cursos em tabelas locais dedicadas antes de tocar no catalogo interno
- quando `integrar_catalogo_interno=true`, continua gravando os cursos no modelo `Curso` sem `eixo_tecnologico`, o que os coloca provisoriamente no agrupamento atual de formacao inicial

### Notas

O endpoint `POST /api/v1/integracoes/moodle/notas/` aceita as acoes:

- `grade_tree`
- `gradeitems`
- `user_grade_items`
- `user_grades_table`
- `update_grades`

Formato base:

```json
{
    "action": "grade_tree",
    "params": {
        "courseid": 12
    }
}
```

As consultas ficam armazenadas em `MoodleGradeSnapshot`. A acao `update_grades` registra a operacao em `MoodleWritebackLog`.

### Assignments

O endpoint `POST /api/v1/integracoes/moodle/assignments/` aceita as acoes:

- `save_grade`
- `save_grades`

Formato base:

```json
{
    "action": "save_grade",
    "params": {
        "assignmentid": 77,
        "userid": 42,
        "grade": 8.5
    }
}
```

Essas operacoes sao enviadas ao Moodle e registradas localmente em `MoodleWritebackLog`.

## Comando administrativo de teste

Tambem foi criado o comando:

```bash
python manage.py testar_integracao_moodle
```

O comando consulta `core_course_get_courses`, mostra a quantidade de cursos retornados e lista os primeiros registros de forma amigavel.

## Comandos administrativos de espelho local

Para sincronizar apenas as categorias do Moodle no banco local do SUAP:

```bash
python manage.py sincronizar_categorias_moodle
```

Para sincronizar categorias e cursos no espelho local do SUAP, sem importar para o catalogo interno `Curso`:

```bash
python manage.py sincronizar_catalogo_moodle
```

Esses comandos sao o caminho mais direto para preparar a base local da integracao antes de qualquer reconciliacao com o catalogo interno.

## Comando de importacao para o catalogo interno

Tambem foi criado o comando:

```bash
python manage.py importar_cursos_moodle --unidade-codigo sede
```

Comportamento atual da importacao:

- ignora o curso institucional com `format = "site"`
- tenta localizar um `Curso` existente com o mesmo `nome` e a mesma `unidade` para apenas vincular o `moodle_course_id`
- cria um novo `Curso` quando nao encontra correspondencia interna
- usa `moodle_course_id` como chave de sincronizacao para reimportacoes futuras
- persiste `moodle_shortname` para rastreabilidade
- persiste um espelho local do Moodle em `MoodleCategory` e `MoodleCourse`
- ainda nao faz sincronizacao bidirecional nem aplica regras automaticas de reconciliacao entre SUAP e Moodle

## Seguranca

- O token nao deve ser registrado em logs, commits, fixtures ou documentacao.
- Exemplos tecnicos devem usar `SEU_TOKEN` em vez de credenciais reais.
- Erros expostos pela API interna e pelo management command nao devem vazar `wstoken`.
- A configuracao deve permanecer centralizada em variaveis de ambiente e `settings.py`.

## Proximos passos recomendados

1. Fechar as regras de negocio para reconciliacao entre `MoodleCourse` e `Curso` antes de transformar esse espelho em sincronizacao automatica.
2. Definir mapeamentos entre identificadores internos do SUAP e identificadores externos do Moodle.
3. Expandir os snapshots locais de notas para regras de consulta historica, caso isso passe a ser requisito funcional.
4. Criar conversores centralizados para timestamps Unix e para tratamento seguro de HTML, quando isso passar a ser necessario.