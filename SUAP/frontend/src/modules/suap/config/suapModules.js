export const SUAP_PENDING = 'pendente de confirma\u00e7\u00e3o no treinamento'

export const publicSuapServices = [
  { group: 'Acessos', source: 'treinamento p\u00fablico', confirmed: true, items: [
    { title: 'Login', path: '/suap/acessos/login', externalUrl: 'https://treinamento.suapdevs.ifrn.edu.br/accounts/login/', status: 'confirmado_publico' },
    { title: 'Alterar Senha', path: '/suap/acessos/alterar-senha', externalUrl: 'https://treinamento.suapdevs.ifrn.edu.br/comum/alterar_senha/', status: 'confirmado_publico' },
    { title: 'Acesso do respons\u00e1vel', path: '/suap/acessos/acesso-responsavel', externalUrl: 'https://treinamento.suapdevs.ifrn.edu.br/', status: 'confirmado_publico' },
  ] },
  { group: 'Auditoria', source: 'treinamento p\u00fablico', confirmed: true, items: [
    { title: 'Estoque de Monitoramentos', path: '/suap/auditoria/estoque-monitoramentos', externalUrl: 'https://treinamento.suapdevs.ifrn.edu.br/', status: 'confirmado_publico' },
    { title: 'Estoque de Recomenda\u00e7\u00f5es', path: '/suap/auditoria/estoque-recomendacoes', externalUrl: 'https://treinamento.suapdevs.ifrn.edu.br/', status: 'confirmado_publico' },
  ] },
  { group: 'Consultas gerais', source: 'treinamento p\u00fablico', confirmed: true, items: [
    { title: 'Processos F\u00edsicos', path: '/suap/consultas/processos-fisicos', externalUrl: 'https://treinamento.suapdevs.ifrn.edu.br/', status: 'confirmado_publico' },
    { title: 'Processos Eletr\u00f4nicos', path: '/suap/consultas/processos-eletronicos', externalUrl: 'https://treinamento.suapdevs.ifrn.edu.br/', status: 'confirmado_publico' },
    { title: 'Contratos', path: '/suap/consultas/contratos', externalUrl: 'https://treinamento.suapdevs.ifrn.edu.br/', status: 'confirmado_publico' },
    { title: 'Eventos', path: '/suap/consultas/eventos', externalUrl: 'https://treinamento.suapdevs.ifrn.edu.br/', status: 'confirmado_publico' },
    { title: 'Farol de Desempenho', path: '/suap/consultas/farol-desempenho', externalUrl: 'https://treinamento.suapdevs.ifrn.edu.br/', status: 'confirmado_publico' },
    { title: 'Servidores PGD', path: '/suap/consultas/servidores-pgd', externalUrl: 'https://treinamento.suapdevs.ifrn.edu.br/', status: 'confirmado_publico' },
  ] },
  { group: 'Ensino', source: 'treinamento p\u00fablico', confirmed: true, items: [
    { title: 'Planos de Ensino', path: '/suap/ensino/planos-ensino', externalUrl: 'https://treinamento.suapdevs.ifrn.edu.br/', status: 'confirmado_publico' },
    { title: 'Valida\u00e7\u00e3o de assinatura digital', path: '/suap/ensino/validacao-assinatura-digital', externalUrl: 'https://treinamento.suapdevs.ifrn.edu.br/', status: 'confirmado_publico' },
    { title: 'Certificados de Minicursos', path: '/suap/ensino/certificados-minicursos', externalUrl: 'https://treinamento.suapdevs.ifrn.edu.br/', status: 'confirmado_publico' },
    { title: 'Certifica\u00e7\u00e3o ENEM', path: '/suap/ensino/certificacao-enem', externalUrl: 'https://treinamento.suapdevs.ifrn.edu.br/', status: 'confirmado_publico' },
    { title: 'Registro de diplomas', path: '/suap/ensino/registro-diplomas', externalUrl: 'https://treinamento.suapdevs.ifrn.edu.br/', status: 'confirmado_publico' },
    { title: 'Certifica\u00e7\u00e3o ENCCEJA / ENEM', path: '/suap/ensino/certificacao-encceja-enem', externalUrl: 'https://treinamento.suapdevs.ifrn.edu.br/', status: 'confirmado_publico' },
    { title: 'Relat\u00f3rios Individuais de Trabalho', path: '/suap/ensino/relatorios-individuais-trabalho', externalUrl: 'https://treinamento.suapdevs.ifrn.edu.br/', status: 'confirmado_publico' },
  ] },
  { group: 'Extens\u00e3o', source: 'treinamento p\u00fablico', confirmed: true, items: [
    { title: 'Avalia\u00e7\u00e3o de Est\u00e1gio', path: '/suap/extensao/avaliacao-estagio', externalUrl: 'https://treinamento.suapdevs.ifrn.edu.br/', status: 'confirmado_publico' },
    { title: 'Demandas da Comunidade', path: '/suap/extensao/demandas-comunidade', externalUrl: 'https://treinamento.suapdevs.ifrn.edu.br/', status: 'confirmado_publico' },
  ] },
  { group: 'Ferramentas', source: 'treinamento p\u00fablico', confirmed: true, items: [
    { title: 'Verifica\u00e7\u00e3o de autentica\u00e7\u00e3o de documento', path: '/suap/ferramentas/verificacao-autenticacao-documento', externalUrl: 'https://treinamento.suapdevs.ifrn.edu.br/', status: 'confirmado_publico' },
  ] },
  { group: 'Gest\u00e3o de Pessoas', source: 'treinamento p\u00fablico', confirmed: true, items: [
    { title: 'Indicadores', path: '/suap/gestao-pessoas/indicadores', externalUrl: 'https://treinamento.suapdevs.ifrn.edu.br/', status: 'confirmado_publico' },
  ] },
  { group: 'Pesquisa', source: 'treinamento p\u00fablico', confirmed: true, items: [
    { title: 'Seja um Parecerista', path: '/suap/pesquisa/seja-parecerista', externalUrl: 'https://treinamento.suapdevs.ifrn.edu.br/', status: 'confirmado_publico' },
  ] },
  { group: 'Sobre o Suap', source: 'treinamento p\u00fablico', confirmed: true, items: [
    { title: 'Documenta\u00e7\u00e3o', path: '/suap/sobre/documentacao', externalUrl: 'https://suap.ifrn.edu.br/comum/documentacao/', status: 'confirmado_publico' },
    { title: 'Design System', path: '/suap/sobre/design-system', externalUrl: 'https://treinamento.suapdevs.ifrn.edu.br/', status: 'confirmado_publico' },
    { title: 'Atualiza\u00e7\u00f5es do sistema', path: '/suap/sobre/atualizacoes-sistema', externalUrl: 'https://treinamento.suapdevs.ifrn.edu.br/', status: 'confirmado_publico' },
  ] },
  { group: 'Transpar\u00eancia', source: 'treinamento p\u00fablico', confirmed: true, items: [
    { title: 'Dados Abertos', path: '/suap/transparencia/dados-abertos', externalUrl: 'https://dados.ifrn.edu.br/', status: 'confirmado_publico' },
  ] },
]

