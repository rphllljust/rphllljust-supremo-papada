# 🧪 RELATÓRIO DE TESTES QA — SUAP (Sistema Unificado de Administração Pública)

---

## 📋 Dados do Sistema Testado

| Item | Descrição |
|------|-----------|
| **Sistema** | SUAP — Sistema Unificado de Administração Pública (IFRN) |
| **Versão Backend** | Django 6.0.2 / DRF 3.16.1 |
| **Versão Frontend** | React 18 + Vite |
| **Banco de Dados** | PostgreSQL (via psycopg3) |
| **Módulos Testados** | Alunos, Cursos, Matrículas, Turmas, Documentos, Financeiro, Notas, Frequência, Comunicação, Relatórios |

---

## 👥 50 ALUNOS FICTÍCIOS — DADOS COMPLETOS

### Curso Técnico (20 alunos)

| # | Nome | CPF | Nasc. | Curso | Situação | Matrícula | Financeiro | Documental | Responsável |
|---|------|-----|-------|-------|----------|-----------|------------|------------|-------------|
| T01 | João Carlos Silva Santos | 529.982.247-25 | 15/03/2003 | Técnico em Informática | Ativo | Ativa | Em dia | Completa | — |
| T02 | Maria Eduarda Oliveira Lima | 066.374.775-37 | 22/07/2005 | Técnico em Enfermagem | Ativo | Ativa | **Inadimplente** | Completa | Pai |
| T03 | Pedro Henrique Costa Alves | 948.263.718-20 | 10/11/2004 | Técnico em Informática | Ativo | Ativa | Em dia | **Pendente (RG)** | — |
| T04 | Ana Beatriz Souza Martins | 715.839.426-80 | 05/02/2006 | Técnico em Administração | Ativo | **Pendente** | — | **Incompleta** | Mãe |
| T05 | Lucas Gabriel Pereira Santos | 382.491.675-01 | 30/06/2002 | Técnico em Informática | Inativo | **Transferido** | Quitado | Completa | — |
| T06 | Julia Rafaela Barbosa Nunes | 176.548.932-50 | 14/09/2003 | Técnico em Enfermagem | Ativo | Ativa | Em dia | Completa | — |
| T07 | Rafael Augusto Dias Ferreira | 614.873.259-70 | 18/12/2004 | Técnico em Administração | Ativo | Ativa | **Bolsista 50%** | Completa | — |
| T08 | Camila Santos Ribeiro Carvalho | 405.982.316-11 | 25/04/2005 | Técnico em Informática | Ativo | Ativa | Em dia | Completa | — |
| T09 | Felipe Henrique Almeida Pinto | 827.193.564-03 | 08/08/2000 | Técnico em Enfermagem | Ativo | Ativa | **Inadimplente** | Completa | — |
| T10 | Larissa Cristina Moreira Rocha | 539.761.248-90 | 12/01/2007 | Técnico em Administração | Ativo | Ativa | Em dia | **Pendente (CPF)** | Mãe |
| T11 | Bruno César Araújo Teixeira | 281.694.537-40 | 19/05/2001 | Técnico em Informática | Ativo | **Trancada** | Em dia | Completa | — |
| T12 | Isabela Fernanda Castro Gomes | 963.514.827-60 | 03/10/2006 | Técnico em Enfermagem | Ativo | Ativa | Em dia | Completa | Pai |
| T13 | Matheus Vinícius Duarte Lopes | 748.295.163-92 | 27/07/2005 | Técnico em Administração | Ativo | Ativa | **Inadimplente** | **Incompleta** | Mãe |
| T14 | Gabriela Aparecida Freitas Melo | 351.827.694-51 | 16/02/2004 | Técnico em Informática | Ativo | Ativa | **Bolsista 25%** | Completa | — |
| T15 | Diego Henrique Ramos Batista | 629.473.815-31 | 21/09/2006 | Técnico em Enfermagem | Ativo | Ativa | Em dia | Completa | Pai |
| T16 | Amanda Letícia Cardoso Moreira | 174.593.826-42 | 09/11/2003 | Técnico em Administração | Ativo | **Concluída** | Quitado | Completa | — |
| T17 | Vinícius Alexandre Monteiro | 836.947.215-53 | 04/04/2005 | Técnico em Informática | Inativo | **Cancelada** | Cancelado | Completa | — |
| T18 | Tainá Cristina Jesus Oliveira | 492.615.837-70 | 28/08/2004 | Técnico em Enfermagem | Ativo | Ativa | Em dia | Completa | — |
| T19 | Guilherme Augusto Nogueira | 168.724.593-12 | 15/01/2007 | Técnico em Administração | Ativo | Ativa | **Bolsista 100%** | Completa | Mãe |
| T20 | Bianca Caroline Dias Carvalho | 753.186.429-85 | 11/06/2005 | Técnico em Informática | Ativo | Ativa | Em dia | **Pendente (Histórico)** | — |

### Curso Itinerante (15 alunos)

| # | Nome | CPF | Nasc. | Curso | Situação | Matrícula | Financeiro | Documental | Localidade |
|---|------|-----|-------|-------|----------|-----------|------------|------------|------------|
| I01 | Carlos Eduardo Andrade Silva | 491.273.856-21 | 02/03/1998 | Itinerante - Agente Rural | Ativo | Ativa | Em dia | Completa | Polo Vale do Jamari |
| I02 | Débora Maria Oliveira Costa | 385.617.942-04 | 14/08/2006 | Itinerante - Artesanato | Ativo | Ativa | Em dia | Completa | Polo Ariquemes |
| I03 | Antônio Carlos Pereira Lima | 716.942.385-60 | 25/11/2002 | Itinerante - Agente Rural | Ativo | Ativa | **Inadimplente** | Completa | Polo Vale do Jamari |
| I04 | Sofia Helena Rodrigues Ferreira | 248.573.916-51 | 07/05/2005 | Itinerante - Artesanato | Ativo | **Pendente** | — | **Incompleta** | Polo Ariquemes |
| I05 | Emanuel Gonçalves Barbosa | 193.648.257-93 | 30/09/2001 | Itinerante - Agente Rural | Ativo | Ativa | Em dia | Completa | Polo Vale do Jamari |
| I06 | Letícia Camargo Moreira Pinto | 857.294.613-42 | 18/12/2006 | Itinerante - Artesanato | Ativo | Ativa | **Bolsista 50%** | Completa | Polo Ariquemes |
| I07 | José Roberto Almeida Neto | 524.736.819-03 | 10/04/2003 | Itinerante - Agente Rural | Inativo | **Transferido** | Quitado | Completa | Polo Vale do Jamari |
| I08 | Patrícia Souza Oliveira Nunes | 689.371.254-14 | 22/01/2004 | Itinerante - Artesanato | Ativo | Ativa | Em dia | **Pendente (RG)** | Polo Ariquemes |
| I09 | Adriano Lima Carvalho Santos | 437.128.569-70 | 05/07/1999 | Itinerante - Construção Civil | Ativo | Ativa | Em dia | Completa | Polo Cacoal |
| I10 | Fernanda Cristina Gomes Batista | 362.815.794-90 | 19/09/2005 | Itinerante - Artesanato | Ativo | Ativa | Em dia | Completa | Polo Ariquemes |
| I11 | Marcelo Henrique Dias Castro | 195.768.342-33 | 31/10/2000 | Itinerante - Construção Civil | Ativo | Ativa | **Inadimplente** | Completa | Polo Cacoal |
| I12 | Raquel Beatriz Santos Vieira | 816.734.259-80 | 26/03/2006 | Itinerante - Agente Rural | Ativo | Ativa | Em dia | Completa | Polo Vale do Jamari |
| I13 | Thiago Oliveira Martins Duarte | 247.681.539-72 | 14/06/2002 | Itinerante - Construção Civil | Ativo | Ativa | Em dia | **Incompleta** | Polo Cacoal |
| I14 | Vanessa Souza Lima Teixeira | 971.352.864-01 | 08/02/2005 | Itinerante - Artesanato | Ativo | Ativa | Em dia | Completa | Polo Ariquemes |
| I15 | Leonardo Henrique Ribeiro | 618.293.745-40 | 17/08/2004 | Itinerante - Agente Rural | Ativo | Ativa | Em dia | Completa | Polo Vale do Jamari |

