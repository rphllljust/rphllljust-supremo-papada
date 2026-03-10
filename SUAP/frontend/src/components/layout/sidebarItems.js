import {
  LayoutDashboard,
  Rocket,
  FileText,
  Settings,
  GraduationCap,
  FlaskConical,
  Briefcase,
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
          unavailable('documentos', 'Documentos', {
            description: 'O modulo de documentos ainda nao foi portado para o frontend. O acesso ao template Django foi bloqueado.',
          }),
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
    id: 'pesquisa',
    type: 'group',
    label: 'Pesquisa',
    icon: FlaskConical,
    items: [
      {
        id: 'pesquisa-editais',
        type: 'group',
        label: 'Editais',
        items: [
          unavailable('pesquisa-editais', 'Editais'),
          unavailable('pesquisa-editais-resultado-final', 'Resultado Final'),
          unavailable('pesquisa-editais-resultado-parcial', 'Resultado Parcial'),
        ],
      },
      {
        id: 'pesquisa-projetos',
        type: 'group',
        label: 'Projetos',
        items: [
          unavailable('pesquisa-projetos-meus-projetos', 'Meus Projetos'),
          unavailable('pesquisa-projetos-meus-recursos', 'Meus Recursos'),
          unavailable('pesquisa-projetos-submeter-projetos', 'Submeter Projetos'),
          unavailable('pesquisa-projetos-tornar-se-avaliador', 'Tornar-se Avaliador'),
        ],
      },
      {
        id: 'pesquisa-declaracoes',
        type: 'group',
        label: 'Declaracoes',
        items: [
          unavailable('pesquisa-declaracoes-avaliador-de-projetos', 'Avaliador de Projetos'),
        ],
      },
      {
        id: 'pesquisa-editora',
        type: 'group',
        label: 'Editora',
        items: [
          unavailable('pesquisa-editora-submissoes', 'Submissoes'),
          unavailable('pesquisa-editora-doacoes-realizadas', 'Doacoes Realizadas'),
        ],
      },
      {
        id: 'pesquisa-laboratorios',
        type: 'group',
        label: 'Laboratorios Multiusuario',
        items: [
          unavailable('pesquisa-laboratorios-multiusuario-laboratorios', 'Laboratorios'),
          unavailable('pesquisa-laboratorios-multiusuario-minhas-solicitacoes', 'Minhas Solicitacoes'),
        ],
      },
      {
        id: 'pesquisa-incubadoras',
        type: 'group',
        label: 'Incubadoras Tecnologicas',
        items: [
          unavailable('pesquisa-incubadoras-tecnologicas-incubadoras-tecnologicas', 'Incubadoras Tecnologicas'),
          unavailable('pesquisa-incubadoras-tecnologicas-equipe-tecnica-eta', 'Equipe Tecnica (ETA)'),
        ],
      },
      {
        id: 'pesquisa-relatorios',
        type: 'group',
        label: 'Relatorios',
        items: [
          unavailable('pesquisa-relatorios-empreendimentos-incubados', 'Empreendimentos Incubados'),
        ],
      },
      {
        id: 'pesquisa-cnpq',
        type: 'group',
        label: 'CNPQ',
        items: [
          unavailable('pesquisa-cnpq-estatistica-importacoes-lattes', 'Estatistica de Importacoes do Lattes'),
          unavailable('pesquisa-cnpq-indicadores', 'Indicadores'),
          unavailable('pesquisa-cnpq-producao-por-campus', 'Producao por Campus'),
          unavailable('pesquisa-cnpq-producao-por-servidor', 'Producao por Servidor'),
          unavailable('pesquisa-cnpq-relatorio-importacoes-lattes', 'Relatorio de Importacoes do Lattes'),
          unavailable('pesquisa-cnpq-titulacao-area-atuacao', 'Titulacao e Area de Atuacao'),
        ],
      },
      unavailable('pesquisa-variaveis-de-gestao', 'Variaveis de Gestao'),
    ],
  },
  {
    id: 'extensao',
    type: 'group',
    label: 'Extensao',
    icon: Briefcase,
    items: [
      {
        id: 'extensao-convenios',
        type: 'group',
        label: 'Convenios',
        items: [
          unavailable('convenios', 'Convenios'),
        ],
      },
      {
        id: 'estagio-e-afins',
        type: 'group',
        label: 'Estagio e Afins',
        items: [
          unavailable('extensao-estagio-afins-aprendizagens', 'Aprendizagens'),
          { id: 'estagios-extensao', type: 'link', label: 'Estagios', to: '/estagio' },
        ],
      },
      {
        id: 'extensao-projetos',
        type: 'group',
        label: 'Projetos',
        items: [
          unavailable('extensao-projetos-editais', 'Editais'),
          unavailable('extensao-projetos-meus-projetos', 'Meus Projetos'),
          unavailable('extensao-projetos-meus-recursos', 'Meus Recursos'),
          unavailable('extensao-projetos-projetos', 'Projetos'),
          unavailable('extensao-projetos-submeter-projetos', 'Submeter Projetos'),
          unavailable('extensao-projetos-tornar-se-avaliador', 'Tornar-se Avaliador'),
        ],
      },
      {
        id: 'demandas-externas',
        type: 'group',
        label: 'Demandas Externas',
        items: [
          unavailable('extensao-demandas-externas-demandas', 'Demandas'),
        ],
      },
      unavailable('extensao-nepp', 'Nucleos de Extensao e Pratica Profissional - NEPP'),
      unavailable('extensao-variaveis-de-gestao', 'Variaveis de Gestao'),
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
        to: '/servidores',
        activePrefixes: ['/servidores'],
      },
      { id: 'setores', type: 'link', label: 'Setores', to: '/setores' },
      {
        id: 'administracao-pessoal',
        type: 'group',
        label: 'Administracao de Pessoal',
        items: [
          unavailable('organograma', 'Organograma'),
          unavailable('ponto', 'Ponto'),
          unavailable('solicitacoes', 'Solicitacoes'),
          unavailable('acumulo-de-cargo', 'Acumulo de Cargo'),
          unavailable('acompanhamento-funcional', 'Acompanhamento Funcional'),
        ],
      },
      {
        id: 'desenvolvimento-pessoal',
        type: 'group',
        label: 'Desenvolvimento de Pessoal',
        items: [
          unavailable('remocao-interna', 'Remocao Interna'),
          unavailable('avaliacao-de-desempenho', 'Avaliacao de Desempenho'),
          unavailable('licenca-capacitacao', 'Licenca Capacitacao'),
          unavailable('pdp', 'PDP'),
          {
            id: 'docentes',
            type: 'link',
            label: 'Docentes',
            to: { pathname: '/usuarios', search: '?tipo=PROFESSOR' },
            activePrefixes: ['/usuarios'],
          },
        ],
      },
      unavailable('atencao-a-saude-do-servidor', 'Atencao a Saude do Servidor'),
      {
        id: 'cadastros-pessoas',
        type: 'group',
        label: 'Cadastros',
        items: [
          { id: 'instituicoes', type: 'link', label: 'Instituicoes', to: '/unidades' },
        ],
      },
      unavailable('variaveis-de-gestao-pessoas', 'Variaveis de Gestao'),
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
    ],
  },
]