export const internalSuapModules = [
  { name: 'Administra\u00e7\u00e3o', status: SUAP_PENDING, confirmed: false, source: 'acesso autenticado n\u00e3o dispon\u00edvel', submodules: [{ name: SUAP_PENDING, status: SUAP_PENDING, enabled: false }] },
  { name: 'Ensino', status: SUAP_PENDING, confirmed: false, source: 'acesso autenticado n\u00e3o dispon\u00edvel', submodules: [{ name: SUAP_PENDING, status: SUAP_PENDING, enabled: false }] },
  { name: 'Gest\u00e3o Institucional', status: SUAP_PENDING, confirmed: false, source: 'acesso autenticado n\u00e3o dispon\u00edvel', submodules: [{ name: SUAP_PENDING, status: SUAP_PENDING, enabled: false }] },
  { name: 'Atividades Estudantis', status: SUAP_PENDING, confirmed: false, source: 'acesso autenticado n\u00e3o dispon\u00edvel', submodules: [{ name: SUAP_PENDING, status: SUAP_PENDING, enabled: false }] },
  { name: 'Tecnologia da Informa\u00e7\u00e3o', status: SUAP_PENDING, confirmed: false, source: 'acesso autenticado n\u00e3o dispon\u00edvel', submodules: [{ name: SUAP_PENDING, status: SUAP_PENDING, enabled: false }] },
]

export const suapModules = publicSuapServices.map((group) => ({
  title: group.group,
  path: group.items[0]?.path?.split('/').slice(0, 3).join('/') || '/suap',
  status: group.confirmed ? 'confirmado_publico' : SUAP_PENDING,
  children: group.items,
}))

export function findSuapPage(pathname) {
  for (const module of suapModules) {
    for (const page of module.children) {
      if (page.path === pathname) return { module, page }
    }
  }
  return null
}
