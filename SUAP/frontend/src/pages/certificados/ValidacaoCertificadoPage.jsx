import { useEffect, useMemo, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { Link, useLocation, useParams } from 'react-router-dom'

import { certificadosApi } from '@/api/endpoints'
import EntityDetailsPanel from '@/components/ui/EntityDetailsPanel'

function getErrorMessage(error, fallback) {
  const data = error?.response?.data
  if (!data) return fallback
  if (typeof data.detail === 'string') return data.detail
  const firstValue = Object.values(data)[0]
  return Array.isArray(firstValue) ? firstValue[0] : (firstValue || fallback)
}

export default function ValidacaoCertificadoPage() {
  const { codigo: codigoParam } = useParams()
  const location = useLocation()
  const isPublicRoute = useMemo(
    () => location.pathname.startsWith('/validar-certificado'),
    [location.pathname],
  )

  const [codigo, setCodigo] = useState('')
  const [resultado, setResultado] = useState(null)

  const validarMutation = useMutation({
    mutationFn: (valorCodigo) => certificadosApi.validarPublico(valorCodigo),
    onSuccess: (response) => {
      setResultado(response.data)
      toast.success('Validacao concluida.')
    },
    onError: (error) => {
      setResultado(null)
      toast.error(getErrorMessage(error, 'Nao foi possivel validar o certificado.'))
    },
  })

  useEffect(() => {
    if (!codigoParam) return
    const codigoInicial = codigoParam.trim().toUpperCase()
    setCodigo(codigoInicial)
    validarMutation.mutate(codigoInicial)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [codigoParam])

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Validacao Publica de Certificado</h1>
          <p className="page-subtitle">Consulta por codigo unico e QR Code institucional.</p>
        </div>
        {!isPublicRoute ? (
          <div className="page-header__actions">
            <Link to="/validar-certificado" className="btn btn--outline">
              Abrir validacao publica
            </Link>
          </div>
        ) : null}
      </div>

      <section className="form-panel">
        <div className="form-panel__body">
          <form
            className="form-panel__grid"
            onSubmit={(event) => {
              event.preventDefault()
              if (!codigo.trim()) {
                toast.error('Informe o codigo de validacao.')
                return
              }
              validarMutation.mutate(codigo.trim())
            }}
          >
            <div className="form-field form-field--full">
              <label>Codigo de validacao</label>
              <input
                type="text"
                value={codigo}
                placeholder="Ex: A1B2C3D4E5F6..."
                onChange={(event) => setCodigo(event.target.value.toUpperCase())}
              />
            </div>
            <div className="form-field form-field--full">
              <button type="submit" className="btn btn--primary" disabled={validarMutation.isPending}>
                {validarMutation.isPending ? 'Validando...' : 'Validar certificado'}
              </button>
            </div>
          </form>
        </div>
      </section>

      {resultado ? (
        <EntityDetailsPanel
          title={`Certificado ${resultado.numero_certificado || ''}`}
          subtitle={`Status de validade: ${resultado.status_validade || ''}`}
          fields={[
            { label: 'Valido', value: resultado.valido ? 'Sim' : 'Nao' },
            { label: 'Aluno', value: resultado.nome_aluno || '-' },
            { label: 'Curso', value: resultado.curso || '-' },
            { label: 'Numero', value: resultado.numero_certificado || '-' },
            { label: 'Codigo', value: resultado.codigo_validacao || '-' },
            { label: 'Data de conclusao', value: resultado.data_conclusao || '-' },
            { label: 'Data de emissao', value: resultado.data_emissao || '-' },
            { label: 'Instituicao emissora', value: resultado.instituicao_emissora || '-' },
          ]}
          onClose={() => setResultado(null)}
        />
      ) : null}
    </div>
  )
}
