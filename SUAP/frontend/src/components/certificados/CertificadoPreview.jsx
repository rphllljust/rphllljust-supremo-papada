export default function CertificadoPreview({ html, onClose, title = 'Pre-visualizacao do certificado' }) {
  if (!html) return null

  const abrirNovaAba = () => {
    const blob = new Blob([html], { type: 'text/html;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    window.open(url, '_blank', 'noopener,noreferrer')
    setTimeout(() => URL.revokeObjectURL(url), 10000)
  }

  return (
    <section className="details-panel">
      <div className="details-panel__header">
        <div>
          <h2 className="details-panel__title">{title}</h2>
          <p className="details-panel__subtitle">
            Layout institucional com faixa lateral, brasao, titulo CERTIFICADO, nome do aluno, texto oficial, assinaturas e logos.
          </p>
        </div>
        <div className="table-actions">
          <button type="button" className="btn btn--outline btn--sm" onClick={abrirNovaAba}>
            Abrir em nova aba
          </button>
          <button type="button" className="btn btn--outline btn--sm" onClick={onClose}>
            Fechar
          </button>
        </div>
      </div>
      <div style={{ border: '1px solid #d8dfe6', borderRadius: 12, overflow: 'hidden', minHeight: 620 }}>
        <iframe
          title={title}
          srcDoc={html}
          style={{ width: '100%', height: 620, border: 'none', backgroundColor: '#f0f2f5' }}
        />
      </div>
    </section>
  )
}
