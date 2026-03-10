import {
  LayoutDashboard,
  Rocket,
  FileText,
  Settings,
  GraduationCap,
  Users,
  Power,
} from 'lucide-react'

function unavailable(slug, label, extra = {}) {
  return {
    id: slug,
    type: 'link',
    to: `/indisponivel/${slug}`,
    label,
    activePrefixes: [`/indisponivel/${slug}`],
    state: {
      title: label,
      status: extra.status || 'indisponivel',
      description: extra.description || 'Este item do SUAP ainda nao foi integrado ao frontend React.',
    },
  }
}

function activation(slug, label) {
  return unavailable(slug, label, {
    status: 'ativacao',
    description: 'Este modulo aparece no menu legado, mas ainda esta em fase de ativacao no frontend do SUAP.',
  })
}

function rhUnavailable(slug, label, extra = {}) {
  return {
    id: `rh-${slug}`,
    type: 'link',
    to: `/rh/${slug}`,
    label,
    activePrefixes: [`/rh/${slug}`],
    state: {
      title: label,
      status: extra.status || 'indisponivel',
      description: extra.description || 'Esta funcionalidade de Gestao de Pessoas ainda nao foi implementada no frontend.',
    },
  }
}

export const sidebarItems = [
  {
    id: 'inicio',
    type: 'link',
    label: 'Inicio',
    icon: LayoutDashboard,
    to: '/dashboard',
    exact: true,
  },
  {
    id: 'acesso-rapido',
    type: 'group',
    label: 'Acesso Rapido',
    icon: Rocket,
    items: [
      { id: 'cursos', type: 'link', label: 'Cursos', to: '/cursos' },
      { id: 'turmas', type: 'link', label: 'Turmas', to: '/turmas' },
      { id: 'matriculas', type: 'link', label: 'Matriculas', to: '/matriculas' },
      { id: 'notas', type: 'link', label: 'Notas', to: '/notas' },
      { id: 'frequencia', type: 'link', label: 'Frequencia', to: '/frequencia' },
      { id: 'agenda', type: 'link', label: 'Agenda', to: '/agenda' },
      unavailable('diario-classe', 'Diario de Classe'),
      { id: 'ata-professores', type: 'link', label: 'Ata dos Professores', to: '/ata-professores' },
    ],
  },
  {
    id: 'documentos-processos',
    type: 'group',
    label: 'Documentos/Processos',
    icon: FileText,
    items: [
      {
        id: 'documentos-eletronicos',
        type: 'group',
        label: 'Documentos Eletronicos',
        items: [
          unavailable('documentos-eletronicos-dashboard', 'Dashboard'),
          { id: 'documentos', type: 'link', label: 'Documentos', to: '/documentos' },
          unavailable('documentos-pessoais', 'Documentos Pessoais'),
          unavailable('documentos-pessoais-digitalizados', 'Documentos Pessoais Digitalizados'),
        ],
      },
      {
        id: 'processos-eletronicos',
        type: 'group',
        label: 'Processos Eletronicos',
        items: [
          { id: 'processos-lista', type: 'link', label: 'Processos', to: '/processos' },
          unavailable('requerimentos', 'Requerimentos'),
        ],
      },
      {
        id: 'processos-fisicos',
        type: 'group',
        label: 'Processos Fisicos',
        items: [
          unavailable('caixa-de-entrada-e-saida', 'Caixa de Entrada e Saida'),
          unavailable('caixa-de-tramitacao-externa', 'Caixa de Tramitacao Externa'),
          { id: 'arquivo-processos', type: 'link', label: 'Processos', to: '/arquivo' },
        ],
      },
      unavailable('minhas-permissoes', 'Minhas Permissoes'),
      unavailable('solitacoes-alteracao-nivel-acesso', 'Solitacoes de Alteracao de Nivel de Acesso'),
    ],
  },
  {
    id: 'gestao-sistema',
    type: 'group',
    label: 'Gestao e Sistema',
    icon: Settings,
    items: [
      { id: 'programa-gestao', type: 'link', label: 'Programa de Gestao', to: '/dashboard' },
      unavailable('administracao', 'Administracao', {
        description: 'O acesso ao Django admin foi bloqueado dentro deste frontend. Use uma tela interna quando ela for portada.',
      }),
      unavailable('auditoria', 'Auditoria'),
    ],
  },
  {
    id: 'ensino',
    type: 'group',
    label: 'Ensino',
    icon: GraduationCap,
    items: [
      {
        id: 'alunos-professores',
        type: 'group',
        label: 'Alunos e Professores',
        items: [
          { id: 'alunos-nav', type: 'link', label: 'Alunos', to: '/alunos' },
          {
            id: 'professores-nav',
            type: 'link',
            label: 'Professores',
            to: { pathname: '/usuarios', search: '?tipo=PROFESSOR' },
            activePrefixes: ['/usuarios'],
          },
        ],
      },
      unavailable('cadastros-gerais', 'Cadastros Gerais'),
      unavailable('dados-de-ensino', 'Dados de Ensino'),
      unavailable('certificados-enem', 'Certificados ENEM'),
      unavailable('comunicador', 'Comunicador'),
      { id: 'cursos-matrizes-componentes', type: 'link', label: 'Cursos, Matrizes e Componentes', to: '/cursos' },
      unavailable('diplomas-e-certificados', 'Diplomas e Certificados'),
      unavailable('ead', 'EAD'),
      { id: 'estagios-docentes', type: 'link', label: 'Estagios Docentes', to: '/estagio' },
      unavailable('etep', 'ETEP'),
      { id: 'painel-controle', type: 'link', label: 'Painel de Controle', to: '/dashboard' },
      unavailable('procedimentos-de-apoio', 'Procedimentos de Apoio'),
      { id: 'processos-seletivos', type: 'link', label: 'Processos Seletivos', to: '/inscricoes' },
      unavailable('relatorios-ensino', 'Relatorios'),
      { id: 'turmas-diarios', type: 'link', label: 'Turmas e Diarios', to: '/turmas' },
      unavailable('programas', 'Programas'),
      unavailable('atas-eletronicas', 'Atas Eletronicas'),
      unavailable('plano-de-oferta', 'Plano de Oferta'),
      unavailable('regulacao', 'Regulacao'),
      unavailable('migracao-de-dados', 'Migracao de dados'),
      unavailable('napne', 'Napne'),
      unavailable('variaveis-de-gestao', 'Variaveis de Gestao'),
      unavailable('acervo-academico', 'Acervo Academico'),
      unavailable('atividade-profissional-efetiva', 'Atividade Profissional Efetiva'),
      unavailable('planos-individuais-de-trabalho', 'Planos Individuais de Trabalho'),
      unavailable('laboratorios-remotos', 'Laboratorios Remotos'),
      unavailable('projetos-ensino', 'Projetos'),
      unavailable('ppc', 'PPC'),
      unavailable('pafc', 'PAFC'),
    ],
  },
  {
    id: 'gestao-pessoas',
    type: 'group',
    label: 'Gestao de Pessoas',
    icon: Users,
    items: [
      {
        id: 'servidores',
        type: 'link',
        label: 'Servidores',
        to: '/rh/servidores',
        activePrefixes: ['/rh/servidores'],
      },
      { id: 'setores', type: 'link', label: 'Setores', to: '/rh/setores', activePrefixes: ['/rh/setores'] },
      {
        id: 'administracao-pessoal',
        type: 'group',
        label: 'Administracao de Pessoal',
        items: [
          rhUnavailable('organograma', 'Organograma'),
          rhUnavailable('ponto', 'Ponto'),
          rhUnavailable('solicitacoes', 'Solicitacoes'),
          rhUnavailable('acumulo-de-cargo', 'Acumulo de Cargo'),
          rhUnavailable('acompanhamento-funcional', 'Acompanhamento Funcional'),
        ],
      },
      {
        id: 'desenvolvimento-pessoal',
        type: 'group',
        label: 'Desenvolvimento de Pessoal',
        items: [
          rhUnavailable('remocao-interna', 'Remocao Interna'),
          rhUnavailable('avaliacao-de-desempenho', 'Avaliacao de Desempenho'),
          rhUnavailable('licenca-capacitacao', 'Licenca Capacitacao'),
          rhUnavailable('pdp', 'PDP'),
          {
            id: 'docentes',
            type: 'link',
            label: 'Docentes',
            to: '/rh/docentes',
            activePrefixes: ['/rh/docentes'],
          },
        ],
      },
      rhUnavailable('atencao-a-saude-do-servidor', 'Atencao a Saude do Servidor'),
      {
        id: 'cadastros-pessoas',
        type: 'group',
        label: 'Cadastros',
        items: [
          { id: 'instituicoes', type: 'link', label: 'Instituicoes', to: '/rh/instituicoes', activePrefixes: ['/rh/instituicoes'] },
        ],
      },
      rhUnavailable('variaveis-de-gestao-pessoas', 'Variaveis de Gestao'),
    ],
  },
  {
    id: 'modulos-ativacao',
    type: 'group',
    label: 'Modulos em Ativacao',
    icon: Power,
    items: [
      activation('tecnologia-da-informacao', 'Tec. da Informacao (ativar)'),
      activation('desenvolvimento-institucional', 'Des. Institucional (ativar)'),
      activation('central-de-servicos', 'Central de Servicos (ativar)'),
      activation('internacionalizacao', 'Internacionalizacao (ativar)'),
      activation('atividades-estudantis', 'Atividades Estudantis (ativar)'),
      activation('comunicacao-social', 'Comunicacao Social (ativar)'),
      activation('seguranca-institucional', 'Seguranca Institucional (ativar)'),
      activation('pesquisa', 'Pesquisa (ativar)'),
      activation('extensao', 'Extensao (ativar)'),
    ],
  },
]