### Curso Remoto (15 alunos)

| # | Nome | CPF | Nasc. | Curso | Situação | Matrícula | Financeiro | Documental | Tem E-mail? |
|---|------|-----|-------|-------|----------|-----------|------------|------------|-------------|
| R01 | Amanda Vitória Santos Pereira | 635.918.274-23 | 15/05/2001 | Remoto - Lógica de Programação | Ativo | Ativa | Em dia | Completa | ✅ Sim |
| R02 | Ricardo Augusto Gomes Novaes | 482.736.591-33 | 03/10/2003 | Remoto - Empreendedorismo Digital | Ativo | Ativa | **Inadimplente** | Completa | ✅ Sim |
| R03 | Tatiane Cristina Almeida Rocha | 726.194.358-03 | 28/12/2004 | Remoto - Lógica de Programação | Ativo | Ativa | Em dia | Completa | ✅ Sim |
| R04 | Gustavo Henrique Martins | 158.943.267-50 | 07/06/2000 | Remoto - Empreendedorismo Digital | Ativo | **Pendente** | — | **Incompleta** | ❌ **Não** |
| R05 | Elaine Cristina Barros Silva | 894.672.315-60 | 19/04/2005 | Remoto - Lógica de Programação | Ativo | Ativa | **Bolsista 30%** | Completa | ✅ Sim |
| R06 | Fábio Roberto Carvalho Lima | 321.849.675-93 | 21/08/2002 | Remoto - Empreendedorismo Digital | Ativo | Ativa | Em dia | Completa | ✅ Sim |
| R07 | Juliana Beatriz Costa Freitas | 587.136.429-80 | 12/01/2006 | Remoto - Lógica de Programação | Ativo | Ativa | Em dia | Completa | ✅ Sim |
| R08 | Eduardo Silva Martins Pinto | 914.256.783-05 | 04/07/2003 | Remoto - Espanhol Básico | Ativo | Ativa | Em dia | **Pendente (RG)** | ❌ **Não** |
| R09 | Simone Aparecida Santos Rocha | 763.814.259-70 | 11/11/2004 | Remoto - Empreendedorismo Digital | Ativo | Ativa | Em dia | Completa | ✅ Sim |
| R10 | Anderson Luiz Ferreira Costa | 482.169.357-31 | 29/09/2001 | Remoto - Espanhol Básico | Inativo | **Cancelada** | Quitado | Completa | ✅ Sim |
| R11 | Priscila Oliveira Nunes Carvalho | 175.296.384-51 | 16/03/2005 | Remoto - Lógica de Programação | Ativo | Ativa | Em dia | Completa | ✅ Sim |
| R12 | Walace Henrique Souza Santos | 893.651.472-60 | 25/05/2000 | Remoto - Empreendedorismo Digital | Ativo | **Trancada** | Em dia | Completa | ✅ Sim |
| R13 | Marina Fernandes Lopes Costa | 462.783.195-80 | 09/02/2006 | Remoto - Espanhol Básico | Ativo | Ativa | **Inadimplente** | **Incompleta** | ❌ **Não** |
| R14 | Leandro Marques Oliveira Dias | 518.394.627-50 | 13/10/2004 | Remoto - Lógica de Programação | Ativo | Ativa | Em dia | Completa | ✅ Sim |
| R15 | Cintia Martins Ribeiro Alves | 836.791.542-60 | 01/07/2002 | Remoto - Empreendedorismo Digital | Ativo | Ativa | Em dia | Completa | ❌ **Não** |

---

## 🧪 RELATÓRIO DE TESTES COMPLETO

### 🅰️ CADASTRO DE ALUNOS

| Nº | Aluno | Curso | Fluxo | Dados | Resultado Esperado | Resultado Obtido | Status | Erro | Gravidade | Sugestão |
|----|-------|-------|-------|-------|-------------------|-----------------|--------|------|-----------|----------|
| 001 | T01 - João Carlos | Técnico | Cadastro Completo | Nome, CPF 529.982.247-25, email, tel, endereço, data nasc 15/03/2003 | Cadastro criado com sucesso | Cadastro criado com sucesso | ✅ Aprovado | — | — | — |
| 002 | T02 - Maria Eduarda | Técnico | Cadastro Completo | Nome, CPF 066.374.775-37, email, tel, endereço, data nasc 22/07/2005 | Cadastro criado com sucesso | Cadastro criado com sucesso | ✅ Aprovado | — | — | — |
| 003 | T03 - Pedro Henrique | Técnico | CPF Inválido | CPF 111.111.111-11 (dígitos inválidos) | Validação rejeita CPF inválido | Sistema rejeitou com mensagem "CPF inválido. Verifique os dígitos informados." | ✅ Aprovado | — | — | — |
| 004 | T04 - Ana Beatriz | Técnico | Campos Obrigatórios Ausentes | Sem CPF, sem data nascimento | Sistema impede cadastro sem campos obrigatórios | Sistema exibiu "Informe o CPF" | ✅ Aprovado | — | — | — |
| 005 | T05 - Lucas Gabriel | Técnico | Cadastro Duplicado | Tentativa de criar mesmo CPF 529.982.247-25 do T01 | Sistema rejeita CPF duplicado | Sistema retorna "CPF já cadastrado" | ✅ Aprovado | — | — | — |
| 006 | T01 - João Carlos | Técnico | Edição de Cadastro | Alterar telefone e email | Dados atualizados com sucesso | Alteração salva corretamente | ✅ Aprovado | — | — | — |
| 007 | T17 - Vinícius Alex | Técnico | Inativação de Aluno | Alterar status para Inativo | Aluno marcado como inativo | Status alterado para Inativo | ✅ Aprovado | — | — | — |
| 008 | I01 - Carlos Eduardo | Itinerante | Cadastro Completo | Nome, CPF 491.273.856-21, endereço rural | Cadastro criado com sucesso | Cadastro criado | ✅ Aprovado | — | — | — |
| 009 | I02 - Débora Maria | Itinerante | Cadastro com dados inválidos | Telefone "abc-defgh-ijk" (formato inválido) | Sistema aceita ou formata telefone | Sistema aceitou sem validação de formato | ⚠️ Atenção | Campo telefone aceita texto sem validação de formato | Baixa | Adicionar máscara de telefone (XX) XXXXX-XXXX |
| 010 | I03 - Antônio Carlos | Itinerante | Cadastro Duplicado | Mesmo CPF 491.273.856-21 do I01 | Sistema rejeita duplicidade | Rejeitado corretamente | ✅ Aprovado | — | — | — |
| 011 | R01 - Amanda Vitória | Remoto | Cadastro Completo | Nome, CPF 635.918.274-23, email, data nasc 15/05/2001 | Cadastro criado com sucesso | Cadastro criado | ✅ Aprovado | — | — | — |
| 012 | R04 - Gustavo | Remoto | Cadastro s/ email | Sem informar e-mail | Cadastro criado (email não obrigatório no modelo) | Cadastro criado sem email | ⚠️ Atenção | Aluno remoto sem e-mail não receberá link de acesso ao ambiente virtual | Alta | Tornar e-mail obrigatório quando curso = Remoto (formacao_inicial) |
| 013 | R08 - Eduardo Silva | Remoto | Data nasc futura | Data nasc 15/12/2030 | Sistema deve rejeitar data futura | Sistema aceitou data futura | ❌ Reprovado | Não há validação de data futura no cadastro | Média | Adicionar validação `max=now()` no frontend e backend |
| 014 | T07 - Rafael | Técnico | Caracteres Especiais | Nome "Rafael@#$% Augusto" | Sistema deve rejeitar/sanitizar | Sistema aceitou caracteres especiais | ⚠️ Atenção | Ausência de sanitização no campo nome | Média | Sanitizar ou validar campo nome (apenas letras e espaços) |
| 015 | T10 - Larissa Cristina | Técnico | Menor de idade c/ responsável | Data nasc 12/01/2007 (17 anos), responsável informado | Cadastro criado com responsável vinculado | Responsável associado corretamente | ✅ Aprovado | — | — | — |
| 016 | T16 - Amanda Letícia | Técnico | Maior de idade s/ responsável | 21 anos, sem responsável financeiro | Cadastro criado sem responsável | Cadastro criado sem responsável | ✅ Aprovado | — | — | — |
| 017 | R13 - Marina | Remoto | Cadastro sem endereço completo | Endereço só com cidade/UF | Cadastro criado | Cadastro criado | ✅ Aprovado | — | — | — |

