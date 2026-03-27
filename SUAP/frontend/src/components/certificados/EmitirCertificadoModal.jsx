import { X } from 'lucide-react'

export default function EmitirCertificadoModal({
  isOpen,
  onClose,
  emissao,
  setEmissao,
  modelos = [],
  matriculas = [],
  turmas = [],
  isSubmitting = false,
  isPreviewPending = false,
  onSubmit,
  onPreview,
}) {
  if (!isOpen) return null

  return (
    <div
      className="certificados-modal__backdrop"
      role="presentation"
      onClick={onClose}
    >
      <section
        className="certificados-modal"
        role="dialog"
        aria-modal="true"
        aria-label="Emissao de certificados"
        onClick={(event) => event.stopPropagation()}
      >
        <header className="certificados-modal__header">
          <div>
            <h2 className="certificados-modal__title">Emissao de certificados</h2>
            <p className="certificados-modal__subtitle">
              Emissao individual por matricula ou emissao em lote por turma.
            </p>
          </div>
          <button type="button" className="btn btn--outline btn--sm" onClick={onClose}>
            <X size={14} /> Fechar
          </button>
        </header>

        <form
          className="certificados-modal__body"
          onSubmit={(event) => {
            event.preventDefault()
            onSubmit?.()
          }}
        >
          <div className="certificados-modal__grid">
            <div className="form-field">
              <label>Modelo</label>
              <select
                className="select"
                value={emissao.modelo_id}
                onChange={(event) => setEmissao((current) => ({ ...current, modelo_id: event.target.value }))}
                required
              >
                <option value="">Selecione</option>
                {modelos.map((modelo) => (
                  <option key={modelo.id} value={modelo.id}>{modelo.nome}</option>
                ))}
              </select>
            </div>

            <div className="form-field">
              <label>Tipo de emissao</label>
              <select
                className="select"
                value={emissao.tipo}
                onChange={(event) => setEmissao((current) => ({ ...current, tipo: event.target.value }))}
              >
                <option value="individual">Individual</option>
                <option value="lote">Lote por turma</option>
              </select>
            </div>

            {emissao.tipo === 'individual' ? (
              <div className="form-field form-field--full">
                <label>Matricula</label>
                <select
                  className="select"
                  value={emissao.matricula_id}
                  onChange={(event) => setEmissao((current) => ({ ...current, matricula_id: event.target.value }))}
                >
                  <option value="">Selecione</option>
                  {matriculas.map((matricula) => (
                    <option key={matricula.id} value={matricula.id}>
                      {matricula.numero_matricula} - {matricula.aluno_nome}
                    </option>
                  ))}
                </select>
              </div>
            ) : (
              <div className="form-field form-field--full">
                <label>Turma (emissao em lote)</label>
                <select
                  className="select"
                  value={emissao.turma_id}
                  onChange={(event) => setEmissao((current) => ({ ...current, turma_id: event.target.value }))}
                >
                  <option value="">Selecione</option>
                  {turmas.map((turma) => (
                    <option key={turma.id} value={turma.id}>
                      {turma.nome} - {turma.curso_nome}
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div className="form-field">
              <label>Data inicio</label>
              <input
                type="date"
                value={emissao.sobrescritas.data_inicio || ''}
                onChange={(event) => setEmissao((current) => ({
                  ...current,
                  sobrescritas: { ...current.sobrescritas, data_inicio: event.target.value || null },
                }))}
              />
            </div>

            <div className="form-field">
              <label>Data fim</label>
              <input
                type="date"
                value={emissao.sobrescritas.data_fim || ''}
                onChange={(event) => setEmissao((current) => ({
                  ...current,
                  sobrescritas: { ...current.sobrescritas, data_fim: event.target.value || null },
                }))}
              />
            </div>

            <div className="form-field">
              <label>Data conclusao</label>
              <input
                type="date"
                value={emissao.sobrescritas.data_conclusao || ''}
                onChange={(event) => setEmissao((current) => ({
                  ...current,
                  sobrescritas: { ...current.sobrescritas, data_conclusao: event.target.value || null },
                }))}
              />
            </div>

            <div className="form-field">
              <label>Cidade</label>
              <input
                type="text"
                value={emissao.sobrescritas.cidade || ''}
                onChange={(event) => setEmissao((current) => ({
                  ...current,
                  sobrescritas: { ...current.sobrescritas, cidade: event.target.value },
                }))}
              />
            </div>

            <div className="form-field">
              <label>UF</label>
              <input
                type="text"
                maxLength={2}
                value={emissao.sobrescritas.estado || ''}
                onChange={(event) => setEmissao((current) => ({
                  ...current,
                  sobrescritas: { ...current.sobrescritas, estado: event.target.value.toUpperCase() },
                }))}
              />
            </div>

            <div className="form-field">
              <label>Livro</label>
              <input
                type="text"
                value={emissao.sobrescritas.livro || ''}
                onChange={(event) => setEmissao((current) => ({
                  ...current,
                  sobrescritas: { ...current.sobrescritas, livro: event.target.value },
                }))}
              />
            </div>

            <div className="form-field">
              <label>Folha</label>
              <input
                type="text"
                value={emissao.sobrescritas.folha || ''}
                onChange={(event) => setEmissao((current) => ({
                  ...current,
                  sobrescritas: { ...current.sobrescritas, folha: event.target.value },
                }))}
              />
            </div>

            <div className="form-field">
              <label>Gerar PDF na emissao</label>
              <select
                className="select"
                value={emissao.gerar_pdf ? 'true' : 'false'}
                onChange={(event) => setEmissao((current) => ({ ...current, gerar_pdf: event.target.value === 'true' }))}
              >
                <option value="true">Sim</option>
                <option value="false">Nao</option>
              </select>
            </div>

            <div className="form-field form-field--full">
              <label>Texto oficial (opcional)</label>
              <textarea
                rows="3"
                value={emissao.sobrescritas.texto_certificado || ''}
                onChange={(event) => setEmissao((current) => ({
                  ...current,
                  sobrescritas: { ...current.sobrescritas, texto_certificado: event.target.value },
                }))}
              />
            </div>
          </div>

          <footer className="certificados-modal__actions">
            <button type="button" className="btn btn--outline" onClick={onPreview} disabled={isPreviewPending}>
              {isPreviewPending ? 'Gerando preview...' : 'Preview'}
            </button>
            <button type="submit" className="btn btn--primary" disabled={isSubmitting}>
              {isSubmitting ? 'Emitindo...' : (emissao.tipo === 'lote' ? 'Emitir lote' : 'Emitir certificado')}
            </button>
          </footer>
        </form>
      </section>
    </div>
  )
}

