import EntityFormPanel from '@/components/ui/EntityFormPanel'

const TIPOS_MODELO = [
  { value: 'CERTIFICADO', label: 'Certificado' },
  { value: 'DIPLOMA', label: 'Diploma' },
  { value: 'CERTIFICADO_CONCLUSAO', label: 'Certificado de Conclusao' },
]

function parseListaUrls(rawValue) {
  return String(rawValue || '')
    .split(/\r?\n|,/)
    .map((item) => item.trim())
    .filter(Boolean)
}

export default function ModeloCertificadoForm({
  formData,
  setFormData,
  cursos = [],
  unidades = [],
  onSubmit,
  onCancel,
  isSubmitting,
  submitLabel = 'Salvar modelo',
}) {
  const assinaturas = Array.isArray(formData.assinaturas) ? formData.assinaturas : []
  const logosRodapeValue = (formData.configuracao_visual.logos_rodape || []).join('\n')

  const updateAssinatura = (index, field, value) => {
    setFormData((current) => ({
      ...current,
      assinaturas: (current.assinaturas || []).map((assinatura, idx) => (
        idx === index
          ? { ...assinatura, [field]: value }
          : assinatura
      )),
    }))
  }

  const addAssinatura = () => {
    setFormData((current) => ({
      ...current,
      assinaturas: [
        ...(current.assinaturas || []),
        {
          nome: '',
          cargo: '',
          ordem: (current.assinaturas || []).length + 1,
          ativo: true,
        },
      ],
    }))
  }

  const removeAssinatura = (index) => {
    setFormData((current) => ({
      ...current,
      assinaturas: (current.assinaturas || [])
        .filter((_, idx) => idx !== index)
        .map((assinatura, idx) => ({ ...assinatura, ordem: idx + 1 })),
    }))
  }

  return (
    <EntityFormPanel
      title="Modelo de Certificado"
      subtitle="Cadastre layout, texto padrao e identidade visual institucional."
      onSubmit={onSubmit}
      onCancel={onCancel}
      submitLabel={submitLabel}
      isSubmitting={isSubmitting}
    >
      <div className="form-field">
        <label>Nome do modelo</label>
        <input
          type="text"
          value={formData.nome}
          onChange={(event) => setFormData((current) => ({ ...current, nome: event.target.value }))}
          required
        />
      </div>

      <div className="form-field">
        <label>Tipo</label>
        <select
          className="select"
          value={formData.tipo}
          onChange={(event) => setFormData((current) => ({ ...current, tipo: event.target.value }))}
        >
          {TIPOS_MODELO.map((tipo) => (
            <option key={tipo.value} value={tipo.value}>{tipo.label}</option>
          ))}
        </select>
      </div>

      <div className="form-field form-field--full">
        <label>Descricao</label>
        <input
          type="text"
          value={formData.descricao}
          onChange={(event) => setFormData((current) => ({ ...current, descricao: event.target.value }))}
        />
      </div>

      <div className="form-field">
        <label>Curso (opcional)</label>
        <select
          className="select"
          value={formData.curso || ''}
          onChange={(event) => setFormData((current) => ({ ...current, curso: event.target.value ? Number(event.target.value) : null }))}
        >
          <option value="">Todos</option>
          {cursos.map((curso) => (
            <option key={curso.id} value={curso.id}>
              {curso.nome}
            </option>
          ))}
        </select>
      </div>

      <div className="form-field">
        <label>Unidade (opcional)</label>
        <select
          className="select"
          value={formData.unidade || ''}
          onChange={(event) => setFormData((current) => ({ ...current, unidade: event.target.value ? Number(event.target.value) : null }))}
        >
          <option value="">Todas</option>
          {unidades.map((unidade) => (
            <option key={unidade.id} value={unidade.id}>
              {unidade.nome}
            </option>
          ))}
        </select>
      </div>

      <div className="form-field form-field--full">
        <label>Texto padrao do certificado</label>
        <textarea
          rows="4"
          value={formData.texto_certificado}
          onChange={(event) => setFormData((current) => ({ ...current, texto_certificado: event.target.value }))}
        />
      </div>

      <div className="form-field form-field--full">
        <label>CSS customizado (opcional)</label>
        <textarea
          rows="8"
          value={formData.stylesheet_css}
          onChange={(event) => setFormData((current) => ({ ...current, stylesheet_css: event.target.value }))}
        />
      </div>

      <div className="form-field form-field--full">
        <label>HTML customizado (opcional)</label>
        <textarea
          rows="8"
          value={formData.template_html}
          onChange={(event) => setFormData((current) => ({ ...current, template_html: event.target.value }))}
        />
      </div>

      <div className="form-field">
        <label>Ativo</label>
        <select
          className="select"
          value={formData.ativo ? 'true' : 'false'}
          onChange={(event) => setFormData((current) => ({ ...current, ativo: event.target.value === 'true' }))}
        >
          <option value="true">Sim</option>
          <option value="false">Nao</option>
        </select>
      </div>

      <div className="form-field">
        <label>Sigla da instituicao</label>
        <input
          type="text"
          value={formData.configuracao_visual.sigla_instituicao}
          onChange={(event) => setFormData((current) => ({
            ...current,
            configuracao_visual: { ...current.configuracao_visual, sigla_instituicao: event.target.value },
          }))}
        />
      </div>

      <div className="form-field form-field--full">
        <label>Nome da instituicao</label>
        <input
          type="text"
          value={formData.configuracao_visual.nome_da_instituicao}
          onChange={(event) => setFormData((current) => ({
            ...current,
            configuracao_visual: { ...current.configuracao_visual, nome_da_instituicao: event.target.value },
          }))}
        />
      </div>

      <div className="form-field">
        <label>Brasao (URL)</label>
        <input
          type="url"
          value={formData.configuracao_visual.brasao_instituicao}
          onChange={(event) => setFormData((current) => ({
            ...current,
            configuracao_visual: { ...current.configuracao_visual, brasao_instituicao: event.target.value },
          }))}
        />
      </div>

      <div className="form-field">
        <label>Logo principal (URL)</label>
        <input
          type="url"
          value={formData.configuracao_visual.logo_instituicao}
          onChange={(event) => setFormData((current) => ({
            ...current,
            configuracao_visual: { ...current.configuracao_visual, logo_instituicao: event.target.value },
          }))}
        />
      </div>

      <div className="form-field">
        <label>Marca d'agua (URL)</label>
        <input
          type="url"
          value={formData.configuracao_visual.marca_dagua}
          onChange={(event) => setFormData((current) => ({
            ...current,
            configuracao_visual: { ...current.configuracao_visual, marca_dagua: event.target.value },
          }))}
        />
      </div>

      <div className="form-field">
        <label>Cidade padrao</label>
        <input
          type="text"
          value={formData.configuracao_visual.cidade_padrao}
          onChange={(event) => setFormData((current) => ({
            ...current,
            configuracao_visual: { ...current.configuracao_visual, cidade_padrao: event.target.value },
          }))}
        />
      </div>

      <div className="form-field">
        <label>UF padrao</label>
        <input
          type="text"
          maxLength={2}
          value={formData.configuracao_visual.estado_padrao}
          onChange={(event) => setFormData((current) => ({
            ...current,
            configuracao_visual: { ...current.configuracao_visual, estado_padrao: event.target.value.toUpperCase() },
          }))}
        />
      </div>

      <div className="form-field form-field--full">
        <label>Logos do rodape (uma URL por linha)</label>
        <textarea
          rows="4"
          value={logosRodapeValue}
          onChange={(event) => setFormData((current) => ({
            ...current,
            configuracao_visual: {
              ...current.configuracao_visual,
              logos_rodape: parseListaUrls(event.target.value),
            },
          }))}
        />
      </div>

      <div className="form-field form-field--full">
        <div className="signature-section__header">
          <label>Assinaturas autorizadas</label>
          <button type="button" className="btn btn--outline btn--sm" onClick={addAssinatura}>
            Adicionar assinatura
          </button>
        </div>

        {(assinaturas || []).length === 0 ? (
          <p className="signature-section__empty">Nenhuma assinatura cadastrada. Adicione pelo menos duas para o rodape do certificado.</p>
        ) : (
          <div className="signature-list">
            {assinaturas.map((assinatura, index) => (
              <div key={`${assinatura.id || 'nova'}-${index}`} className="signature-card">
                <div className="signature-card__row">
                  <div className="form-field">
                    <label>Nome</label>
                    <input
                      type="text"
                      value={assinatura.nome || ''}
                      onChange={(event) => updateAssinatura(index, 'nome', event.target.value)}
                      required
                    />
                  </div>
                  <div className="form-field">
                    <label>Cargo</label>
                    <input
                      type="text"
                      value={assinatura.cargo || ''}
                      onChange={(event) => updateAssinatura(index, 'cargo', event.target.value)}
                      required
                    />
                  </div>
                </div>

                <div className="signature-card__row signature-card__row--meta">
                  <div className="form-field">
                    <label>Ordem</label>
                    <input
                      type="number"
                      min={1}
                      value={assinatura.ordem || index + 1}
                      onChange={(event) => updateAssinatura(index, 'ordem', Number(event.target.value || index + 1))}
                    />
                  </div>

                  <div className="form-field">
                    <label>Ativo</label>
                    <select
                      className="select"
                      value={assinatura.ativo === false ? 'false' : 'true'}
                      onChange={(event) => updateAssinatura(index, 'ativo', event.target.value === 'true')}
                    >
                      <option value="true">Sim</option>
                      <option value="false">Nao</option>
                    </select>
                  </div>

                  <div className="form-field signature-card__action">
                    <label>&nbsp;</label>
                    <button type="button" className="btn btn--danger btn--sm" onClick={() => removeAssinatura(index)}>
                      Remover
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </EntityFormPanel>
  )
}
