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
    () => location.pathname.startsWith('/validar-certificado') || location.pathname.startsWith('/validar-documento'),
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
      toast.error(getErrorMessage(error, 'Nao foi possivel validar o documento.'))
    },
  })

  useEffect(() => {
    if (!codigoParam) return
    const codigoInicial = codigoParam.trim().toUpperCase()
    setCodigo(codigoInicial)
    validarMutation.mutate(codigoInicial)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [codigoParam])

  const autenticidadeValida = resultado?.autenticidade === 'valido' || resultado?.valido

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Validacao Publica de Documento</h1>
          <p className="page-subtitle">Consulta de autenticidade de diploma e historico escolar via QR Code ou codigo.</p>
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
                {validarMutation.isPending ? 'Validando...' : 'Validar documento'}
              </button>
            </div>
          </form>
        </div>
      </section>

      {resultado ? (
        <EntityDetailsPanel
          title={`${resultado.tipo_documento_display || 'Documento'} ${resultado.numero_registro || ''}`}
          subtitle={`Autenticidade: ${autenticidadeValida ? 'Valido' : 'Invalido'}`}
          fields={[
            { label: 'Status', value: autenticidadeValida ? 'Valido' : 'Invalido' },
            { label: 'Tipo de documento', value: resultado.tipo_documento_display || resultado.tipo_documento },
            { label: 'Aluno', value: resultado.nome_aluno || '-' },
            { label: 'Curso', value: resultado.curso || '-' },
            { label: 'Situacao do documento', value: resultado.situacao_documento_display || resultado.situacao_documento || '-' },
            { label: 'Numero de registro', value: resultado.numero_registro || '-' },
            { label: 'Livro', value: resultado.livro || '-' },
            { label: 'Folha', value: resultado.folha || '-' },
            { label: 'Pagina', value: resultado.pagina || '-' },
            { label: 'Data de emissao', value: resultado.data_emissao || '-' },
            { label: 'Data de registro', value: resultado.data_registro || '-' },
            { label: 'Hash resumido', value: resultado.hash_resumido || '-' },
            { label: 'Media final', value: resultado.media_final || '-' },
            { label: 'Frequencia final', value: resultado.frequencia_final || '-' },
            { label: 'Situacao final', value: resultado.situacao_final_display || resultado.situacao_final || '-' },
            { label: 'Mensagem institucional', value: autenticidadeValida ? 'Documento autentico e valido na base institucional.' : 'Documento invalido ou cancelado na base institucional.' },
            { label: 'Observacoes', value: resultado.observacoes_publicas || '-' },
          ]}
          onClose={() => setResultado(null)}
        />
      ) : null}
    </div>
  )
}