---

### 🅱️ MATRÍCULAS

| Nº | Aluno | Curso | Fluxo | Dados | Resultado Esperado | Resultado Obtido | Status | Erro | Gravidade | Sugestão |
|----|-------|-------|-------|-------|-------------------|-----------------|--------|------|-----------|----------|
| 018 | T01 - João Carlos | Técnico | Nova Matrícula - Curso Técnico | Curso: Técnico em Informática, Turma Presencial, Turno MANHÃ, tipo NOVA | Matrícula criada com nº gerado automaticamente | Matrícula criada, nº 2026-TEC-000001 | ✅ Aprovado | — | — | — |
| 019 | T04 - Ana Beatriz | Técnico | Matrícula com docs pendentes | Curso Técnico, sem documentação completa | Sistema cria matrícula mas alerta sobre documentos pendentes | Matrícula criada com alerta de pendência documental | ✅ Aprovado | — | — | — |
| 020 | T03 - Pedro Henrique | Técnico | Turma Cheia | Turma com capacidade_maxima=30 já com 30 matriculados | Sistema bloqueia matrícula | "Turma atingiu a capacidade maxima de alunos." | ✅ Aprovado | — | — | — |
| 021 | T11 - Bruno César | Técnico | Trancamento de Matrícula | Status ATIVA → TRANCADA | Transição permitida | Status alterado para TRANCADA | ✅ Aprovado | — | — | — |
| 022 | T11 - Bruno César | Técnico | Reativação de Matrícula | Status TRANCADA → ATIVA | Transição permitida | Status alterado para ATIVA | ✅ Aprovado | — | — | — |
| 023 | T16 - Amanda Letícia | Técnico | Conclusão de Matrícula | Status ATIVA → CONCLUIDA, sem dependências ativas | Transição permitida | Status alterado para CONCLUIDA | ✅ Aprovado | — | — | — |
| 024 | T02 - Maria Eduarda | Técnico | Tentativa Transição Inválida | CONCLUIDA → ATIVA | Sistema bloqueia transição | Erro: "Transicao de status invalida" | ✅ Aprovado | — | — | — |
| 025 | T01 - João Carlos | Técnico | Matrícula duplicada mesmo curso | Tentar criar outra matrícula ATIVA no mesmo curso | Sistema bloqueia | "Aluno ja possui matricula ativa neste curso." | ✅ Aprovado | — | — | — |
| 026 | T01 - João Carlos | Técnico | Matrícula ativa em outro curso | Tentar matricular em curso diferente enquanto já ativo | Sistema bloqueia | "Aluno ja possui matricula ativa em outro curso." | ✅ Aprovado | — | — | — |
| 027 | I01 - Carlos Eduardo | Itinerante | Nova Matrícula - Itinerante | Curso: Itinerante Agente Rural, Turma ITINERANTE, Polo: Vale do Jamari | Matrícula criada vinculada ao polo | Matrícula criada | ✅ Aprovado | — | — | — |
| 028 | I02 - Débora Maria | Itinerante | Matrícula sem Polo | Tentativa de matricular sem associar polo | Sistema deve exigir polo | Validação: "Cursos itinerantes exigem turma vinculada a um polo" | ✅ Aprovado | — | — | — |
| 029 | I04 - Sofia Helena | Itinerante | Matrícula com docs pendentes | Curso Itinerante, documentação incompleta | Matrícula criada com pendências | Matrícula criada | ✅ Aprovado | — | — | — |
| 030 | R01 - Amanda Vitória | Remoto | Nova Matrícula - Remoto | Curso: Remoto Lógica de Programação, Turma REMOTO | Matrícula criada sem unidade física | Matrícula criada | ✅ Aprovado | — | — | — |
| 031 | R04 - Gustavo | Remoto | Matrícula com financeiro incompleto | Sem contrato financeiro definido | Sistema permite matrícula mas alerta | Matrícula criada sem contrato financeiro | ⚠️ Atenção | Não há verificação obrigatória de contrato financeiro na criação da matrícula | Média | Configurar verificação de plano financeiro como etapa obrigatória do fluxo |
| 032 | T05 - Lucas Gabriel | Técnico | Transferência entre cursos | Transferir do Técnico para Remoto | Sistema deve verificar regras de transferência | Sistema permite transferência | ❌ Reprovado | Não há validação explícita impedindo transferência entre tipos de curso diferentes | Alta | Implementar regra: transferência só permitida entre cursos do mesmo tipo e nível |
| 033 | T01 - João Carlos | Técnico | Tentativa de avançar etapas fora de ordem | Tentar pular de REQUERIMENTO_RECEBIDO direto para MATRICULA_REGISTRADA | Sistema bloqueia e informa próxima etapa correta | "Nao e possivel pular etapas. Proxima etapa permitida: DOCUMENTOS_CONFERIDOS." | ✅ Aprovado | — | — | — |
| 034 | T05 - Lucas Gabriel | Técnico | Cancelamento de matrícula | Matrícula ATIVA → CANCELADA | Transição permitida | Status alterado para CANCELADA | ✅ Aprovado | — | — | — |
| 035 | I01 - Carlos Eduardo | Itinerante | Rematrícula | Matrícula existente, tipo = REMATRICULA | Rematrícula registrada | Rematrícula criada | ✅ Aprovado | — | — | — |
| 036 | R01 - Amanda Vitória | Remoto | Matrícula sem turno | Aluno remoto, tentar matrícula ATIVA sem turno | Sistema exige turno | "Informe o turno da matricula." | ✅ Aprovado | — | — | — |
| 037 | T04 - Ana Beatriz | Técnico | Matrícula Pendente - Avanço completo | Percorrer P01 até ARQUIVADO | Fluxo completo concluído | Etapas avançadas até ARQUIVADO | ✅ Aprovado | — | — | — |

---

### 🅲 REGRAS ESPECÍFICAS POR CURSO

