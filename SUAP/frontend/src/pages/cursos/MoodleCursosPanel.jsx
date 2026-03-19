import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Database, Eye, RefreshCw, Search, Trash2, Upload } from 'lucide-react'
import toast from 'react-hot-toast'

import { moodleIntegrationApi } from '@/api/endpoints'

const DEFAULT_CREATE_FORM = {
  categoryid: '',
  fullname: '',
  shortname: '',
  idnumber: '',
  summary: '',
}

const DEFAULT_UPDATE_FORM = {
  id: '',
  categoryid: '',
  fullname: '',
  shortname: '',
  idnumber: '',
  summary: '',
}

const DEFAULT_QUERY_RESULT = {
  title: 'Sem consulta executada',
  payload: null,
}

function getErrorMessage(error, fallback) {
  return error?.response?.data?.detail || fallback
}

function asOptionalNumber(value) {
  const trimmed = String(value || '').trim()
  if (!trimmed) {
    return undefined
  }
  const parsed = Number(trimmed)
  return Number.isFinite(parsed) ? parsed : trimmed
}

function buildCoursePayload(formState) {
  const payload = {
    fullname: formState.fullname.trim(),
    shortname: formState.shortname.trim(),
  }

  const categoryid = asOptionalNumber(formState.categoryid)
  const idnumber = formState.idnumber.trim()
  const summary = formState.summary.trim()

  if (categoryid !== undefined) {
    payload.categoryid = categoryid
  }
  if (idnumber) {
    payload.idnumber = idnumber
  }
  if (summary) {
    payload.summary = summary
  }

  return payload
}

