import React, { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { PlusCircle, Trash2, Edit2, ChevronRight, ChevronDown } from 'lucide-react'
import { cursosApi, moodleIntegrationApi } from '@/api/endpoints'
import { moodleCategoriesApi } from '@/api/endpoints'

function buildTree(items) {
  const map = {}
  const roots = []
  items.forEach(i => { map[i.id] = { ...i, children: [] } })
  items.forEach(i => {
    const parentId = i.parent || 0
    if (parentId && map[parentId]) map[parentId].children.push(map[i.id])
    else roots.push(map[i.id])
  })
  return roots
}

function flattenWithDepth(nodes, depth = 0, out = []) {
  nodes.forEach(n => {
    out.push({ id: n.id, name: n.name, depth })
    if (n.children && n.children.length) flattenWithDepth(n.children, depth + 1, out)
  })
  return out
}

function extractArrayPayload(response) {
  const payload = response?.data
  if (!payload) return []
  if (Array.isArray(payload)) return payload
  if (Array.isArray(payload.results)) return payload.results
  if (Array.isArray(payload.data)) return payload.data
  return []
}

function getCategoryDescendantIds(node, out = []) {
  if (!node?.children?.length) return out
  node.children.forEach((child) => {
    if (child.__isCourse) return
    out.push(child.id)
    getCategoryDescendantIds(child, out)
  })
  return out
}

function snapshotCategoryBranchState(node, expandedState, out = {}) {
  if (!node?.children?.length) return out
  node.children.forEach((child) => {
    if (child.__isCourse) return
    out[child.id] = !!expandedState[child.id]
    snapshotCategoryBranchState(child, expandedState, out)
  })
  return out
}

function compareCategoryNodes(left, right) {
  const leftSort = Number.isFinite(Number(left?.sortorder)) ? Number(left.sortorder) : Number.MAX_SAFE_INTEGER
  const rightSort = Number.isFinite(Number(right?.sortorder)) ? Number(right.sortorder) : Number.MAX_SAFE_INTEGER

  if (leftSort !== rightSort) {
    return leftSort - rightSort
  }

  const nameComparison = String(left?.name || '').localeCompare(String(right?.name || ''), 'pt-BR', {
    sensitivity: 'base',
    numeric: true,
  })
  if (nameComparison !== 0) {
    return nameComparison
  }

  return Number(left?.id || 0) - Number(right?.id || 0)
}

function compareCourseNodes(left, right) {
  const leftName = String(left?.fullname || left?.shortname || '').trim()
  const rightName = String(right?.fullname || right?.shortname || '').trim()
  const nameComparison = leftName.localeCompare(rightName, 'pt-BR', {
    sensitivity: 'base',
    numeric: true,
  })
  if (nameComparison !== 0) {
    return nameComparison
  }

  return Number(left?.id || 0) - Number(right?.id || 0)
}

function sortTreeNodes(nodes) {
  const categoryNodes = nodes.filter((node) => !node.__isCourse).slice().sort(compareCategoryNodes)
  const courseNodes = nodes.filter((node) => node.__isCourse).slice().sort(compareCourseNodes)
  const orderedNodes = [...categoryNodes, ...courseNodes]

  orderedNodes.forEach((node) => {
    if (node?.children?.length) {
      node.children = sortTreeNodes(node.children)
    }
  })

  return orderedNodes
}

export default function MoodleCategoriasCursosPanel() {
  const queryClient = useQueryClient()
  const { data: catResp, isFetching: fetchingCats, isError: catsError } = useQuery({
    queryKey: ['moodle-categorias'],
    queryFn: () => moodleIntegrationApi.getCategorias(),
    retry: 1,
    refetchOnWindowFocus: true,
    refetchInterval: 10000, // poll every 10s to pick up external changes
  })
  const { data: cursosResp, isFetching: fetchingCursos, isError: cursosError } = useQuery({
    queryKey: ['moodle-cursos'],
    queryFn: () => moodleIntegrationApi.listCursos(),
    retry: 1,
    refetchOnWindowFocus: true,
    refetchInterval: 10000,
  })
  const { data: internalCursosResp } = useQuery({ queryKey: ['cursos', 'moodle-link-map'], queryFn: () => cursosApi.list({ page_size: 5000 }).then((response) => response.data), staleTime: 5 * 60 * 1000 })

  const categorias = extractArrayPayload(catResp)
  const cursos = extractArrayPayload(cursosResp)
  const internalCursos = extractArrayPayload(internalCursosResp)

  // Helpers to update cached categories (handle axios response shape)
  const updateCachedCategories = (updater) => {
    queryClient.setQueryData(['moodle-categorias'], (old) => {
      const current = extractArrayPayload(old)
      const next = updater(Array.isArray(current) ? current.slice() : [])
      if (!old) return { data: { results: next } }
      // axios response shape: old.data may be array or object with results
      const cloned = { ...old }
      if (Array.isArray(cloned.data)) {
        cloned.data = next
      } else if (cloned.data && typeof cloned.data === 'object') {
        cloned.data = { ...(cloned.data || {}), results: next }
      } else {
        cloned.data = { results: next }
      }
      return cloned
    })
  }

  const internalCourseLookup = new Map()
  internalCursos.forEach((curso) => {
    if (curso?.moodle_course_id) {
      internalCourseLookup.set(`moodle:${Number(curso.moodle_course_id)}`, curso)
    }
    if (curso?.moodle_shortname) {
      internalCourseLookup.set(`shortname:${String(curso.moodle_shortname).trim().toLowerCase()}`, curso)
    }
  })

  // Build category-only tree (used for selects and category-only operations)
  const categoryMap = {}
  const categoryRoots = []
  categorias.forEach(i => { categoryMap[i.id] = { ...i, children: [] } })
  categorias.forEach(i => {
    const parentId = i.parent || 0
    if (parentId && categoryMap[parentId]) categoryMap[parentId].children.push(categoryMap[i.id])
    else categoryRoots.push(categoryMap[i.id])
  })

  // Build display roots starting from categoryRoots and attach courses under their category
  const roots = JSON.parse(JSON.stringify(categoryRoots || []))
  const mapForDisplay = {}
  // build a quick map for display nodes by category id
  const collectMap = (nodes) => {
    nodes.forEach(n => {
      mapForDisplay[n.id] = n
      if (n.children && n.children.length) collectMap(n.children)
    })
  }
  collectMap(roots)

  // attach courses under their category node; orphan courses will be skipped (not shown) unless needed
  cursos.forEach(c => {
    const catId = Number(c.categoryid || 0)
    const node = mapForDisplay[catId]
    const courseNode = { __isCourse: true, id: c.id, fullname: c.fullname || c.displayname || c.shortname, shortname: c.shortname, raw: c }
    if (node) {
      node.children = node.children || []
      node.children.push(courseNode)
    }
  })

  const orderedCategoryRoots = sortTreeNodes(roots)

  const flatCategories = flattenWithDepth(orderedCategoryRoots)

  // Category CRUD state (copied from MoodleCategoriasPanel behavior)
  const [form, setForm] = useState({ name: '', description: '', parent: 0 })
  const [editing, setEditing] = useState(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [modalParent, setModalParent] = useState(0)
  const [expandedNodes, setExpandedNodes] = useState({})
  const [expandedBranchMemory, setExpandedBranchMemory] = useState({})

  const openCreateModal = (parentId = 0) => {
    setForm(f => ({ ...f, parent: Number(parentId || 0) }))
    setModalParent(Number(parentId || 0))
    setShowCreateModal(true)
  }

  const resolveInternalCourseId = (courseNode) => {
    const linkedCourse = courseNode?.raw?.curso
    if (linkedCourse && typeof linkedCourse === 'object' && linkedCourse.id) {
      return linkedCourse.id
    }

    if (courseNode?.raw?.curso_id) {
      return Number(courseNode.raw.curso_id)
    }

    if (courseNode?.raw?.cursoId) {
      return Number(courseNode.raw.cursoId)
    }

    const moodleId = Number(courseNode?.raw?.id || courseNode?.id)
    const linkedByMoodleId = internalCourseLookup.get(`moodle:${moodleId}`)
    if (linkedByMoodleId?.id) {
      return linkedByMoodleId.id
    }

    const shortname = String(courseNode?.raw?.shortname || courseNode?.shortname || '').trim().toLowerCase()
    const linkedByShortname = shortname ? internalCourseLookup.get(`shortname:${shortname}`) : null
    return linkedByShortname?.id || null
  }

  const setBranchExpanded = (node, nextExpanded) => {
    const descendantIds = getCategoryDescendantIds(node)

    if (nextExpanded) {
      setExpandedNodes((current) => {
        const next = { ...current, [node.id]: true }
        descendantIds.forEach((id) => {
          if (expandedBranchMemory[id] !== undefined) {
            next[id] = expandedBranchMemory[id]
          }
        })
        return next
      })
      return
    }

    setExpandedBranchMemory((current) => {
      const next = { ...current }
      Object.assign(next, snapshotCategoryBranchState(node, expandedNodes))
      return next
    })

    setExpandedNodes((current) => {
      const next = { ...current, [node.id]: false }
      descendantIds.forEach((id) => {
        next[id] = false
      })
      return next
    })
  }

  const createMutation = useMutation({
    mutationFn: (payload) => moodleIntegrationApi.createCategorias(payload),
    onMutate: async (payload) => {
      await queryClient.cancelQueries(['moodle-categorias'])
      const previous = queryClient.getQueryData(['moodle-categorias'])
      // determine new category object (support shapes from UI)
      const raw = payload?.params?.[0] || payload
      const temp = {
        id: `tmp-${Date.now()}`,
        name: raw.name || raw.nome || '',
        parent: Number(raw.parent || 0),
        description: raw.description || raw.descricao || '',
      }
      updateCachedCategories(list => [temp, ...list])
      return { previous }
    },
    onError: (err, _payload, context) => {
      if (context?.previous) queryClient.setQueryData(['moodle-categorias'], context.previous)
      toast.error('Erro ao criar categoria no Moodle.')
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['moodle-categorias'] })
      setForm({ name: '', description: '', parent: 0 })
    },
  })

  const updateMutation = useMutation({
    mutationFn: (payload) => moodleIntegrationApi.updateCategorias(payload),
    onMutate: async (payload) => {
      await queryClient.cancelQueries(['moodle-categorias'])
      const previous = queryClient.getQueryData(['moodle-categorias'])
      const raw = (payload?.params && payload.params[0]) || payload
      const id = raw.id || raw.idnumber || raw.moodle_category_id
      updateCachedCategories(list => list.map(item => (String(item.id) === String(id) ? { ...item, name: raw.name || raw.nome || item.name, description: raw.description || raw.descricao || item.description, parent: raw.parent ?? item.parent } : item)))
      return { previous }
    },
    onError: (err, _payload, context) => {
      if (context?.previous) queryClient.setQueryData(['moodle-categorias'], context.previous)
      toast.error('Erro ao atualizar categoria no Moodle.')
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['moodle-categorias'] })
      setEditing(null)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (payload) => moodleIntegrationApi.deleteCategorias(payload),
    onMutate: async (payload) => {
      await queryClient.cancelQueries(['moodle-categorias'])
      const previous = queryClient.getQueryData(['moodle-categorias'])
      // payload might be { params: { categoryids: [id] } } or { categoryids: [id] }
      const ids = payload?.params?.categoryids || payload?.categoryids || ([])
      updateCachedCategories(list => list.filter(item => !ids.includes(Number(item.id))))
      return { previous }
    },
    onError: (err, _payload, context) => {
      if (context?.previous) queryClient.setQueryData(['moodle-categorias'], context.previous)
      toast.error('Erro ao excluir categoria no Moodle.')
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['moodle-categorias'] })
    },
  })

  // Course create/update
  const createCourseMutation = useMutation({
    mutationFn: (data) => moodleIntegrationApi.createCursos(data),
    onSuccess: () => {
      toast.success('Curso criado no Moodle!')
      queryClient.invalidateQueries({ queryKey: ['moodle-cursos'] })
      queryClient.invalidateQueries({ queryKey: ['moodle-categorias'] })
      setShowCreateCourse(false)
    },
    onError: () => toast.error('Erro ao criar curso no Moodle.'),
  })

  const submitCreateCategory = () => {
    if (!form.name.trim()) { toast.error('Informe o nome da categoria.'); return }
    createMutation.mutate({ params: [form] })
    setShowCreateModal(false)
    setForm({ name: '', description: '', parent: 0 })
  }

  const startEditCategory = (cat) => setEditing({ id: cat.id, name: cat.name || '', description: cat.description || '', parent: cat.parent || 0 })
  const cancelEditCategory = () => setEditing(null)
  const submitEditCategory = (e) => {
    e?.preventDefault()
    if (!editing || !editing.name.trim()) { toast.error('Nome inválido.'); return }
    updateMutation.mutate({ params: [{ id: editing.id, name: editing.name, description: editing.description, parent: Number(editing.parent || 0) }] })
  }

  const handleDeleteCategory = (id) => {
    if (!window.confirm('Confirma exclusão da categoria?')) return
    deleteMutation.mutate({ params: { categoryids: [id] } })
  }

  const openCreateCourseFor = (categoryId) => {
    // Redireciona para a página de criação de curso inicial, informando a categoria alvo
    navigate('/ensino/cursoinicial/novo', { state: { from: '/ti/moodle/catalogo/', categoryId: Number(categoryId || 0) } })
  }

  const submitCreateCourse = () => {
    if (createCourseMode === 'new') {
      if (!courseForm.fullname.trim() || !courseForm.shortname.trim()) { toast.error('Informe nome e shortname do curso.'); return }
      const payload = {
        unidade_codigo: 'sede',
        persistir_espelho_local: true,
        integrar_catalogo_interno: true,
        params: { courses: [ { fullname: courseForm.fullname.trim(), shortname: courseForm.shortname.trim(), categoryid: Number(courseForm.categoryid || 0), idnumber: (courseForm.idnumber || '').trim(), summary: (courseForm.summary || '').trim() } ] },
      }
      createCourseMutation.mutate(payload)
      return
    }
    // existing mode: nothing on submit
    return
  }

  // search existing courses
  const searchExistingMutation = useMutation({
    mutationFn: (value) => moodleIntegrationApi.searchCursos(value),
    onSuccess: (res) => {
      const data = res?.data || res
      const list = Array.isArray(data) ? data : (data?.results || data?.data || [])
      setExistingResults(list)
    },
    onError: () => toast.error('Erro ao buscar cursos no Moodle.'),
  })

  const handleSearchExisting = () => {
    if (!existingQuery.trim()) { toast.error('Informe termo para buscar cursos.'); return }
    searchExistingMutation.mutate(existingQuery.trim())
  }

  const addExistingCourseToCategory = (course) => {
    const cat = Number(targetCategoryForAdd || courseForm.categoryid || 0)
    if (!cat && cat !== 0) { toast.error('Categoria inválida'); return }
    updateCourseMutation.mutate({ unidade_codigo: 'sede', persistir_espelho_local: true, integrar_catalogo_interno: true, params: { courses: [{ id: Number(course.id), categoryid: cat }] } })
  }

  const openMoveCourse = (course) => {
    setMovingCourse(course)
    setShowMoveCourse(true)
    setCourseForm(f => ({ ...f, categoryid: course.raw?.categoryid || '' }))
  }

  const handleDeleteCourse = (course) => {
    if (!window.confirm(`Confirma exclusão do curso ${course.fullname || course.shortname || course.id}? Esta ação remove o curso no Moodle.`)) return
    deleteCourseMutation.mutate({ persistir_espelho_local: true, params: { courseids: [Number(course.id)] } })
  }

  const submitMoveCourse = () => {
    if (!movingCourse) return
    const cat = Number(courseForm.categoryid || 0)
    updateCourseMutation.mutate({ unidade_codigo: 'sede', persistir_espelho_local: true, integrar_catalogo_interno: true, params: { courses: [{ id: Number(movingCourse.id), categoryid: cat }] } })
  }

  const findCategoryName = (catid) => {
    const c = categorias.find(x => Number(x.id) === Number(catid))
    return c ? c.name : (catid ? `ID ${catid}` : '—')
  }

  // Search state
  const [query, setQuery] = useState('')

  // Filter function that keeps categories or courses that match the query
  const matchNode = (node, q) => {
    if (!q) return true
    const norm = String(q).trim().toLowerCase()
    if (node.__isCourse) {
      const name = String(node.fullname || node.shortname || '').toLowerCase()
      if (name.includes(norm)) return true
      if (String(node.id).toLowerCase().includes(norm)) return true
      return false
    }
    // category node
    const cname = String(node.name || '').toLowerCase()
    if (cname.includes(norm)) return true
    if (String(node.id).toLowerCase().includes(norm)) return true
    return false
  }

  const filterDisplayTree = (nodes, q) => {
    if (!q) return nodes
    const out = []
    nodes.forEach(n => {
      const cloned = { ...n }
      cloned.children = filterDisplayTree(cloned.children || [], q)
      if (matchNode(cloned, q) || (cloned.children && cloned.children.length)) out.push(cloned)
    })
    return out
  }

  const visibleRoots = filterDisplayTree(orderedCategoryRoots, query)

  const navigate = useNavigate()

  // Auto-run the same routine as the "Atualizar" button when the page opens.
  // Wait until initial fetching of categories/courses finishes, and guard
  // against React StrictMode double-invocation using a ref.
  const _autoRunGuard = useRef(false)
  useEffect(() => {
    if (_autoRunGuard.current) return
    if (fetchingCats || fetchingCursos) return
    _autoRunGuard.current = true

    const doAutoSync = async () => {
      try {
        await moodleCategoriesApi.resetLocalAndSync()
        queryClient.invalidateQueries({ queryKey: ['moodle-categorias'] })
        queryClient.invalidateQueries({ queryKey: ['moodle-cursos'] })
        toast.success('Espelho do Moodle atualizado ao abrir a página.')
      } catch (err) {
        const detail = err?.response?.data?.detail || err?.message || 'Erro desconhecido'
        toast.error(`Falha ao atualizar espelho ao abrir: ${detail}`)
      }
    }

    doAutoSync()
  }, [fetchingCats, fetchingCursos, queryClient])

  // Course-related UI state
  const [showCreateCourse, setShowCreateCourse] = useState(false)
  const [courseForm, setCourseForm] = useState({ fullname: '', shortname: '', idnumber: '', summary: '', categoryid: 0 })
  const [createCourseMode, setCreateCourseMode] = useState('new')
  const [existingQuery, setExistingQuery] = useState('')
  const [existingResults, setExistingResults] = useState([])
  const [targetCategoryForAdd, setTargetCategoryForAdd] = useState(0)
  const [movingCourse, setMovingCourse] = useState(null)
  const [showMoveCourse, setShowMoveCourse] = useState(false)

  const updateCourseMutation = useMutation({
    mutationFn: (data) => moodleIntegrationApi.updateCursos(data),
    onSuccess: () => {
      toast.success('Curso atualizado no Moodle!')
      queryClient.invalidateQueries({ queryKey: ['moodle-cursos'] })
      queryClient.invalidateQueries({ queryKey: ['moodle-categorias'] })
      setShowCreateCourse(false)
      setShowMoveCourse(false)
    },
    onError: () => toast.error('Erro ao atualizar curso no Moodle.'),
  })

  const deleteCourseMutation = useMutation({
    mutationFn: (data) => moodleIntegrationApi.deleteCursos(data),
    onSuccess: () => {
      toast.success('Curso excluído no Moodle!')
      queryClient.invalidateQueries({ queryKey: ['moodle-cursos'] })
      queryClient.invalidateQueries({ queryKey: ['moodle-categorias'] })
    },
    onError: () => toast.error('Erro ao excluir curso no Moodle.'),
  })

  function ResetMirrorButton({ queryClient, fetchingCats, fetchingCursos }) {
    const resetMutation = useMutation({
      mutationFn: async () => {
        // Call backend endpoint that wipes local mirror and re-syncs from Moodle
        await moodleCategoriesApi.resetLocalAndSync()
      },
      onSuccess: () => {
        toast.success('Espelho do Moodle resetado e sincronizado com sucesso.')
        queryClient.invalidateQueries({ queryKey: ['moodle-categorias'] })
        queryClient.invalidateQueries({ queryKey: ['moodle-cursos'] })
      },
      onError: (err) => {
        const detail = err?.response?.data?.detail || err?.message || 'Erro desconhecido'
        toast.error(`Falha ao resetar espelho: ${detail}`)
      },
    })

    return (
      <button
        className="btn btn--danger"
        disabled={resetMutation.isPending || fetchingCats || fetchingCursos}
        onClick={() => {
          if (!window.confirm('Confirma resetar o espelho local do Moodle? Isso apagará dados espelhados e re-importará do Moodle.')) return
          resetMutation.mutate()
        }}
        title="Atualizar espelho local (limpar e importar do Moodle)"
      >
        Atualizar
      </button>
    )
  }

  return (
    <section className="dashboard-card moodle-categorias-cursos-panel">
      <div className="moodle-categorias-header" style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 16}}>
        <div>
          <h2 className="dashboard-card__title">Categorias & Cursos Moodle</h2>
          <div style={{fontSize: 13, color: '#666'}}>{categorias.length} categorias — {cursos.length} cursos</div>
        </div>
        <div style={{display: 'flex', gap: 8}}>
          <input placeholder="Buscar cursos/categoria..." value={query} onChange={e => setQuery(e.target.value)} style={{padding: '6px 8px', borderRadius: 6, border: '1px solid #ddd'}} />
          
          <ResetMirrorButton queryClient={queryClient} fetchingCats={fetchingCats} fetchingCursos={fetchingCursos} />
        </div>
      </div>

      <div style={{display: 'grid', gap: '0.75rem'}}>
        <div>
          <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, marginBottom: 6}}>
            <h3 style={{marginTop: 4, marginBottom: 0}}>Árvore de categorias</h3>
            <div>
              <button className="btn btn--primary" onClick={() => openCreateModal(0)}><PlusCircle size={14} />&nbsp;Criar categoria</button>
            </div>
          </div>
          <div style={{background: '#fff', border: '1px solid #dcc8b2', borderRadius: 8, overflowX: 'auto'}}>
            <table style={{width: '100%', minWidth: 1080, borderCollapse: 'collapse', tableLayout: 'fixed'}}>
              <thead>
                <tr style={{background: '#f2e6d6'}}>
                  <th style={{textAlign: 'left', padding: '10px 10px', width: '30%', borderBottom: '2px solid #c8b39c'}}>Curso</th>
                  <th style={{textAlign: 'left', padding: '10px 10px', width: 90, borderBottom: '2px solid #c8b39c'}}>Sigla</th>
                  <th style={{textAlign: 'left', padding: '10px 10px', width: 140, borderBottom: '2px solid #c8b39c'}}>Unidade</th>
                  <th style={{textAlign: 'left', padding: '10px 10px', width: 180, borderBottom: '2px solid #c8b39c'}}>Área do Curso</th>
                  <th style={{textAlign: 'left', padding: '10px 10px', width: 180, borderBottom: '2px solid #c8b39c'}}>Eixo Tecnológico</th>
                  <th style={{textAlign: 'right', padding: '10px 10px', width: 120, borderBottom: '2px solid #c8b39c'}}>Carga Horária (h)</th>
                  <th style={{textAlign: 'right', padding: '10px 10px', width: 240, borderBottom: '2px solid #c8b39c'}}>Ações</th>
                </tr>
              </thead>
              <tbody>
                {visibleRoots.length === 0 ? (
                  <tr>
                    <td colSpan={7} style={{padding: '14px 12px', color: '#666'}}>Nenhuma categoria ou curso encontrado.</td>
                  </tr>
                ) : (
                  visibleRoots.map(node => (
                    <TreeNode
                      key={node.__isCourse ? `course-${node.id}` : `cat-${node.id}`}
                      node={node}
                      depth={0}
                      editing={editing}
                      setEditing={setEditing}
                      submitEditCategory={submitEditCategory}
                      cancelEditCategory={cancelEditCategory}
                      startEditCategory={startEditCategory}
                      handleDeleteCategory={handleDeleteCategory}
                      openCreateModal={openCreateModal}
                      openCreateCourseFor={openCreateCourseFor}
                      openMoveCourse={openMoveCourse}
                      handleDeleteCourse={handleDeleteCourse}
                      deletePending={deleteCourseMutation.isPending}
                      searchQuery={query}
                      navigate={navigate}
                      expandedNodes={expandedNodes}
                      setBranchExpanded={setBranchExpanded}
                      resolveInternalCourseId={resolveInternalCourseId}
                    />
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {showCreateModal && (
        <div style={{position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9999}}>
          <div style={{background: '#fff', padding: 20, borderRadius: 8, width: 600, maxWidth: '95%'}}>
            <h3 style={{marginTop: 0}}>Criar categoria</h3>
            <form onSubmit={(e) => { e.preventDefault(); submitCreateCategory() }}>
              <label style={{display: 'block', marginBottom: 8}}>
                <div>Nome</div>
                <input autoFocus value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
              </label>
              <label style={{display: 'block', marginBottom: 8}}>
                <div>Descrição</div>
                <input value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} />
              </label>
              <label style={{display: 'block', marginBottom: 8}}>
                <div>Parent (ID)</div>
                <select value={form.parent} onChange={e => setForm(f => ({ ...f, parent: Number(e.target.value) }))}>
                  <option value={0}>— Nenhum —</option>
                    {flatCategories.map(c => (
                      <option key={c.id} value={c.id}>{'\u00A0'.repeat(c.depth * 2)}{c.name} (ID: {c.id})</option>
                    ))}
                </select>
              </label>
              <div style={{display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 12}}>
                <button type="button" className="btn" onClick={() => { setShowCreateModal(false); setForm({ name: '', description: '', parent: 0 }) }}>Cancelar</button>
                <button type="submit" className="btn btn--primary" disabled={createMutation.isPending}>Criar</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showCreateCourse && (
        <div style={{position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9999}}>
          <div style={{background: '#fff', padding: 20, borderRadius: 8, width: 760, maxWidth: '95%'}}>
            <h3 style={{marginTop: 0}}>{createCourseMode === 'new' ? 'Criar curso no Moodle' : 'Adicionar curso existente'}</h3>
            <div style={{display: 'grid', gap: 8}}>
              <div style={{display: 'flex', gap: 12, alignItems: 'center'}}>
                <label style={{display: 'flex', gap: 6, alignItems: 'center'}}><input type="radio" checked={createCourseMode === 'new'} onChange={() => setCreateCourseMode('new')} /> Criar novo</label>
                <label style={{display: 'flex', gap: 6, alignItems: 'center'}}><input type="radio" checked={createCourseMode === 'existing'} onChange={() => setCreateCourseMode('existing')} /> Adicionar existente</label>
              </div>

              {createCourseMode === 'new' ? (
                <>
                  <label><div>Nome completo</div><input autoFocus value={courseForm.fullname} onChange={e => setCourseForm(f => ({ ...f, fullname: e.target.value }))} /></label>
                  <label><div>Shortname</div><input value={courseForm.shortname} onChange={e => setCourseForm(f => ({ ...f, shortname: e.target.value }))} /></label>
                  <label><div>Categoria</div>
                    <select value={courseForm.categoryid} onChange={e => setCourseForm(f => ({ ...f, categoryid: e.target.value }))}>
                      <option value="">— Selecionar —</option>
                      {flatCategories.map(f => <option key={f.id} value={f.id}>{'\u00A0'.repeat(f.depth * 2)}{f.name} (ID: {f.id})</option>)}
                    </select>
                  </label>
                  <label><div>ID number (opcional)</div><input value={courseForm.idnumber} onChange={e => setCourseForm(f => ({ ...f, idnumber: e.target.value }))} /></label>
                  <label><div>Resumo (opcional)</div><textarea rows={3} value={courseForm.summary} onChange={e => setCourseForm(f => ({ ...f, summary: e.target.value }))} /></label>
                  <div style={{display: 'flex', justifyContent: 'flex-end', gap: 8}}>
                    <button className="btn" onClick={() => setShowCreateCourse(false)}>Cancelar</button>
                    <button className="btn btn--primary" onClick={() => submitCreateCourse()} disabled={createCourseMutation.isPending}>Criar curso</button>
                  </div>
                </>
              ) : (
                <div style={{display: 'grid', gridTemplateColumns: '1fr 320px', gap: 12}}>
                  <div>
                    <label><div>Pesquisar curso existente</div>
                      <div style={{display: 'flex', gap: 8}}>
                        <input value={existingQuery} onChange={e => setExistingQuery(e.target.value)} placeholder="Pesquisar por nome ou ID" />
                        <button className="btn btn--secondary" onClick={() => handleSearchExisting()} disabled={searchExistingMutation?.isPending}>Buscar</button>
                      </div>
                    </label>

                    <div style={{marginTop: 8}}>
                      {existingResults.length === 0 ? <div>Nenhum resultado.</div> : (
                        <ul style={{listStyle: 'none', paddingLeft: 0}}>
                          {existingResults.map(r => (
                            <li key={r.id} style={{display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid #eee'}}>
                              <div>
                                <div><strong>{r.fullname || r.displayname || r.shortname}</strong> <span style={{color: '#666', fontSize: 12}}>(ID: {r.id})</span></div>
                                <div style={{fontSize: 12, color: '#666'}}>Categoria atual: {findCategoryName(r.categoryid)}</div>
                              </div>
                              <div style={{display: 'flex', flexDirection: 'column', gap: 6}}>
                                <button className="btn btn--secondary" onClick={() => { setCourseForm(f => ({ ...f, categoryid: targetCategoryForAdd || courseForm.categoryid })); addExistingCourseToCategory(r) }}>Adicionar aqui</button>
                                <button className="btn" onClick={() => { setCourseForm(f => ({ ...f, categoryid: targetCategoryForAdd || courseForm.categoryid })); setCreateCourseMode('new'); setCourseForm({ ...courseForm, fullname: r.fullname || r.displayname || r.shortname, shortname: r.shortname, idnumber: r.idnumber || '' }) }}>Criar cópia</button>
                              </div>
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  </div>

                  <div style={{borderLeft: '1px solid #eee', paddingLeft: 12}}>
                    <div style={{marginBottom: 8}}><strong>Cursos nesta categoria</strong></div>
                    <div style={{maxHeight: 300, overflow: 'auto'}}>
                      <ul style={{listStyle: 'none', paddingLeft: 0}}>
                        {(mapForDisplay[targetCategoryForAdd]?.children || []).filter(n => n.__isCourse).map(cc => (
                          <li key={cc.id} style={{padding: '6px 0', borderBottom: '1px solid #f3f3f3'}}>
                            <div><strong>{cc.fullname}</strong> <span style={{color: '#666', fontSize: 12}}>(ID: {cc.id})</span></div>
                          </li>
                        ))}
                      </ul>
                    </div>
                    <div style={{marginTop: 12}}>
                      <button className="btn" onClick={() => setShowCreateCourse(false)}>Fechar</button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {showMoveCourse && (
        <div style={{position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9999}}>
          <div style={{background: '#fff', padding: 20, borderRadius: 8, width: 480, maxWidth: '95%'}}>
            <h3 style={{marginTop: 0}}>Mover curso</h3>
            <div>
              <div style={{marginBottom: 8}}>Curso: <strong>{movingCourse?.raw?.fullname || movingCourse?.raw?.shortname || movingCourse?.fullname}</strong></div>
              <label><div>Nova categoria</div>
                <select value={courseForm.categoryid} onChange={e => setCourseForm(f => ({ ...f, categoryid: e.target.value }))}>
                  <option value="">— Selecionar —</option>
                  {flatCategories.map(f => <option key={f.id} value={f.id}>{'\u00A0'.repeat(f.depth * 2)}{f.name} (ID: {f.id})</option>)}
                </select>
              </label>
              <div style={{display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 12}}>
                <button className="btn" onClick={() => setShowMoveCourse(false)}>Cancelar</button>
                <button className="btn btn--primary" onClick={() => submitMoveCourse()} disabled={updateCourseMutation.isPending}>Mover</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  )
}

function TreeNode({ node, depth, editing, setEditing, submitEditCategory, cancelEditCategory, startEditCategory, handleDeleteCategory, openCreateModal, openCreateCourseFor, openMoveCourse, handleDeleteCourse, deletePending, searchQuery, navigate, expandedNodes, setBranchExpanded, resolveInternalCourseId }) {
  const isCourse = node.__isCourse === true
  const expanded = isCourse ? false : !!expandedNodes[node.id]
  useEffect(() => {
    if (searchQuery && String(searchQuery).trim()) {
      if (!isCourse) {
        setBranchExpanded(node, true)
      }
    }
  }, [searchQuery, isCourse, node, setBranchExpanded])

  if (isCourse) {
    return (
      <tr style={{background: '#fff'}}>
        <td style={{padding: '8px 10px 8px 24px', borderBottom: '1px solid #d9c8b5'}}>
          <div style={{display: 'flex', flexDirection: 'column', gap: 2}}>
            <strong style={{color: '#222'}}>{node.fullname}</strong>
            <span style={{fontSize: 12, color: '#666'}}>Curso Moodle</span>
          </div>
        </td>
        <td style={{padding: '8px 10px', borderBottom: '1px solid #d9c8b5'}}>{node.shortname || '—'}</td>
        <td style={{padding: '8px 10px', borderBottom: '1px solid #d9c8b5'}}>{(node.raw && node.raw.curso && node.raw.curso.unidade_nome) || '—'}</td>
        <td style={{padding: '8px 10px', borderBottom: '1px solid #d9c8b5'}}>{(node.raw && node.raw.curso && node.raw.curso.area_curso_nome) || '—'}</td>
        <td style={{padding: '8px 10px', borderBottom: '1px solid #d9c8b5'}}>{(node.raw && node.raw.curso && node.raw.curso.eixo_tecnologico) || '—'}</td>
        <td style={{padding: '8px 10px', borderBottom: '1px solid #d9c8b5', textAlign: 'right'}}>{(node.raw && node.raw.curso && node.raw.curso.carga_horaria) || 0}</td>
        <td style={{padding: '8px 10px', borderBottom: '1px solid #d9c8b5'}}>
          <div style={{display: 'flex', flexDirection: 'column', gap: 6, alignItems: 'flex-end'}}>
            <button className="btn btn--outline" onClick={() => {
              const linkedId = resolveInternalCourseId(node)
              if (linkedId) navigate(`/ensino/cursoinicial/${linkedId}`)
            }}>Detalhes</button>
            <button className="btn btn--secondary" onClick={() => {
              const linkedId = resolveInternalCourseId(node)
              if (linkedId) navigate(`/ensino/cursoinicial/${linkedId}/editar`)
            }}>Editar</button>
            <button className="btn btn--danger" onClick={() => handleDeleteCourse(node)} disabled={deletePending}>Excluir</button>
          </div>
        </td>
      </tr>
    )
  }

  const hasChildren = node.children && node.children.length > 0
  return (
    <>
      <tr style={{background: depth % 2 === 0 ? '#fffdf7' : '#fff'}}>
        <td style={{padding: '8px 10px', borderBottom: '1px solid #d9c8b5'}}>
          <div style={{display: 'flex', alignItems: 'center', gap: 6, paddingLeft: depth * 12}}>
            <button className="btn btn--icon" onClick={() => setBranchExpanded(node, !expanded)} aria-label={expanded ? 'Fechar' : 'Abrir'} style={{width: 24, height: 24, flex: '0 0 auto', visibility: hasChildren ? 'visible' : 'hidden'}}>
              {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            </button>
            <div style={{minWidth: 0}}>
              {editing && editing.id === node.id ? (
                <input value={editing.name} onChange={e => setEditing(ed => ({ ...ed, name: e.target.value }))} />
              ) : (
                <>
                  <button className="btn btn--link" onClick={() => setBranchExpanded(node, !expanded)} style={{padding: 0, border: 'none', background: 'transparent', textAlign: 'left'}}>
                    <strong style={{cursor: 'pointer', color: '#222'}}>{node.name}</strong>
                  </button>
                  <span style={{color: '#666', fontSize: 12, marginLeft: 8}}>(ID: {node.id})</span>
                </>
              )}
              {node.description ? <div style={{fontSize: 12, color: '#666'}}>{node.description}</div> : null}
            </div>
          </div>
        </td>
        <td style={{padding: '8px 10px', borderBottom: '1px solid #d9c8b5', color: '#666'}}>{node.shortname || '—'}</td>
        <td style={{padding: '8px 10px', borderBottom: '1px solid #d9c8b5', color: '#666'}}>{node.unidade || '—'}</td>
        <td style={{padding: '8px 10px', borderBottom: '1px solid #d9c8b5', color: '#666'}}>{node.area_curso || '—'}</td>
        <td style={{padding: '8px 10px', borderBottom: '1px solid #d9c8b5', color: '#666'}}>{node.eixo_tecnologico || '—'}</td>
        <td style={{padding: '8px 10px', borderBottom: '1px solid #d9c8b5', textAlign: 'right', color: '#666'}}>{node.carga_horaria || '—'}</td>
        <td style={{padding: '8px 10px', borderBottom: '1px solid #d9c8b5'}}>
          <div style={{display: 'flex', gap: 6, alignItems: 'center', justifyContent: 'flex-end', flexWrap: 'wrap'}}>
            {editing && editing.id === node.id ? (
              <>
                <button className="btn btn--primary" onClick={submitEditCategory}>Salvar</button>
                <button className="btn" onClick={cancelEditCategory}>Cancelar</button>
              </>
            ) : (
              <>
                <button className="btn btn--outline" onClick={() => startEditCategory(node)}><Edit2 size={14} /></button>
                <button className="btn btn--danger" onClick={() => handleDeleteCategory(node.id)}><Trash2 size={14} /></button>
                <button className="btn btn--outline" onClick={() => openCreateModal(node.parent)} title="Criar irmão">Criar irmão</button>
                <button className="btn btn--outline" onClick={() => openCreateModal(node.id)} title="Adicionar subcategoria">Criar subcategoria</button>
                <button className="btn btn--outline" onClick={() => openCreateCourseFor(node.id)} title="Adicionar curso"><PlusCircle size={14} />&nbsp;Adicionar curso</button>
              </>
            )}
          </div>
        </td>
      </tr>

      {expanded && hasChildren && node.children.map(c => (
        <TreeNode
          key={c.__isCourse ? `course-${c.id}` : `cat-${c.id}`}
          node={c}
          depth={depth + 1}
          editing={editing}
          setEditing={setEditing}
          submitEditCategory={submitEditCategory}
          cancelEditCategory={cancelEditCategory}
          startEditCategory={startEditCategory}
          handleDeleteCategory={handleDeleteCategory}
          openCreateModal={openCreateModal}
          openCreateCourseFor={openCreateCourseFor}
          openMoveCourse={openMoveCourse}
          handleDeleteCourse={handleDeleteCourse}
          deletePending={deletePending}
          searchQuery={searchQuery}
          navigate={navigate}
          expandedNodes={expandedNodes}
          setBranchExpanded={setBranchExpanded}
          resolveInternalCourseId={resolveInternalCourseId}
        />
      ))}
    </>
  )
}
