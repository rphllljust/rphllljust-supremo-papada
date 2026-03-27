import AlertMessage from '@/modules/configurar-curso/components/AlertMessage'

function Block({ title, children }) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <h3 className="text-base font-semibold text-slate-900">{title}</h3>
      <div className="mt-3 text-sm text-slate-700">{children}</div>
    </section>
  )
}

function KeyValue({ label, value }) {
  return (
    <div className="grid grid-cols-1 gap-1 border-b border-slate-100 py-1.5 sm:grid-cols-[180px_1fr]">
      <strong className="font-semibold text-slate-600">{label}</strong>
      <span>{value || '-'}</span>
    </div>
  )
}

export default function EtapaResumoFinal({ summaryPayload, onRefreshSummary, isRefreshing, canConclude }) {
  const resumo = summaryPayload?.resumo || null

  return (
    <section className="grid gap-6">
      <AlertMessage
        type="info"
        title="Etapa 7"
        message="Revise os dados consolidados antes da conclusao. O sistema validara matriz vinculada, componentes e coordenadores obrigatorios."
      />

      <div className="flex justify-end">
        <button
          type="button"
          onClick={onRefreshSummary}
          disabled={isRefreshing}
          className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-60"
        >
          {isRefreshing ? 'Atualizando resumo...' : 'Atualizar resumo'}
        </button>
      </div>

      {!resumo ? (
        <AlertMessage type="warning" message="Gere o resumo para visualizar os dados consolidados desta configuracao." />
      ) : (
        <>
          <Block title="Estrutura de curso">
            <KeyValue label="ID" value={resumo.estrutura_curso?.id} />
            <KeyValue label="Nome" value={resumo.estrutura_curso?.nome} />
            <KeyValue label="Descricao" value={resumo.estrutura_curso?.descricao} />
          </Block>

          <Block title="Matriz curricular">
            <KeyValue label="ID" value={resumo.matriz_curricular?.id} />
            <KeyValue label="Nome" value={resumo.matriz_curricular?.nome} />
            <KeyValue label="Codigo" value={resumo.matriz_curricular?.codigo} />
            <KeyValue label="Versao" value={resumo.matriz_curricular?.versao} />
            <KeyValue label="Carga horaria" value={resumo.matriz_curricular?.carga_horaria_total} />
          </Block>

          <Block title="Curso">
            <KeyValue label="ID" value={resumo.curso?.id} />
            <KeyValue label="Codigo" value={resumo.curso?.codigo} />
            <KeyValue label="Nome" value={resumo.curso?.nome} />
            <KeyValue label="Nome curto" value={resumo.curso?.nome_curto} />
            <KeyValue label="Modalidade" value={resumo.curso?.modalidade} />
            <KeyValue label="Situacao" value={resumo.curso?.situacao} />
          </Block>

          <Block title={`Componentes vinculados (${resumo.componentes_vinculados?.length || 0})`}>
            <ul className="list-disc space-y-1 pl-5">
              {(resumo.componentes_vinculados || []).map((item) => (
                <li key={item.id}>{`${item.componente_codigo} - ${item.componente_nome} | Periodo ${item.periodo} | Ordem ${item.ordem}`}</li>
              ))}
            </ul>
          </Block>

          <Block title={`Pre-requisitos (${resumo.pre_requisitos?.length || 0})`}>
            <ul className="list-disc space-y-1 pl-5">
              {(resumo.pre_requisitos || []).map((item) => (
                <li key={item.id}>{`${item.componente_nome} <- ${item.requisito_nome}`}</li>
              ))}
            </ul>
          </Block>

          <Block title={`Co-requisitos (${resumo.co_requisitos?.length || 0})`}>
            <ul className="list-disc space-y-1 pl-5">
              {(resumo.co_requisitos || []).map((item) => (
                <li key={item.id}>{`${item.componente_nome} <-> ${item.requisito_nome}`}</li>
              ))}
            </ul>
          </Block>

          <Block title={`Coordenadores (${resumo.coordenadores?.length || 0})`}>
            <ul className="list-disc space-y-1 pl-5">
              {(resumo.coordenadores || []).map((item) => (
                <li key={item.id}>{`${item.coordenador_nome} | Principal: ${item.principal ? 'Sim' : 'Nao'} | Vigencia: ${item.inicio_vigencia}${item.fim_vigencia ? ` a ${item.fim_vigencia}` : ''}`}</li>
              ))}
            </ul>
          </Block>

          {!canConclude ? (
            <AlertMessage
              type="warning"
              message="Ainda existem validacoes pendentes para conclusao. Revise as etapas obrigatorias e atualize o resumo."
            />
          ) : null}
        </>
      )}
    </section>
  )
}