export default function MoodleCursosPanel() {
  const queryClient = useQueryClient()
  const [fieldQuery, setFieldQuery] = useState({ field: 'idnumber', value: '' })
  const [recentUserId, setRecentUserId] = useState('')
  const [searchValue, setSearchValue] = useState('')
  const [createForm, setCreateForm] = useState(DEFAULT_CREATE_FORM)
  const [updateForm, setUpdateForm] = useState(DEFAULT_UPDATE_FORM)
  const [deleteIds, setDeleteIds] = useState('')
  const [viewCourseId, setViewCourseId] = useState('')
  const [queryResult, setQueryResult] = useState(DEFAULT_QUERY_RESULT)
  const [writeResult, setWriteResult] = useState(DEFAULT_QUERY_RESULT)

  const invalidateCourses = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ['cursos'] }),
      queryClient.invalidateQueries({ queryKey: ['curso'] }),
    ])
  }

  const syncCategoriasMutation = useMutation({
    mutationFn: () => moodleIntegrationApi.syncCategorias({}),
    onSuccess: (response) => {
      const summary = response.data?.summary || {}
      setWriteResult({
        title: 'Categorias sincronizadas',
        payload: response.data,
      })
      toast.success(`Categorias sincronizadas. Novas: ${summary.categories_created || 0}, atualizadas: ${summary.categories_updated || 0}.`)
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Nao foi possivel sincronizar as categorias do Moodle.'))
    },
  })

  const importCursosMutation = useMutation({
    mutationFn: () => moodleIntegrationApi.importCursos({ unidade_codigo: 'sede', integrar_catalogo_interno: true }),
    onSuccess: async (response) => {
      const summary = response.data?.summary || {}
      setWriteResult({
        title: 'Catalogo Moodle importado',
        payload: response.data,
      })
      await invalidateCourses()
      toast.success(`Importacao concluida. Criados: ${summary.created || 0}, atualizados: ${summary.updated || 0}, vinculados: ${summary.linked_existing || 0}.`)
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Nao foi possivel importar os cursos do Moodle.'))
    },
  })

  const getByFieldMutation = useMutation({
    mutationFn: ({ field, value }) => moodleIntegrationApi.getCursosByField(field, value),
    onSuccess: (response) => {
      setQueryResult({ title: 'Consulta por campo', payload: response.data })
      toast.success(`Consulta concluida. ${response.data?.count || 0} curso(s) retornado(s).`)
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Nao foi possivel consultar cursos por campo.'))
    },
  })

  const recentCoursesMutation = useMutation({
    mutationFn: (userid) => moodleIntegrationApi.getRecentCursos(userid),
    onSuccess: (response) => {
      setQueryResult({ title: 'Cursos recentes do usuario', payload: response.data })
      toast.success(`Consulta concluida. ${response.data?.count || 0} curso(s) recente(s).`)
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Nao foi possivel consultar os cursos recentes.'))
    },
  })

  const searchCoursesMutation = useMutation({
    mutationFn: (value) => moodleIntegrationApi.searchCursos(value),
    onSuccess: (response) => {
      setQueryResult({ title: 'Pesquisa de cursos', payload: response.data })
      toast.success(`Pesquisa concluida. ${response.data?.count || 0} curso(s) retornado(s).`)
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Nao foi possivel pesquisar cursos no Moodle.'))
    },
  })

  const createCoursesMutation = useMutation({
    mutationFn: (payload) => moodleIntegrationApi.createCursos(payload),
    onSuccess: async (response) => {
      setWriteResult({ title: 'Curso criado no Moodle', payload: response.data })
      setCreateForm(DEFAULT_CREATE_FORM)
      await invalidateCourses()
      toast.success('Curso criado no Moodle e refletido no SUAP.')
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Nao foi possivel criar o curso no Moodle.'))
    },
  })

  const updateCoursesMutation = useMutation({
    mutationFn: (payload) => moodleIntegrationApi.updateCursos(payload),
    onSuccess: async (response) => {
      setWriteResult({ title: 'Curso atualizado no Moodle', payload: response.data })
      await invalidateCourses()
      toast.success('Curso atualizado no Moodle e sincronizado com o SUAP.')
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Nao foi possivel atualizar o curso no Moodle.'))
    },
  })

  const deleteCoursesMutation = useMutation({
    mutationFn: (payload) => moodleIntegrationApi.deleteCursos(payload),
    onSuccess: async (response) => {
      setWriteResult({ title: 'Cursos excluidos no Moodle', payload: response.data })
      setDeleteIds('')
      await invalidateCourses()
      toast.success('Cursos excluidos no Moodle e desvinculados localmente.')
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Nao foi possivel excluir os cursos no Moodle.'))
    },
  })

  const viewCourseMutation = useMutation({
    mutationFn: (payload) => moodleIntegrationApi.viewCurso(payload),
    onSuccess: (response) => {
      setWriteResult({ title: 'Visualizacao registrada no Moodle', payload: response.data })
      toast.success('Visualizacao do curso registrada no Moodle.')
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Nao foi possivel registrar a visualizacao do curso.'))
    },
  })

  const handleQueryByField = (event) => {
    event.preventDefault()
    if (!fieldQuery.value.trim()) {
      toast.error('Informe o valor para consultar o curso no Moodle.')
      return
    }
    getByFieldMutation.mutate({ field: fieldQuery.field, value: fieldQuery.value.trim() })
  }

  const handleRecentCourses = (event) => {
    event.preventDefault()
    if (!recentUserId.trim()) {
      toast.error('Informe o usuario do Moodle para listar os cursos recentes.')
      return
    }
    recentCoursesMutation.mutate(recentUserId.trim())
  }

  const handleSearchCourses = (event) => {
    event.preventDefault()
    if (!searchValue.trim()) {
      toast.error('Informe um termo para pesquisar cursos no Moodle.')
      return
    }
    searchCoursesMutation.mutate(searchValue.trim())
  }

  const handleCreateCourse = (event) => {
    event.preventDefault()
    if (!createForm.fullname.trim() || !createForm.shortname.trim()) {
      toast.error('Informe pelo menos nome completo e shortname para criar o curso.')
      return
    }

    createCoursesMutation.mutate({
      unidade_codigo: 'sede',
      persistir_espelho_local: true,
      integrar_catalogo_interno: true,
      params: { courses: [buildCoursePayload(createForm)] },
    })
  }

  const handleUpdateCourse = (event) => {
    event.preventDefault()
    if (!updateForm.id.trim()) {
      toast.error('Informe o ID do curso Moodle que sera atualizado.')
      return
    }
    if (!updateForm.fullname.trim() || !updateForm.shortname.trim()) {
      toast.error('Informe nome completo e shortname para atualizar o curso.')
      return
    }

    updateCoursesMutation.mutate({
      unidade_codigo: 'sede',
      persistir_espelho_local: true,
      integrar_catalogo_interno: true,
      params: {
        courses: [
          {
            id: Number(updateForm.id),
            ...buildCoursePayload(updateForm),
          },
        ],
      },
    })
  }

  const handleDeleteCourses = (event) => {
    event.preventDefault()
    const ids = deleteIds
      .split(',')
      .map((value) => Number(value.trim()))
      .filter((value) => Number.isFinite(value))

    if (!ids.length) {
      toast.error('Informe ao menos um ID valido para excluir cursos do Moodle.')
      return
    }

    if (!window.confirm(`Deseja realmente excluir ${ids.length} curso(s) no Moodle?`)) {
      return
    }

    deleteCoursesMutation.mutate({
      persistir_espelho_local: true,
      desvincular_catalogo_interno: true,
      params: { courseids: ids },
    })
  }

  const handleViewCourse = (event) => {
    event.preventDefault()
    if (!viewCourseId.trim()) {
      toast.error('Informe o ID do curso Moodle para registrar a visualizacao.')
      return
    }

    viewCourseMutation.mutate({
      params: { courseid: Number(viewCourseId.trim()) },
    })
  }

  return (
    <section className="dashboard-card moodle-cursos-panel">
      <div className="moodle-cursos-panel__header">
        <div>
          <h2 className="dashboard-card__title">Integração Moodle</h2>
          <p className="page-subtitle">Consulta, sincronização e gestão operacional dos cursos do AVA diretamente dentro do SUAP.</p>
        </div>
        <div className="moodle-cursos-panel__actions">
          <button
            type="button"
            className="btn btn--secondary"
            onClick={() => syncCategoriasMutation.mutate()}
            disabled={syncCategoriasMutation.isPending}
          >
            <Database size={16} /> {syncCategoriasMutation.isPending ? 'Sincronizando categorias...' : 'Sincronizar categorias'}
          </button>
          <button
            type="button"
            className="btn btn--secondary"
            onClick={() => importCursosMutation.mutate()}
            disabled={importCursosMutation.isPending}
          >
            <RefreshCw size={16} /> {importCursosMutation.isPending ? 'Importando...' : 'Importar catálogo'}
          </button>
        </div>
      </div>

      <div className="moodle-cursos-grid">
        <form className="moodle-cursos-card" onSubmit={handleQueryByField}>
          <div className="moodle-cursos-card__header">
            <Search size={18} />
            <div>
              <h3>Consultar por campo</h3>
              <p>Usa core_course_get_courses_by_field para localizar um curso específico.</p>
            </div>
          </div>
          <div className="moodle-cursos-card__body">
            <label className="moodle-cursos-field">
              <span>Campo</span>
              <select value={fieldQuery.field} onChange={(event) => setFieldQuery((current) => ({ ...current, field: event.target.value }))}>
                <option value="id">ID</option>
                <option value="shortname">Shortname</option>
                <option value="idnumber">ID number</option>
                <option value="category">Categoria</option>
              </select>
            </label>
            <label className="moodle-cursos-field">
              <span>Valor</span>
              <input value={fieldQuery.value} onChange={(event) => setFieldQuery((current) => ({ ...current, value: event.target.value }))} placeholder="Ex.: CURSO-2026" />
            </label>
            <button type="submit" className="btn btn--secondary" disabled={getByFieldMutation.isPending}>Consultar</button>
          </div>
        </form>

        <form className="moodle-cursos-card" onSubmit={handleRecentCourses}>
          <div className="moodle-cursos-card__header">
            <RefreshCw size={18} />
            <div>
              <h3>Cursos recentes</h3>
              <p>Usa core_course_get_recent_courses para listar os últimos cursos acessados por um usuário.</p>
            </div>
          </div>
          <div className="moodle-cursos-card__body">
            <label className="moodle-cursos-field">
              <span>Usuário Moodle</span>
              <input value={recentUserId} onChange={(event) => setRecentUserId(event.target.value)} placeholder="Ex.: 42" />
            </label>
            <button type="submit" className="btn btn--secondary" disabled={recentCoursesMutation.isPending}>Listar recentes</button>
          </div>
        </form>

        <form className="moodle-cursos-card" onSubmit={handleSearchCourses}>
          <div className="moodle-cursos-card__header">
            <Search size={18} />
            <div>
              <h3>Pesquisar cursos</h3>
              <p>Usa core_course_search_courses por nome, módulo, bloco ou tag.</p>
            </div>
          </div>
          <div className="moodle-cursos-card__body">
            <label className="moodle-cursos-field">
              <span>Termo de pesquisa</span>
              <input value={searchValue} onChange={(event) => setSearchValue(event.target.value)} placeholder="Ex.: técnico" />
            </label>
            <button type="submit" className="btn btn--secondary" disabled={searchCoursesMutation.isPending}>Pesquisar</button>
          </div>
        </form>

        <form className="moodle-cursos-card moodle-cursos-card--form" onSubmit={handleCreateCourse}>
          <div className="moodle-cursos-card__header">
            <Upload size={18} />
            <div>
              <h3>Criar curso</h3>
              <p>Usa core_course_create_courses e já sincroniza o espelho local e o catálogo interno.</p>
            </div>
          </div>
          <div className="moodle-cursos-card__body moodle-cursos-card__body--grid">
            <label className="moodle-cursos-field"><span>Nome completo</span><input value={createForm.fullname} onChange={(event) => setCreateForm((current) => ({ ...current, fullname: event.target.value }))} /></label>
            <label className="moodle-cursos-field"><span>Shortname</span><input value={createForm.shortname} onChange={(event) => setCreateForm((current) => ({ ...current, shortname: event.target.value }))} /></label>
            <label className="moodle-cursos-field"><span>Categoria Moodle</span><input value={createForm.categoryid} onChange={(event) => setCreateForm((current) => ({ ...current, categoryid: event.target.value }))} /></label>
            <label className="moodle-cursos-field"><span>ID number</span><input value={createForm.idnumber} onChange={(event) => setCreateForm((current) => ({ ...current, idnumber: event.target.value }))} /></label>
            <label className="moodle-cursos-field moodle-cursos-field--full"><span>Resumo</span><textarea rows="3" value={createForm.summary} onChange={(event) => setCreateForm((current) => ({ ...current, summary: event.target.value }))} /></label>
            <div className="moodle-cursos-card__footer"><button type="submit" className="btn btn--secondary" disabled={createCoursesMutation.isPending}>Criar no Moodle</button></div>
          </div>
        </form>

        <form className="moodle-cursos-card moodle-cursos-card--form" onSubmit={handleUpdateCourse}>
          <div className="moodle-cursos-card__header">
            <RefreshCw size={18} />
            <div>
              <h3>Atualizar curso</h3>
              <p>Usa core_course_update_courses e atualiza os vínculos do SUAP com o curso do Moodle.</p>
            </div>
          </div>
          <div className="moodle-cursos-card__body moodle-cursos-card__body--grid">
            <label className="moodle-cursos-field"><span>ID Moodle</span><input value={updateForm.id} onChange={(event) => setUpdateForm((current) => ({ ...current, id: event.target.value }))} /></label>
            <label className="moodle-cursos-field"><span>Nome completo</span><input value={updateForm.fullname} onChange={(event) => setUpdateForm((current) => ({ ...current, fullname: event.target.value }))} /></label>
            <label className="moodle-cursos-field"><span>Shortname</span><input value={updateForm.shortname} onChange={(event) => setUpdateForm((current) => ({ ...current, shortname: event.target.value }))} /></label>
            <label className="moodle-cursos-field"><span>Categoria Moodle</span><input value={updateForm.categoryid} onChange={(event) => setUpdateForm((current) => ({ ...current, categoryid: event.target.value }))} /></label>
            <label className="moodle-cursos-field"><span>ID number</span><input value={updateForm.idnumber} onChange={(event) => setUpdateForm((current) => ({ ...current, idnumber: event.target.value }))} /></label>
            <label className="moodle-cursos-field moodle-cursos-field--full"><span>Resumo</span><textarea rows="3" value={updateForm.summary} onChange={(event) => setUpdateForm((current) => ({ ...current, summary: event.target.value }))} /></label>
            <div className="moodle-cursos-card__footer"><button type="submit" className="btn btn--secondary" disabled={updateCoursesMutation.isPending}>Atualizar no Moodle</button></div>
          </div>
        </form>

        <form className="moodle-cursos-card" onSubmit={handleDeleteCourses}>
          <div className="moodle-cursos-card__header">
            <Trash2 size={18} />
            <div>
              <h3>Excluir cursos</h3>
              <p>Usa core_course_delete_courses e remove o espelho local, limpando o vínculo com o catálogo interno.</p>
            </div>
          </div>
          <div className="moodle-cursos-card__body">
            <label className="moodle-cursos-field">
              <span>IDs Moodle</span>
              <input value={deleteIds} onChange={(event) => setDeleteIds(event.target.value)} placeholder="Ex.: 12, 18, 27" />
            </label>
            <button type="submit" className="btn btn--danger" disabled={deleteCoursesMutation.isPending}>Excluir cursos</button>
          </div>
        </form>

        <form className="moodle-cursos-card" onSubmit={handleViewCourse}>
          <div className="moodle-cursos-card__header">
            <Eye size={18} />
            <div>
              <h3>Registrar visualização</h3>
              <p>Usa core_course_view_course para registrar visualização/auditoria do curso no Moodle.</p>
            </div>
          </div>
          <div className="moodle-cursos-card__body">
            <label className="moodle-cursos-field">
              <span>ID Moodle</span>
              <input value={viewCourseId} onChange={(event) => setViewCourseId(event.target.value)} placeholder="Ex.: 12" />
            </label>
            <button type="submit" className="btn btn--secondary" disabled={viewCourseMutation.isPending}>Registrar visualização</button>
          </div>
        </form>
      </div>

      <div className="moodle-cursos-results">
        <article className="moodle-cursos-result-card">
          <h3>Última consulta</h3>
          <p>{queryResult.title}</p>
          <pre>{JSON.stringify(queryResult.payload, null, 2) || 'Nenhum resultado de consulta ainda.'}</pre>
        </article>
        <article className="moodle-cursos-result-card">
          <h3>Última operação</h3>
          <p>{writeResult.title}</p>
          <pre>{JSON.stringify(writeResult.payload, null, 2) || 'Nenhuma operação executada ainda.'}</pre>
        </article>
      </div>
    </section>
  )
}
