import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { cursosApi } from '@/api/endpoints'
import SearchableRemoteSelect from '@/components/ui/SearchableRemoteSelect'

import { PUBLICACAO_STATUS_OPTIONS } from './publicacaoShared'

export default function PublicacaoFormFields({ formData, setFormData, selectedCursoOption = null }) {
  const [cursoSearch, setCursoSearch] = useState('')

  const { data: cursosData } = useQuery({
    queryKey: ['cursos', 'publicacoes-options', cursoSearch],
    queryFn: () => cursosApi.list({ page_size: 10, search: cursoSearch || undefined }).then((response) => response.data),
    staleTime: 60_000,
  })

  const cursos = cursosData?.results || []

  return (
    <>
      <SearchableRemoteSelect
        id="publicacao-curso"
        label="Curso"
        searchLabel="Buscar curso"
        searchPlaceholder="Digite nome ou sigla do curso"
        searchValue={cursoSearch}
        onSearchChange={setCursoSearch}
        value={formData.curso}
        onChange={(nextValue) => setFormData((current) => ({ ...current, curso: nextValue }))}
        options={cursos}
        selectedOption={selectedCursoOption}
        getOptionLabel={(item) => `${item.nome}${item.sigla ? ` - ${item.sigla}` : ''}`}
      />

      <div className="form-field form-field--full">
        <label htmlFor="publicacao-titulo">Título do edital</label>
        <input id="publicacao-titulo" className="form-control" value={formData.titulo} onChange={(event) => setFormData((current) => ({ ...current, titulo: event.target.value }))} />
      </div>

      <div className="form-field">
        <label htmlFor="publicacao-vagas">Vagas</label>
        <input id="publicacao-vagas" type="number" min="0" className="form-control" value={formData.vagas} onChange={(event) => setFormData((current) => ({ ...current, vagas: event.target.value }))} />
      </div>

      <div className="form-field">
        <label htmlFor="publicacao-status">Status</label>
        <select id="publicacao-status" className="select" value={formData.status} onChange={(event) => setFormData((current) => ({ ...current, status: event.target.value }))}>
          {PUBLICACAO_STATUS_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
      </div>

      <div className="form-field">
        <label htmlFor="publicacao-data-inicio">Início das inscrições</label>
        <input id="publicacao-data-inicio" type="date" className="form-control" value={formData.data_inicio} onChange={(event) => setFormData((current) => ({ ...current, data_inicio: event.target.value }))} />
      </div>

      <div className="form-field">
        <label htmlFor="publicacao-data-fim">Fim das inscrições</label>
        <input id="publicacao-data-fim" type="date" className="form-control" value={formData.data_fim} onChange={(event) => setFormData((current) => ({ ...current, data_fim: event.target.value }))} />
      </div>

      <div className="form-field form-field--full">
        <label htmlFor="publicacao-descricao">Descrição / requisitos</label>
        <textarea id="publicacao-descricao" className="form-control" rows={4} value={formData.descricao} onChange={(event) => setFormData((current) => ({ ...current, descricao: event.target.value }))} />
      </div>
    </>
  )
}