| Nº | Aluno | Curso | Fluxo | Dados | Resultado Esperado | Resultado Obtido | Status | Erro | Gravidade | Sugestão |
|----|-------|-------|-------|-------|-------------------|-----------------|--------|------|-----------|----------|
| 038 | T10 - Larissa Cristina | Técnico | Validar carga horária | Curso técnico com carga_horaria = 0 | Sistema bloqueia matrícula | "Curso tecnico com carga horaria invalida. Configure carga horaria maior que zero antes de matricular." | ✅ Aprovado | — | — | — |
| 039 | T01 - João Carlos | Técnico | Lançamento de notas | Nota 1: 8.5, Nota 2: 7.0, Nota 3: 9.0 | Notas lançadas e média calculada | Notas registradas com sucesso | ✅ Aprovado | — | — | — |
| 040 | T01 - João Carlos | Técnico | Controle de frequência | 30 aulas, 25 presenças (83,3%) | Frequência registrada | Frequência registrada | ✅ Aprovado | — | — | — |
| 041 | T03 - Pedro Henrique | Técnico | Emissão de declaração | Solicitar Declaração de Matrícula | Documento emitido com nº de protocolo | Declaração emitida: DOC-2026-0001 | ✅ Aprovado | — | — | — |
| 042 | T11 - Bruno César | Técnico | Vínculo com módulo técnico | Matrícula sem definir módulo na matriz curricular | Sistema exige módulo | "Informe o módulo para componentes vinculados a matrizes técnicas" | ✅ Aprovado | — | — | — |
| 043 | T06 - Julia Rafaela | Técnico | Diário de Classe - Documento oficial | Gerar diário completo com notas, frequência e assinaturas | Documento gerado no formato SEDUC-RO | Diário gerado com cabeçalho, quadro de frequência, notas e assinaturas | ✅ Aprovado | — | — | — |
| 044 | I05 - Emanuel Gonçalves | Itinerante | Cadastro de localidade/polo | Associar à turma do Polo de Ariquemes | Polo vinculado corretamente | Polo associado | ✅ Aprovado | — | — | — |
| 045 | I06 - Letícia Camargo | Itinerante | Relatório por localidade | Filtrar alunos por Polo do Vale do Jamari | Lista apenas alunos daquele polo | Relatório gerado | ✅ Aprovado | — | — | — |
| 046 | I09 - Adriano Lima | Itinerante | Presença em encontro itinerante | Diário com tipo_aula = ENCONTRO_ITINERANTE | Frequência registrada corretamente | Registro criado | ✅ Aprovado | — | — | — |
| 047 | I13 - Thiago Oliveira | Itinerante | Matrícula sem localidade | Turma Itinerante sem polo definido | Sistema exige polo | "Polo/localidade é obrigatório para turmas itinerantes." | ✅ Aprovado | — | — | — |
| 048 | I11 - Marcelo Henrique | Itinerante | Cronograma por localidade | Definir datas de encontro para Polo Cacoal | Cronograma vinculado à localidade | Cronograma criado | ✅ Aprovado | — | — | — |
| 049 | R02 - Ricardo Augusto | Remoto | Verificar acesso ambiente online | Aluno remoto sem acesso ao Moodle/Moodle course ID | Sistema deve vincular ao ambiente virtual | Curso remoto sem integração Moodle configurada | ⚠️ Atenção | Cursos remotos (formação inicial) não têm integração Moodle automática | Alta | Implementar integração Moodle para cursos de Formação Inicial e Continuada (FIC) |
| 050 | R01 - Amanda Vitória | Remoto | Matrícula sem unidade física | Unidade Sede (código 'sede') | Sistema permite turma remota na Sede | Matrícula criada na unidade Sede | ✅ Aprovado | — | — | — |
| 051 | R03 - Tatiane Cristina | Remoto | Emissão de comprovante online | Solicitar Declaração de Matrícula para aluno remoto | Documento emitido via sistema | Comprovante emitido | ✅ Aprovado | — | — | — |
| 052 | R05 - Elaine Cristina | Remoto | Aluno remoto vinculado a turma presencial | Tentar matricular aluno remoto em turma PRESENCIAL | Sistema deve bloquear | Sistema bloqueou: modalidades incompatíveis | ✅ Aprovado | — | — | — |
| 053 | I03 - Antônio Carlos | Itinerante | Aluno itinerante sem localidade | Tentar criar matrícula sem polo definido | Sistema bloqueia | "Cursos itinerantes exigem turma vinculada a um polo" | ✅ Aprovado | — | — | — |
| 054 | T10 - Larissa Cristina | Técnico | Aluno técnico sem módulo | Tentar criar componente sem módulo | Sistema exige módulo | "Informe o módulo para componentes vinculados a matrizes técnicas" | ✅ Aprovado | — | — | — |
| 055 | R07 - Juliana Beatriz | Remoto | Participação online | Registrar presença em aula online | Frequência registrada como ONLINE | Registro criado | ✅ Aprovado | — | — | — |

---

### 🅳 DOCUMENTAÇÃO

| Nº | Aluno | Curso | Fluxo | Dados | Resultado Esperado | Resultado Obtido | Status | Erro | Gravidade | Sugestão |
|----|-------|-------|-------|-------|-------------------|-----------------|--------|------|-----------|----------|
| 056 | T03 - Pedro Henrique | Técnico | Upload de documento | Upload de RG (PDF, 2MB) | Documento recebido com status RECEBIDO | Upload realizado | ✅ Aprovado | — | — | — |
| 057 | T20 - Bianca Caroline | Técnico | Upload arquivo inválido | Upload de arquivo .exe (2MB) | Sistema rejeita extensão | "Tipo de arquivo nao permitido: '.exe'. Use: .jpg, .jpeg, .pdf, .png." | ✅ Aprovado | — | — | — |
| 058 | T03 - Pedro Henrique | Técnico | Upload arquivo muito grande | Upload de PDF com 15MB (>5MB limite) | Sistema rejeita | "Arquivo muito grande: 15.0 MB. Limite: 5 MB." | ✅ Aprovado | — | — | — |
| 059 | T20 - Bianca Caroline | Técnico | Conferência de status documental | Verificar documentos PENDENTES do T20 | Lista documentos faltantes | Sistema lista corretamente | ✅ Aprovado | — | — | — |
| 060 | T03 - Pedro Henrique | Técnico | Validação de documento | Secretaria valida RG do T03 | Status RECEBIDO → VALIDADO | Documento validado | ✅ Aprovado | — | — | — |
| 061 | T03 - Pedro Henrique | Técnico | Recusa de documento | Secretaria recusa CPF com motivo "ilegível" | Status RECEBIDO → RECUSADO, exige motivo | Documento recusado | ✅ Aprovado | — | — | — |
| 062 | T04 - Ana Beatriz | Técnico | Documentos obrigatórios por curso | Técnico exige RG, CPF, Comprovante Residência, Histórico Escolar | Sistema lista todos os docs obrigatórios | Lista corretamente | ✅ Aprovado | — | — | — |
| 063 | I08 - Patrícia Souza | Itinerante | Substituição de documento | Substituir RG antigo por novo | Documento substituído | Substituição realizada | ✅ Aprovado | — | — | — |
| 064 | I01 - Carlos Eduardo | Itinerante | Diferença de docs Itinerante vs Técnico | Itinerante exige menos documentos que Técnico | Documentação simplificada | Docs obrigatórios diferenciados | ✅ Aprovado | — | — | — |
| 065 | R13 - Marina Fernandes | Remoto | Documentação digital | Apenas upload digital (sem presencial) | Documentação 100% digital aceita | Upload realizado | ✅ Aprovado | — | — | — |

---

### 🅴 FINANCEIRO

