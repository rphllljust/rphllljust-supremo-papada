# Estrategia Hibrida de Renderizacao

## Objetivo

Reduzir custo de manutencao e risco de tela branca mantendo no React apenas areas com ganho real de SPA e devolvendo ao Django os modulos mais orientados a fluxo, formularios e permissao fina.

## Criterio adotado

- Client-side: leitura rapida, filtros simples, navegação entre listas e paineis agregados.
- Server-side: CRUDs operacionais, formularios longos, uploads, passos encadeados e regras fortes de permissao.

## Client-side nesta fase

- `/` e `/dashboard`
- `/portal` e `/portal/cursos`
- `/cursos`
- `/turmas`
- `/alunos`
- `/usuarios`
- `/unidades`
- `/agenda`
- `/access/ava-export/preview`

## Server-side nesta fase

- `/matriculas/`
- `/processos/`
- `/arquivo/`
- `/inscricoes/`
- `/estagio/`
- `/documentos/`
- `/notas/`
- `/frequencia/`
- `/admin/`

## Aplicacao pratica

- O menu lateral agora aponta diretamente para o Django nos modulos operacionais.
- As rotas React antigas de `matriculas`, `processos`, `arquivo`, `inscricoes` e `estagio` viraram redirecionamentos imediatos para o backend.
- Antes do redirecionamento, o frontend sincroniza a sessao Django via `/api/v1/auth/session/` para evitar login duplicado ao sair do SPA.
- A resolucao da URL do backend foi centralizada em `src/utils/backendUrls.js`, usando `VITE_BACKEND_ORIGIN` ou derivando a origem a partir de `VITE_API_URL`.

## Proxima fase sugerida

- Revisar se `cursos` e `turmas` devem continuar em React ou voltar ao Django quando entrarem fluxos de edicao mais complexos.
- Migrar perfil/configuracoes do usuario para paginas servidoras ou consolidar uma estrategia unica de autenticacao.
- Remover paginas React hoje redundantes apos validar o uso real em producao.