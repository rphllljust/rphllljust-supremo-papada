import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { moodleIntegrationApi, moodleCategoriesApi } from '@/api/endpoints'
import toast from 'react-hot-toast'
import { PlusCircle, Trash2, RefreshCw, Edit2, ChevronRight, ChevronDown } from 'lucide-react'

function fetchCategorias() {
  return moodleIntegrationApi.getCategorias()
}

export default function MoodleCategoriasPanel() {
  const queryClient = useQueryClient()
  const { data, isFetching, isError } = useQuery({
    queryKey: ['moodle-categorias'],
    queryFn: fetchCategorias,
    retry: 1,
    refetchOnWindowFocus: false,
  })

  const categorias = (data?.data?.results) || []
  const [query, setQuery] = useState('')

  // Constrói uma árvore de categorias a partir da lista plana
  const buildTree = (items) => {
    const map = {}
    const roots = []
    items.forEach(i => { map[i.id] = { ...i, children: [] } })
    items.forEach(i => {
      const parentId = i.parent || 0
      if (parentId && map[parentId]) {
        map[parentId].children.push(map[i.id])
      } else {
        roots.push(map[i.id])
      }
    })
    return roots
  }

  const tree = buildTree(categorias)

  // Estado de nós expandidos
  const [expanded, setExpanded] = useState(new Set())
  const toggle = (id) => {
    setExpanded(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  // Flatten para o select com indentação
  const flattenWithDepth = (nodes, depth = 0, out = []) => {
    nodes.forEach(n => {
      out.push({ id: n.id, name: n.name, depth })
      if (n.children && n.children.length) flattenWithDepth(n.children, depth + 1, out)
    })
    return out
  }
  const flatCategories = flattenWithDepth(tree)

  // Filter tree by search query (keep nodes that match or have matching descendants)
  const filterTree = (nodes, q) => {
    if (!q) return nodes
    const norm = q.trim().toLowerCase()
    const matches = (n) => (n.name || '').toLowerCase().includes(norm)
    const rez = []
    nodes.forEach(n => {
      const cloned = { ...n }
      cloned.children = filterTree(cloned.children || [], q)
      if (matches(cloned) || (cloned.children && cloned.children.length)) rez.push(cloned)
    })
    return rez
  }

  const visibleTree = filterTree(tree, query)

  const [form, setForm] = useState({ name: '', description: '', parent: 0 })
  const [editing, setEditing] = useState(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [modalParent, setModalParent] = useState(0)

  const openCreateModal = (parentId = 0) => {
    setForm(f => ({ ...f, parent: Number(parentId || 0) }))
    setModalParent(Number(parentId || 0))
    setShowCreateModal(true)
  }

  const createMutation = useMutation({
    mutationFn: (payload) => moodleIntegrationApi.createCategorias(payload),
    onSuccess: () => {
      toast.success('Categoria criada no Moodle!')
      queryClient.invalidateQueries({ queryKey: ['moodle-categorias'] })
      setForm({ name: '', description: '', parent: 0 })
    },
    onError: () => toast.error('Erro ao criar categoria no Moodle.'),
  })

  const updateMutation = useMutation({
    mutationFn: (payload) => moodleIntegrationApi.updateCategorias(payload),
    onSuccess: () => {
      toast.success('Categoria atualizada no Moodle!')
      queryClient.invalidateQueries({ queryKey: ['moodle-categorias'] })
      setEditing(null)
    },
    onError: () => toast.error('Erro ao atualizar categoria no Moodle.'),
  })

  const deleteMutation = useMutation({
    mutationFn: (payload) => {
      // Always use POST to backend; backend will call Moodle REST POST.
      return moodleIntegrationApi.deleteCategorias(payload)
    },
    onSuccess: (res) => {
      // res is the axios response; try to summarize backend result to help debugging
      try {
        const body = res?.data
        if (body && body.moodle_response) {
          const mr = body.moodle_response
          if (mr.deleted && Array.isArray(mr.deleted)) {
            toast.success(`Excluídas: ${mr.deleted.length}`)
          } else if (mr.deleted && typeof mr.deleted === 'number') {
            toast.success(`Excluídas: ${mr.deleted}`)
          } else if (mr.failed && Array.isArray(mr.failed) && mr.failed.length) {
            toast.error(`Falhas: ${mr.failed.length}`)
          } else {
            toast.success('Categoria excluída no Moodle!')
          }
        } else if (body && body.detail) {
          toast.success(body.detail)
        } else {
          toast.success('Categoria excluída no Moodle!')
        }
      } catch (err) {
        toast.success('Categoria excluída no Moodle!')
      }

      console.info('Delete response:', res)
      queryClient.invalidateQueries({ queryKey: ['moodle-categorias'] })
    },
    onError: (err) => {
      console.error('Delete error:', err)
      try {
        const detail = err?.response?.data?.detail || err?.response?.data || err?.message
        toast.error(String(detail))
      } catch (e) {
        toast.error('Erro ao excluir categoria no Moodle.')
      }
    },
  })

  const compareMutation = useMutation({
    mutationFn: () => moodleCategoriesApi.diffAndSync.diff(),
    onSuccess: (res) => {
      const data = res?.data || res
      const msg = `Moodle: ${data.count_live} categorias\nSUAP (espelho): ${data.count_local} categorias\nSomente no Moodle: ${data.only_in_live_count}\nSomente no SUAP: ${data.only_in_local_count}`
      // Ask user confirmation before syncing
      if (window.confirm(`${msg}\n\nDeseja sincronizar (resetar Moodle e recriar a estrutura do SUAP)?`)) {
        syncMutation.mutate()
      }
    },
    onError: () => toast.error('Erro ao comparar categorias com o Moodle.'),
  })

  const syncMutation = useMutation({
    mutationFn: () => moodleCategoriesApi.diffAndSync.sync(),
    onSuccess: (res) => {
      toast.success('Sincronizacao executada com sucesso.')
      queryClient.invalidateQueries({ queryKey: ['moodle-categorias'] })
    },
    onError: () => toast.error('Erro ao executar sincronizacao.'),
  })

  const handleCreate = (e) => {
    e.preventDefault()
    if (!form.name.trim()) {
      toast.error('Informe o nome da categoria.')
      return
    }
    createMutation.mutate({ params: [form] })
  }

  const submitCreate = () => {
    if (!form.name.trim()) {
      toast.error('Informe o nome da categoria.')
      return
    }
    createMutation.mutate({ params: [form] })
    setShowCreateModal(false)
    setForm({ name: '', description: '', parent: 0 })
  }

  const handleStartEdit = (cat) => {
    setEditing({ id: cat.id, name: cat.name || '', description: cat.description || '', parent: cat.parent || 0 })
  }

  const handleCancelEdit = () => setEditing(null)

  const handleSaveEdit = (e) => {
    e.preventDefault()
    if (!editing || !editing.name.trim()) {
      toast.error('Nome inválido.')
      return
    }
    updateMutation.mutate({ params: [{ id: editing.id, name: editing.name, description: editing.description, parent: Number(editing.parent || 0) }] })
  }

  const handleDelete = (id) => {
    if (!window.confirm('Confirma exclusão da categoria?')) return
    // API espera { params: { categoryids: [..] } }
    deleteMutation.mutate({ params: { categoryids: [id] } })
  }

  return (
    <section className="dashboard-card moodle-categorias-panel">
      <div className="moodle-categorias-header" style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
        <div>
          <h2 className="dashboard-card__title">Categorias Moodle</h2>
          <div style={{fontSize: 13, color: '#666'}}>{categorias.length} categorias</div>
        </div>
        <div style={{display: 'flex', gap: 8}}>
          <input placeholder="Buscar categorias..." value={query} onChange={e => setQuery(e.target.value)} style={{padding: '6px 8px', borderRadius: 6, border: '1px solid #ddd'}} />
          <button className="btn btn--secondary" onClick={() => queryClient.invalidateQueries(['moodle-categorias'])} disabled={isFetching} title="Atualizar lista"><RefreshCw size={16} />&nbsp;Atualizar</button>
          <button className="btn btn--outline" onClick={() => compareMutation.mutate()} disabled={compareMutation.isPending || syncMutation.isPending}><RefreshCw size={14} />&nbsp;Comparar & Sincronizar</button>
          <button
            className="btn btn--danger"
            onClick={() => {
              if (!categorias || categorias.length === 0) {
                toast.error('Nenhuma categoria para excluir.')
                return
              }
              if (!window.confirm(`Confirma exclusão de TODAS as categorias (${categorias.length}) do Moodle? Esta operação é irreversível.`)) return
              const ids = categorias.map(c => c.id)
              deleteMutation.mutate({ params: { categoryids: ids } })
            }}
            disabled={deleteMutation.isPending}
            title="Apagar todas as categorias do Moodle"
          >
            <Trash2 size={14} />&nbsp;Apagar todas
          </button>
        </div>
      </div>

      <div style={{display: 'flex', gap: '1rem', flexWrap: 'wrap'}}>
        {categorias.length === 0 ? (
          <div style={{flex: '1 1 320px', minWidth: 280}}>
            <div style={{marginBottom: 8}}>Nenhuma categoria encontrada. Crie a primeira categoria:</div>
            <button className="btn btn--primary" onClick={() => openCreateModal(0)}><PlusCircle size={14} />&nbsp;Criar primeira categoria</button>
          </div>
        ) : null}

        <div style={{flex: '2 1 520px', minWidth: 320}}>
          <div style={{marginBottom: 8}}>
            {isFetching ? <div>Carregando categorias...</div> : isError ? <div>Erro ao carregar categorias.</div> : null}
          </div>

          <div>
            {categorias.length === 0 && <div>Nenhuma categoria encontrada.</div>}

            <ul style={{listStyle: 'none', paddingLeft: 0}}>
              {visibleTree.map(node => (
                <TreeNode
                  key={node.id}
                  node={node}
                  depth={0}
                  expanded={expanded}
                  toggle={toggle}
                  editing={editing}
                  setEditing={setEditing}
                  handleSaveEdit={handleSaveEdit}
                  handleCancelEdit={handleCancelEdit}
                  handleStartEdit={handleStartEdit}
                  handleDelete={handleDelete}
                  updatePending={updateMutation.isPending}
                  deletePending={deleteMutation.isPending}
                  createMutation={createMutation}
                  openCreateModal={openCreateModal}
                />
              ))}
            </ul>
          </div>
        </div>
      </div>
      {showCreateModal && (
        <div style={{position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9999}}>
          <div style={{background: '#fff', padding: 20, borderRadius: 8, width: 600, maxWidth: '95%'}}>
            <h3 style={{marginTop: 0}}>Criar categoria</h3>
            <form onSubmit={(e) => { e.preventDefault(); submitCreate() }}>
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
    </section>
  )
}

function TreeNode({ node, depth, expanded, toggle, editing, setEditing, handleSaveEdit, handleCancelEdit, handleStartEdit, handleDelete, updatePending, deletePending, createMutation, openCreateModal }) {
  const isExpanded = expanded.has(node.id)
  const [showChildForm, setShowChildForm] = useState(false)
  const [childName, setChildName] = useState('')
  const [childDesc, setChildDesc] = useState('')

  const handleCreateChild = () => {
    if (!childName.trim()) {
      toast.error('Informe o nome da subcategoria.')
      return
    }
    createMutation.mutate({ params: [{ name: childName.trim(), description: childDesc || '', parent: Number(node.id || 0) }] })
    setChildName('')
    setChildDesc('')
    setShowChildForm(false)
    if (!isExpanded) toggle(node.id)
  }
  return (
    <li style={{paddingLeft: depth * 16, marginBottom: 6}}>
      <div style={{display: 'flex', alignItems: 'center', gap: 8}}>
        <button className="btn btn--icon" onClick={() => toggle(node.id)} aria-label={isExpanded ? 'Fechar' : 'Abrir'} style={{width: 28}}>
          {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        </button>
        <div style={{flex: 1}}>
          {editing && editing.id === node.id ? (
            <input value={editing.name} onChange={e => setEditing(ed => ({ ...ed, name: e.target.value }))} />
          ) : (
            <strong>{node.name}</strong>
          )}
          {node.description ? <div style={{fontSize: 12, color: '#666'}}>{node.description}</div> : null}
        </div>
        <div style={{display: 'flex', gap: 6, alignItems: 'center'}}>
          {editing && editing.id === node.id ? (
            <>
              <button className="btn btn--primary" onClick={handleSaveEdit} disabled={updatePending}>Salvar</button>
              <button className="btn" onClick={handleCancelEdit}>Cancelar</button>
            </>
          ) : (
            <>
              <button className="btn btn--outline" onClick={() => handleStartEdit(node)}><Edit2 size={14} /></button>
              <button className="btn btn--danger" onClick={() => handleDelete(node.id)} disabled={deletePending}><Trash2 size={14} /></button>
              <button className="btn btn--outline" onClick={() => openCreateModal(node.parent)} title="Criar na mesma raiz">Criar irmão</button>
              <button className="btn btn--outline" onClick={() => setShowChildForm(s => !s)} title="Adicionar categoria filha"><PlusCircle size={14} /></button>
            </>
          )}
        </div>
      </div>

      {showChildForm && (
        <div style={{marginTop: 6, marginLeft: Math.max(8, depth * 16), display: 'flex', gap: 8, alignItems: 'center'}}>
          <input placeholder="Nome da subcategoria" value={childName} onChange={e => setChildName(e.target.value)} style={{padding: 6, flex: '1 1 220px'}} />
          <input placeholder="Descrição (opcional)" value={childDesc} onChange={e => setChildDesc(e.target.value)} style={{padding: 6, flex: '1 1 220px'}} />
          <button className="btn btn--primary" onClick={() => handleCreateChild()} disabled={createMutation?.isPending || !childName.trim()}>Criar</button>
          <button className="btn" onClick={() => { setShowChildForm(false); setChildName(''); setChildDesc('') }}>Cancelar</button>
        </div>
      )}

      {isExpanded && node.children && node.children.length > 0 && (
        <ul style={{listStyle: 'none', paddingLeft: 0, marginTop: 6}}>
          {node.children.map(child => (
            <TreeNode
              key={child.id}
              node={child}
              depth={depth + 1}
              expanded={expanded}
              toggle={toggle}
              editing={editing}
              setEditing={setEditing}
              handleSaveEdit={handleSaveEdit}
              handleCancelEdit={handleCancelEdit}
              handleStartEdit={handleStartEdit}
              handleDelete={handleDelete}
              updatePending={updatePending}
              deletePending={deletePending}
              createMutation={createMutation}
              openCreateModal={openCreateModal}
            />
          ))}
        </ul>
      )}
    </li>
  )
}