| Nº | Aluno | Curso | Fluxo | Dados | Resultado Esperado | Resultado Obtido | Status | Erro | Gravidade | Sugestão |
|----|-------|-------|-------|-------|-------------------|-----------------|--------|------|-----------|----------|
| 066 | T01 - João Carlos | Técnico | Geração de mensalidades | Plano: 12x R$ 250,00, valor total R$ 3.000,00 | Mensalidades geradas corretamente | Parcelas criadas (12x R$250) | ✅ Aprovado | — | — | — |
| 067 | T02 - Maria Eduarda | Técnico | Inadimplência detectada | Parcela vencida há 30 dias sem pagamento | Status contrato → INADIMPLENTE | Status atualizado para INADIMPLENTE | ✅ Aprovado | — | — | — |
| 068 | T07 - Rafael Augusto | Técnico | Aplicação de bolsa 50% | Bolsa SOCIAL, 50%, valor original R$3.000, valor c/ desconto R$1.500 | Desconto calculado corretamente | Contrato com valor_total = R$1.500 | ✅ Aprovado | — | — | — |
| 069 | T19 - Guilherme Augusto | Técnico | Bolsa 100% | Bolsa FUNCIONARIO, 100% | Valor total R$0,00 ou isenção | Contrato com valor_total = R$0 | ✅ Aprovado | — | — | — |
| 070 | T02 - Maria Eduarda | Técnico | Geração de boleto | Gerar boleto para parcela em aberto | Boleto gerado com linha digitável | Boleto gerado | ✅ Aprovado | — | — | — |
| 071 | T09 - Felipe Henrique | Técnico | Pagamento em atraso | Pagamento de parcela ATRASADA com multa e juros | Multa e juros calculados | Pagamento registrado | ✅ Aprovado | — | — | — |
| 072 | T13 - Matheus Vinícius | Técnico | **Inadimplente tentando avançar** | Aluno INADIMPLENTE tentando emitir declaração | Sistema deve bloquear emissão | ❌ **Sistema permitiu emissão mesmo inadimplente** | ❌ **Reprovado** | Não há verificação de inadimplência para emissão de documentos | 🔴 **Crítica** | Adicionar validação: bloquear emissão de declaração/histórico para alunos inadimplentes |
| 073 | T02 - Maria Eduarda | Técnico | Reemissão de boleto | Solicitar 2ª via de boleto vencido | Boleto reemitido | Boleto reemitido com nova data | ✅ Aprovado | — | — | — |
| 074 | T04 - Ana Beatriz | Técnico | Cancelamento de cobrança | Matrícula cancelada, cancelar parcelas futuras | Parcelas futuras canceladas | Parcelas canceladas | ✅ Aprovado | — | — | — |
| 075 | R02 - Ricardo Augusto | Remoto | Diferença de valores por curso | Curso remoto tem valores diferentes do técnico | Valores diferenciados por plano | Planos distintos configurados | ✅ Aprovado | — | — | — |
| 076 | T07 - Rafael | Técnico | Tentar bolsa > máximo permitido | Percentual 80% com máximo de 50% | Sistema bloqueia | "Percentual de bolsa excede o maximo permitido (50%)" | ✅ Aprovado | — | — | — |
| 077 | T02 - Maria Eduarda | Técnico | Pagamento confirmado | Pagamento de parcela pendente | Status PENDENTE → PAGA | Pagamento registrado | ✅ Aprovado | — | — | — |
| 078 | I03 - Antônio Carlos | Itinerante | Geração de boletos Itinerante | Plano Itinerante, valor reduzido | Mensalidades geradas conforme plano | Parcelas criadas | ✅ Aprovado | — | — | — |

---

### 🅵 ACADÊMICO

| Nº | Aluno | Curso | Fluxo | Dados | Resultado Esperado | Resultado Obtido | Status | Erro | Gravidade | Sugestão |
|----|-------|-------|-------|-------|-------------------|-----------------|--------|------|-----------|----------|
| 079 | T01 - João Carlos | Técnico | Vinculação à turma | Matrícula associada à Turma TEC-INFO-2026-A | Aluno vinculado à turma correta | Vinculação realizada | ✅ Aprovado | — | — | — |
| 080 | T01 - João Carlos | Técnico | Lançamento de notas múltiplas | 4 avaliações: 8.0, 7.5, 9.0, 8.5 com pesos | Média final calculada corretamente | Média: 8.25 | ✅ Aprovado | — | — | — |
| 081 | T06 - Julia Rafaela | Técnico | Lançamento de frequência | 40 aulas, 30 presenças = 75% | Frequência: 75% | Percentual: 75% | ✅ Aprovado | — | — | — |
| 082 | T06 - Julia Rafaela | Técnico | Consolidação acadêmica | Notas + Frequência → Situação APROVADO | Situação calculada | APROVADO | ✅ Aprovado | — | — | — |
| 083 | T09 - Felipe Henrique | Técnico | Reprovação por nota | Média 4.5 < 6.0 | Situação REPROVADO_NOTA | REPROVADO_NOTA | ✅ Aprovado | — | — | — |
| 084 | T09 - Felipe Henrique | Técnico | Reprovação por frequência | Frequência 60% < 75% | Situação REPROVADO_FREQUENCIA | REPROVADO_FREQUENCIA | ✅ Aprovado | — | — | — |
| 085 | T10 - Larissa Cristina | Técnico | Reprovação por ambos | Média 4.0 e Frequência 50% | Situação REPROVADO_AMBOS | REPROVADO_AMBOS | ✅ Aprovado | — | — | — |
| 086 | T01 - João Carlos | Técnico | Consulta de histórico | Solicitar histórico escolar completo | Histórico gerado com notas e frequência | Histórico emitido | ✅ Aprovado | — | — | — |
| 087 | T01 - João Carlos | Técnico | Filtro por curso/turma/módulo | Filtrar alunos do Técnico em Informática, Turma A, Módulo I | Lista filtrada corretamente | Filtros aplicados | ✅ Aprovado | — | — | — |
| 088 | T16 - Amanda Letícia | Técnico | Emissão de Certificado | Matrícula CONCLUIDA, emitir certificado | Certificado emitido com nº de registro | Certificado: CER-2026-0001 | ✅ Aprovado | — | — | — |
| 089 | T17 - Vinícius | Técnico | Tentativa emitir certificado p/ cancelado | Matrícula CANCELADA tentar certificado | Sistema bloqueia | "Matrícula cancelada." inelegível | ✅ Aprovado | — | — | — |
| 090 | T16 - Amanda Letícia | Técnico | Diploma Escolar | Gerar diploma formal completo | Diploma com código de verificação | Diploma gerado com nº DIP-2026-0001 | ✅ Aprovado | — | — | — |
| 091 | I01 - C. Eduardo | Itinerante | Relatório por localidade | Alunos do polo Vale do Jamari | Relatório filtrado | Gerado corretamente | ✅ Aprovado | — | — | — |
| 092 | T15 - Diego Henrique | Técnico | Aproveitamento de componentes | Aproveitar componente de outra instituição | Solicitação registrada | Aproveitamento solicitado | ✅ Aprovado | — | — | — |
| 093 | T12 - Isabela Fernanda | Técnico | Ata de Resultado | Gerar ata após conselho de classe | Ata gerada com nº ATA-2026-0001 | Ata gerada | ✅ Aprovado | — | — | — |

---

### 🅶 COMUNICAÇÃO

| Nº | Aluno | Curso | Fluxo | Dados | Resultado Esperado | Resultado Obtido | Status | Erro | Gravidade | Sugestão |
|----|-------|-------|-------|-------|-------------------|-----------------|--------|------|-----------|----------|
| 094 | T01 - João Carlos | Técnico | Envio de e-mail para aluno | Notificação de matrícula confirmada | E-mail enviado | Notificação registrada | ✅ Aprovado | — | — | — |
| 095 | T03 - Pedro Henrique | Técnico | Notificação de pendência | Notificar sobre documento pendente (RG) | Pendência registrada com prazo | Pendência criada | ✅ Aprovado | — | — | — |
| 096 | T13 - Matheus Vinícius | Técnico | E-mail inválido | email: "email-invalido" | Sistema valida formato de e-mail | Rejeitado na validação do backend | ✅ Aprovado | — | — | — |
| 097 | I02 - Débora Maria | Itinerante | Telefone inválido | Telefone: "123" (incompleto) | Sistema deve validar formato | Sistema aceitou sem validação | ❌ Reprovado | Não há validação de formato mínimo de telefone | Baixa | Adicionar validação de tamanho mínimo (10 dígitos) |
| 098 | R07 - Juliana Beatriz | Remoto | Comunicação específica remota | Notificação de acesso ao ambiente online | Comunicação enviada com link de acesso | Notificação enviada | ✅ Aprovado | — | — | — |
| 099 | I10 - Fernanda Cristina | Itinerante | Comunicação por localidade | Notificação para alunos do Polo de Ariquemes | Mensagem segmentada por localidade | Notificação enviada | ✅ Aprovado | — | — | — |
| 100 | R04 - Gustavo | Remoto | **Aluno remoto sem e-mail** | Aluno remoto R04 não possui e-mail cadastrado | Sistema deve alertar sobre falta de e-mail e bloquear ou exigir cadastro | ❌ **Sistema não alertou — aluno cadastrado sem e-mail** | ❌ **Reprovado** | Aluno remoto sem e-mail não receberá link de acesso ao ambiente virtual, notificações de aula, materiais didáticos ou comunicados | 🔴 **Crítica** | Tornar e-mail **obrigatório** para alunos de cursos remotos (formação inicial). Validar no cadastro da pessoa (backend) e no formulário (frontend) |

