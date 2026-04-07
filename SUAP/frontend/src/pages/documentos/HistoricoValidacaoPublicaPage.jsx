import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { CheckCircle2, Search, ShieldAlert } from 'lucide-react'
import { useParams } from 'react-router-dom'

import { historicosApi } from '@/api/endpoints'

export default function HistoricoValidacaoPublicaPage() {
  const params = useParams()
  const [uuidInput, setUuidInput] = useState(params.uuid || '')
  const [submittedUuid, setSubmittedUuid] = useState(params.uuid || '')

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['validacao-historico-publica', submittedUuid],
    queryFn: async () => {
      try {
        const response = await historicosApi.validarPublico(submittedUuid)
        return response.data
      } catch (_error) {
        const responseByCode = await historicosApi.validarPublicoPorCodigo(submittedUuid)
        return responseByCode.data
      }
    },
    enabled: Boolean(submittedUuid),
    retry: false,
  })

  const statusChip = useMemo(() => {
    const autenticidade = data?.autenticidade || ''
    if (autenticidade === 'VALIDO') return { label: 'Valido', className: 'badge badge--success' }
    if (autenticidade === 'CANCELADO') return { label: 'Cancelado', className: 'badge badge--danger' }
    if (autenticidade === 'SUBSTITUIDO') return { label: 'Substituido', className: 'badge badge--warning' }
    return { label: 'Invalido', className: 'badge badge--danger' }
  }, [data?.autenticidade])

  return (
    <div className="page page--wide">
      <div className="page-header">
        <div>
          <h1 className="page-title">Validacao Publica de Historico Escolar</h1>
          <p className="page-subtitle">Autenticidade por UUID/codigo de validacao do documento institucional.</p>
        </div>
      </div>

      <section className="entity-details-panel">
        <div className="entity-details-panel__header">
          <h2>Consultar documento</h2>
        </div>
        <form
          onSubmit={(event) => {
            event.preventDefault()
            setSubmittedUuid(uuidInput.trim())
          }}
          style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}
        >
          <input
            type="text"
            value={uuidInput}
            onChange={(event) => setUuidInput(event.target.value)}
            placeholder="UUID do historico"
          />
          <button className="btn btn--primary" type="submit" disabled={!uuidInput.trim()}>
            <Search size={16} /> Validar
          </button>
        </form>
      </section>

      {isLoading ? <div className="alert">Consultando documento...</div> : null}
      {isError ? <div className="alert alert--error">{error?.response?.data?.detail || 'Documento nao encontrado.'}</div> : null}

      {data ? (
        <section className="entity-details-panel" style={{ marginTop: '1rem' }}>
          <div className="entity-details-panel__header">
            <h2>Resultado da validacao</h2>
            <span className={statusChip.className} style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}>
              {data.autenticidade === 'VALIDO' ? <CheckCircle2 size={14} /> : <ShieldAlert size={14} />}
              {statusChip.label}
            </span>
          </div>

          {data.documento_encontrado ? (
            <div className="entity-details-grid">
              <div className="entity-details-item"><span className="entity-details-item__label">Aluno</span><span className="entity-details-item__value">{data.nome_aluno}</span></div>
              <div className="entity-details-item"><span className="entity-details-item__label">CPF</span><span className="entity-details-item__value">{data.cpf_mascarado}</span></div>
              <div className="entity-details-item"><span className="entity-details-item__label">Curso Tecnico</span><span className="entity-details-item__value">{data.curso_tecnico}</span></div>
              <div className="entity-details-item"><span className="entity-details-item__label">Eixo Tecnologico</span><span className="entity-details-item__value">{data.eixo_tecnologico || '-'}</span></div>
              <div className="entity-details-item"><span className="entity-details-item__label">Carga Horaria Total</span><span className="entity-details-item__value">{data.carga_horaria_total}</span></div>
              <div className="entity-details-item"><span className="entity-details-item__label">Situacao Final</span><span className="entity-details-item__value">{data.situacao_final}</span></div>
              <div className="entity-details-item"><span className="entity-details-item__label">Data Conclusao</span><span className="entity-details-item__value">{data.data_conclusao || '-'}</span></div>
              <div className="entity-details-item"><span className="entity-details-item__label">Numero Registro</span><span className="entity-details-item__value">{data.numero_registro}</span></div>
              <div className="entity-details-item"><span className="entity-details-item__label">Versao</span><span className="entity-details-item__value">{data.versao}</span></div>
              <div className="entity-details-item"><span className="entity-details-item__label">Hash Resumido</span><span className="entity-details-item__value">{data.hash_resumido}</span></div>
              <div className="entity-details-item"><span className="entity-details-item__label">Data Emissao</span><span className="entity-details-item__value">{data.data_emissao || '-'}</span></div>
              <div className="entity-details-item"><span className="entity-details-item__label">Status Documento</span><span className="entity-details-item__value">{data.status_documento}</span></div>
            </div>
          ) : (
            <div className="alert alert--error">Documento nao encontrado.</div>
          )}
        </section>
      ) : null}
    </div>
  )
}