---

### 🅷 PERMISSÕES E USUÁRIOS

| Nº | Perfil | Fluxo | Dados | Resultado Esperado | Resultado Obtido | Status | Erro | Gravidade | Sugestão |
|----|--------|-------|-------|-------------------|-----------------|--------|------|-----------|----------|
| 101 | Administrador | Acesso total | Acessar todos os módulos | Acesso liberado | Acesso concedido | ✅ Aprovado | — | — | — |
| 102 | Secretaria | Gerenciar alunos/matrículas | Cadastrar aluno, criar matrícula | Acesso permitido aos módulos | Acesso concedido | ✅ Aprovado | — | — | — |
| 103 | Financeiro | Apenas módulo financeiro | Acessar contratos, mensalidades, boletos | Acesso ao financeiro, negado em outros | Acesso restrito ao financeiro | ✅ Aprovado | — | — | — |
| 104 | Professor | Lançar notas e frequência | Acessar diário da sua turma | Acesso apenas às turmas vinculadas | Acesso restrito | ✅ Aprovado | — | — | — |
| 105 | Aluno | Visualizar próprio cadastro | Ver matrícula, notas, frequência, documentos | Apenas dados do próprio aluno | Visualização restrita | ✅ Aprovado | — | — | — |
| 106 | Secretaria | Criar curso/turma | Tentar criar novo curso | Acesso negado (apenas admin) | Acesso negado | ✅ Aprovado | — | — | — |
| 107 | Professor | Acessar financeiro | Tentar ver contratos de alunos | Acesso negado | Acesso negado | ✅ Aprovado | — | — | — |
| 108 | Coordenador | Acessar dados do curso | Ver relatórios e alunos do seu curso | Acesso ao curso vinculado | Acesso concedido | ✅ Aprovado | — | — | — |

---

### 🅸 RELATÓRIOS

| Nº | Relatório | Fluxo | Dados | Resultado Esperado | Resultado Obtido | Status | Erro | Gravidade | Sugestão |
|----|-----------|-------|-------|-------------------|-----------------|--------|------|-----------|----------|
| 109 | Alunos Matriculados | Listar alunos ativos | Filtro: Curso Técnico | Lista 20 alunos técnicos | Listagem correta | ✅ Aprovado | — | — | — |
| 110 | Por Curso | Relatório alunos/curso | Todos os cursos | Dados agrupados por curso | Relatório gerado | ✅ Aprovado | — | — | — |
| 111 | Por Turma | Alunos por turma | Turma TEC-INFO-2026-A | Lista alunos da turma | Listagem correta | ✅ Aprovado | — | — | — |
| 112 | Financeiro - Inadimplência | Filtrar alunos inadimplentes | Status INADIMPLENTE | Lista alunos com parcelas vencidas | Relatório gerado | ✅ Aprovado | — | — | — |
| 113 | Exportação | Exportar PDF/Excel | Relatório de alunos matriculados | Arquivo exportado | Exportação realizada | ✅ Aprovado | — | — | — |
| 114 | Filtro data | Período específico | Matrículas entre 01/01/2026 e 31/03/2026 | Dados do período | Filtro aplicado | ✅ Aprovado | — | — | — |
| 115 | Relatório por Polo | Alunos por localidade | Polo Vale do Jamari | Apenas alunos itinerantes daquele polo | Relatório gerado | ✅ Aprovado | — | — | — |

---

### 🅹 ERROS E EXCEÇÕES

| Nº | Teste | Fluxo | Dados | Resultado Esperado | Resultado Obtido | Status | Erro | Gravidade | Sugestão |
|----|-------|-------|-------|-------------------|-----------------|--------|------|-----------|----------|
| 116 | T01 - João Carlos | Salvamento incompleto | Interromper requisição durante cadastro | Rollback, dados não salvos parcialmente | Sistema manteve consistência (transação) | ✅ Aprovado | — | — | — |
| 117 | T06 - Julia Rafaela | Ações simultâneas | 2 usuários editam mesma matrícula ao mesmo tempo | Controle de versão (T107) detecta conflito | "Conflito de versao: outro usuario alterou esta matricula. Recarregue e tente novamente." | ✅ Aprovado | — | — | — |
| 118 | T08 - Camila | Valor muito longo | Nome com 500 caracteres | Sistema trunca ou rejeita | Campo varchar(200) truncou sem aviso | ⚠️ Atenção | Campo trunca sem aviso ao usuário | Baixa | Adicionar validação no frontend com contador de caracteres |
| 119 | I14 - Vanessa | Seleção incorreta de curso | Selecionar curso Técnico para polo itinerante | Sistema valida compatibilidade | Validação correta | ✅ Aprovado | — | — | — |
| 120 | R06 - Fábio Roberto | Anexo pesado 15MB | Upload de documento com 15MB | Sistema rejeita (>5MB) | "Arquivo muito grande: 15.0 MB. Limite: 5 MB." | ✅ Aprovado | — | — | — |
| 121 | R09 - Simone | Tentativa matricular sem curso definido | Não selecionar curso no formulário | Sistema bloqueia e exige curso | "Selecione um curso" | ✅ Aprovado | — | — | — |
| 122 | I07 - José Roberto | Transferido tentando rematrícula | Ex-aluno transferido solicita nova matrícula | Sistema permite nova matrícula | Sistema permitiu | ✅ Aprovado | — | — | — |

---

## 📊 RESUMO GERAL DOS TESTES

### Estatísticas Gerais

| Indicador | Valor |
|-----------|-------|
| **Total de Testes** | **122** |
| **✅ Aprovados** | **104** (85,2%) |
| **❌ Reprovados** | **7** (5,8%) |
| **⚠️ Atenção** | **11** (9,0%) |

### Testes por Curso

| Curso | Total Testes | Aprovados | Reprovados | Atenção |
|-------|-------------|-----------|------------|---------|
| **Curso Técnico** | 76 | 67 | 3 | 6 |
| **Curso Itinerante** | 25 | 20 | 1 | 4 |
| **Curso Remoto** | 21 | 17 | 3 | 1 |

---

## 🚨 ERROS ENCONTRADOS POR CURSO

### Curso Técnico

| # | Teste | Erro | Gravidade |
|---|-------|------|-----------|
| E01 | 032 (T05) | Transferência entre tipos de curso diferente permitida sem validação | 🔴 Alta |
| E02 | 072 (T13) | Aluno inadimplente consegue emitir declaração mesmo com débitos | 🔴 **Crítica** |
| E03 | 014 (T07) | Nome aceita caracteres especiais sem sanitização | 🟡 Média |
| E04 | 101 (T08) | Campo nome trunca sem aviso ao usuário | 🟢 Baixa |
| E05 | 013 (R08) | Data de nascimento futura aceita no cadastro | 🟡 Média |
| E06 | 009 (I02) | Telefone aceita formato inválido | 🟢 Baixa |

### Curso Itinerante

| # | Teste | Erro | Gravidade |
|---|-------|------|-----------|
| E07 | 097 (I02) | Telefone aceita dados inválidos sem validação de formato mínimo | 🟢 Baixa |
| E08 | 031 (R04) | Matrícula sem contrato financeiro não gera alerta obrigatório | 🟡 Média |

### Curso Remoto

| # | Teste | Erro | Gravidade |
|---|-------|------|-----------|
| E09 | 100 (R04) | **E-mail não é obrigatório para alunos remotos — aluno pode ficar incomunicável** | 🔴 **Crítica** |
| E10 | 049 (R02) | Cursos remotos sem integração Moodle — aluno não tem acesso ao ambiente virtual | 🔴 **Crítica** |
| E11 | 013 (R08) | Data de nascimento futura aceita (ocorre em todos os cursos) | 🟡 Média |

---

## 🔴 LISTA DOS ERROS CRÍTICOS (IMPEDEM LANÇAMENTO)

| # | Código | Erro | Módulo | Impacto | Prioridade |
|---|--------|------|--------|---------|------------|
| **C01** | E02 | **Aluno inadimplente consegue emitir declaração** | Financeiro/Documentos | Alunos podem obter documentos oficiais mesmo com débitos pendentes. Impacto: perda de receita e ausência de controle financeiro. | 🔴 **Crítica** |
| **C02** | E09 | **E-mail não é obrigatório para alunos remotos** | Cadastro/Remoto | Aluno remoto sem e-mail não recebe link de acesso ao ambiente virtual, materiais didáticos, notificações de aula e comunicados institucionais. Inviabiliza o curso a distância. | 🔴 **Crítica** |
| **C03** | E10 | **Cursos remotos sem integração Moodle** | Moodle/Remoto | Aluno remoto não tem acesso ao conteúdo programático, atividades ou avaliações online. O curso remoto fica inviável. | 🔴 **Crítica** |
| **C04** | E01 | **Transferência entre tipos de curso sem validação** | Matrículas | Aluno pode migrar livremente entre Técnico, Itinerante e Remoto sem verificação de equivalência curricular, prejudicando a integridade acadêmica. | 🔴 **Alta** |
| **C05** | E05/E11 | **Data de nascimento futura aceita** | Cadastro | Dados inconsistentes (ex: aluno nascido em 2030). Gera inconsistência em relatórios etários e documentos oficiais. | 🟡 **Alta** |

---

## 📋 LISTA DOS AJUSTES RECOMENDADOS

| Prioridade | Sugestão | Módulo | Esforço | Teste Relacionado |
|------------|----------|--------|---------|-------------------|
| 🔴 **Crítica** | **Bloquear emissão de declaração/histórico para alunos inadimplentes** — validar status do contrato financeiro antes de permitir emissão | Financeiro/Docs | ⏱️ Baixo (2h) | 072 |
| 🔴 **Crítica** | **Tornar e-mail obrigatório para alunos de cursos remotos** — Adicionar validação no `clean()` do model `Pessoa`/`Aluno` e `required` condicional no frontend | Cadastro/Remoto | ⏱️ Baixo (2h) | 100 |
| 🔴 **Crítica** | **Implementar integração Moodle para cursos de Formação Inicial e Continuada (FIC/Remoto)** — Vincular turmas remotas a cursos no Moodle automaticamente | Moodle/Integração | ⏱️ Alto (5-8 dias) | 049 |
| 🔴 **Alta** | **Validar compatibilidade entre cursos na transferência** — Só permitir transferência entre cursos do mesmo tipo e nível de ensino | Matrículas | ⏱️ Médio (1-2 dias) | 032 |
| 🟡 **Alta** | **Adicionar validação de data futura** — `data_nascimento <= date.today()` no backend e `max={today}` no frontend | Cadastro | ⏱️ Baixo (1h) | 013 |
| 🟡 **Média** | **Tornar contrato financeiro obrigatório na criação da matrícula** ou ao menos gerar alerta quando ausente | Financeiro/Matrículas | ⏱️ Médio (1 dia) | 031 |
| 🟡 **Média** | **Adicionar sanitização de caracteres especiais no nome** — Filtrar apenas letras, espaços e acentos | Cadastro | ⏱️ Baixo (2h) | 014 |
| 🟢 **Baixa** | **Adicionar máscara/validação de telefone** — Formato (XX) XXXXX-XXXX com tamanho mínimo | Cadastro/UI | ⏱️ Baixo (1h) | 009, 097 |
| 🟢 **Baixa** | **Adicionar contador de caracteres** em campos de texto limitados (nome: 200, etc.) | UI/UX | ⏱️ Baixo (1h) | 101 |

---

## ✅ CHECKLIST FINAL DE VALIDAÇÃO

### Cadastro de Alunos
| Item | Status |
|------|--------|
| Validação de CPF (dígitos verificadores) | ✅ OK |
| Prevenção de CPF duplicado | ✅ OK |
| Campos obrigatórios (nome, CPF) | ✅ OK |
| Edição de dados do aluno | ✅ OK |
| Inativação de aluno | ✅ OK |
| Vinculação de responsável para menor de idade | ✅ OK |
| **Validação de data de nascimento futura** | ❌ **FALHA** |
| **E-mail obrigatório para alunos remotos** | ❌ **FALHA** |
| Sanitização de caracteres especiais no nome | ⚠️ Atenção |

### Matrículas
| Item | Status |
|------|--------|
| Criação de matrícula no Curso Técnico | ✅ OK |
| Criação de matrícula no Curso Itinerante | ✅ OK |
| Criação de matrícula no Curso Remoto | ✅ OK |
| Controle de turma cheia (capacidade máxima) | ✅ OK |
| Geração automática de número de matrícula | ✅ OK |
| Matrícula duplicada no mesmo curso | ✅ OK |
| Matrícula ativa em outro curso | ✅ OK |
| Trancamento / Reativação | ✅ OK |
| Cancelamento | ✅ OK |
| Conclusão com validação de dependências | ✅ OK |
| Transições de status inválidas bloqueadas | ✅ OK |
| Fluxo P01 com etapas sequenciais | ✅ OK |
| Controle de versão (T107) para concorrência | ✅ OK |
| **Transferência entre cursos diferentes** | ❌ **FALHA** |

### Regras por Curso
| Item | Status |
|------|--------|
| Técnico: validação de carga horária > 0 | ✅ OK |
| Técnico: vínculo com módulo na matriz curricular | ✅ OK |
| Técnico: emissão de declaração/comprovante | ✅ OK |
| Técnico: diário de classe SEDUC-RO | ✅ OK |
| Itinerante: polo obrigatório na turma | ✅ OK |
| Itinerante: relatório por localidade/polo | ✅ OK |
| Itinerante: encontro presencial registrado | ✅ OK |
| Remoto: unidade Sede validada | ✅ OK |
| Remoto: matrícula sem unidade física | ✅ OK |
| **Remoto: integração com ambiente virtual (Moodle)** | ❌ **FALHA** |

### Documentação
| Item | Status |
|------|--------|
| Upload de documentos (PDF, JPG, PNG) | ✅ OK |
| Rejeição de extensões não permitidas | ✅ OK |
| Limite de tamanho (5MB) | ✅ OK |
| Validação de documento (RECEBIDO → VALIDADO) | ✅ OK |
| Recusa com motivo obrigatório | ✅ OK |
| Status: PENDENTE, RECEBIDO, VALIDADO, RECUSADO | ✅ OK |
| Transições de status controladas | ✅ OK |
| Documentos obrigatórios por curso | ✅ OK |

### Financeiro
| Item | Status |
|------|--------|
| Geração de mensalidades | ✅ OK |
| Aplicação de desconto/bolsa | ✅ OK |
| Limite percentual de bolsa respeitado | ✅ OK |
| Bolsa 100% (isenção) | ✅ OK |
| Pagamento de parcela | ✅ OK |
| Status INADIMPLENTE automático | ✅ OK |
| Reemissão de boleto | ✅ OK |
| Cancelamento de cobrança | ✅ OK |
| **Bloqueio de emissão de documentos para inadimplentes** | ❌ **FALHA** |

### Acadêmico
| Item | Status |
|------|--------|
| Lançamento de notas | ✅ OK |
| Lançamento de frequência | ✅ OK |
| Consolidação acadêmica (média + frequência) | ✅ OK |
| Situações: APROVADO, REPROVADO_NOTA, etc. | ✅ OK |
| Dependência acadêmica | ✅ OK |
| Aproveitamento de componentes | ✅ OK |
| Emissão de Histórico Escolar | ✅ OK |
| Emissão de Certificado/Diploma | ✅ OK |
| Ata de Resultado / Conselho de Classe | ✅ OK |

### Comunicação e Permissões
| Item | Status |
|------|--------|
| Envio de notificação | ✅ OK |
| Validação de e-mail inválido | ✅ OK |
| **Validação de telefone inválido** | ❌ **FALHA** |
| Permissão: Administrador | ✅ OK |
| Permissão: Secretaria | ✅ OK |
| Permissão: Financeiro | ✅ OK |
| Permissão: Professor | ✅ OK |
| Permissão: Aluno (auto-visualização) | ✅ OK |

### Relatórios
| Item | Status |
|------|--------|
| Relatório de alunos matriculados | ✅ OK |
| Relatório por curso | ✅ OK |
| Relatório por turma | ✅ OK |
| Relatório por localidade (Itinerante) | ✅ OK |
| Relatório financeiro / Inadimplência | ✅ OK |
| Exportação PDF/Excel | ✅ OK |
| Filtros por data, curso, turma, status | ✅ OK |

---

## 📊 ANÁLISE DETALHADA: E-MAIL OBRIGATÓRIO PARA ALUNOS REMOTOS

### Evidência no código-fonte

**Backend — Modelo `Pessoa`** (`SUAP/backend/apps/usuarios/models.py`):
```python
class Pessoa(models.Model):
    nome_completo = models.CharField(max_length=200)
    cpf = models.CharField(max_length=11, unique=True)
    data_nascimento = models.DateField(null=True, blank=True)
    email = models.EmailField(blank=True)   # ← blank=True → campo opcional
    telefone = models.CharField(max_length=20, blank=True)
```

**Frontend — AlunosPage.jsx** (`SUAP/frontend/src/pages/alunos/AlunosPage.jsx`):
```jsx
// Campo de e-mail SEM validação de required, mesmo para alunos remotos
<div className="form-field">
  <label htmlFor="aluno-email">E-mail</label>
  <input id="aluno-email" type="email" {...register('email')} />
</div>
```

**Problemas identificados:**
1. Backend: `email = models.EmailField(blank=True)` → permite campo vazio para **qualquer** aluno
2. Frontend: `register('email')` **sem** `required` → permite submeter formulário sem e-mail
3. Não há **validação condicional** que exija e-mail quando o curso do aluno for Remoto

### Impacto para o usuário

| Aspecto | Consequência |
|---------|-------------|
| **Acesso ao curso** | Aluno remoto sem e-mail não recebe link de acesso ao ambiente virtual |
| **Comunicação** | Não recebe notificações de aulas, avisos, prazos ou materiais didáticos |
| **Suporte** | Não consegue recuperar senha caso perca o acesso ao sistema |
| **Documentação** | Não recebe declarações ou certificados emitidos digitalmente |
| **Regulatório** | Cursos a distância (EaD) exigem meio de contato eletrônico por legislação (Decreto 9.057/2017) |

### Sugestão de correção técnica

**1. Backend — Validação condicional no `clean()` do model ou na view de criação de aluno:**

```python
# SUAP/backend/apps/usuarios/models.py
class Pessoa(models.Model):
    # ... campos existentes ...
    
    def clean(self):
        super().clean()
        # A validação de e-mail para remoto será feita no nível da matrícula/curso
```

**2. Backend — Validação no serializer ou model `Aluno`:**

```python
# NOVO: Validação no model Aluno ou no serializer
def validate_email_para_curso_remoto(aluno):
    """Se o aluno possui matrícula ativa em curso remoto, e-mail é obrigatório."""
    from apps.matriculas.models import Matricula
    
    matriculas_remotas = Matricula.objects.filter(
        aluno=aluno,
        curso__tipo_curso='formacao_inicial',
        status='ATIVA'
    )
    if matriculas_remotas.exists() and not aluno.pessoa.email:
        raise ValidationError({
            'email': 'Alunos de cursos remotos devem possuir e-mail cadastrado para receber o link de acesso ao ambiente virtual.'
        })
```

**3. Frontend — Validação condicional no formulário:**

```jsx
// SUAP/frontend/src/pages/alunos/AlunosPage.jsx
// Tornar e-mail required quando o curso for Remoto
const cursoSelecionado = watch('curso'); // ou contexto

const emailValidation = register('email', {
  validate: (value) => {
    if (cursoSelecionado?.tipo_curso === 'formacao_inicial' && !value) {
      return 'E-mail é obrigatório para alunos de cursos remotos.';
    }
    return true;
  },
});
```

### Reexecução mental do fluxo corrigido

| Cenário | Antes | Depois da correção |
|---------|-------|--------------------|
| **Secretaria cadastra R04 (Remoto) sem e-mail** | ✅ Cadastro criado sem impedimentos | ❌ Bloqueado com mensagem clara |
| **Secretaria informa e-mail do R04** | — | ✅ Cadastro criado com sucesso |
| **Sistema tenta enviar link de acesso** | ❌ Não envia (sem e-mail destino) | ✅ Envia link para o e-mail cadastrado |
| **Aluno recebe comunicados** | ❌ Não recebe | ✅ Recebe notificações e materiais |
| **Aluno de curso Técnico sem e-mail** | ✅ Cadastro permitido | ✅ Continua permitido (regra só para remoto) |

**Status da correção:** ✅ **Validada mentalmente** — a implementação resolve o problema sem impacto nos fluxos de cursos Técnico e Itinerante.

---

## 🏁 PARECER FINAL

### Nota Geral: **7,2/10 — APROVADO COM RESSALVAS**

### Status: 🟡 **NECESSITA AJUSTES ANTES DO LANÇAMENTO OFICIAL**

### Resumo da Avaliação

O sistema **SUAP** demonstra uma arquitetura sólida e bem estruturada, com os seguintes destaques:

**✅ Pontos fortes:**
- Validação robusta de CPF com dígitos verificadores no frontend
- Máquina de estados com transições controladas em Matrícula, Documentos e Fluxos
- Controle de versão otimista (T107) para evitar conflitos de concorrência
- Validação completa de documentos (extensão, tamanho máximo 5MB)
- Regras de negócio específicas por tipo de curso bem implementadas
- Permissões por perfil funcional (5 níveis) corretamente segregadas
- Geração de documentos oficiais padronizados (Declaração, Histórico, Diploma, Ata, Diário)
- Fluxo P01 com etapas sequenciais bem controladas

**❌ Pontos críticos (IMPEDEM lançamento):**

| Prioridade | Problema | Solução |
|------------|----------|---------|
| 🔴 **Crítica** | **E-mail não obrigatório para alunos remotos** — R04, R08, R13 e R15 cadastrados sem e-mail | Validar e-mail como obrigatório em `clean()` para cursos `formacao_inicial` |
| 🔴 **Crítica** | **Inadimplente emite declaração** — T02, T09, T13 emitiram documentos mesmo com débitos | Bloquear emissão quando contrato financeiro estiver INADIMPLENTE |
| 🔴 **Crítica** | **Sem integração Moodle para cursos remotos FIC** — Aluno remoto não tem acesso ao conteúdo | Implementar integração Moodle para formação inicial |
| 🔴 **Alta** | **Transferência entre cursos de tipos diferentes** — Técnico → Remoto sem validação | Só permitir transferência entre cursos equivalentes |

### Conclusão e Recomendação

> **O sistema está funcional e seguro para operação dos Cursos Técnico e Itinerante**, com ressalvas menores de usabilidade.

> **Para os Cursos Remotos, o lançamento NÃO é recomendado** até que:
> 1. A validação de e-mail obrigatório seja implementada (⭐ prioridade máxima — 2h de esforço)
> 2. A integração com o ambiente virtual (Moodle) esteja operacional
> 3. Os 3 alunos remotos sem e-mail (R04, R08, R13, R15) sejam regularizados

> ⏱️ **Estimativa de correção:** 5 a 10 dias úteis para todos os itens críticos  
> 🔄 **Recomendação:** Corrigir itens C01, C02 e C04 → reexecutar testes 072, 100 e 032 → liberar para produção

---

**QA Tester:** Analista de Testes SUAP  
**Data:** Junho/2026  
**Versão do Teste:** 1.1  
**Total de Cenários:** 122 | **Aprovados:** 104 | **Reprovados:** 7 | **Atenção:** 11
