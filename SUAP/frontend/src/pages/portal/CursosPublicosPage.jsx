import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { MapPin, Clock, BookOpen, Users } from 'lucide-react'

import { portalApi } from '@/api/endpoints'

function getDashboardHref() {
  if (typeof window !== 'undefined' && window.location.port === '5173') {
    return 'http://localhost:8010/'
  }
  return '/'
}

export default function CursosPublicosPage() {
  const [search, setSearch] = useState('')
  const [unidade, setUnidade] = useState('')
  const [eixo, setEixo] = useState('')
  const [filtroAtivo, setFiltroAtivo] = useState({ search: '', unidade: '', eixo: '' })
  const dashboardHref = getDashboardHref()

  const { data: cursosData, isLoading } = useQuery({
    queryKey: ['cursos-publicos', filtroAtivo],
    queryFn: () =>
      portalApi.cursos({
        search: filtroAtivo.search || undefined,
        unidade: filtroAtivo.unidade || undefined,
        eixo_tecnologico: filtroAtivo.eixo || undefined,
      }).then((response) => response.data),
    staleTime: 60_000,
  })

  const { data: unidadesData } = useQuery({
    queryKey: ['unidades-publicas'],
    queryFn: () => portalApi.unidades().then((response) => response.data),
    staleTime: 300_000,
  })

  const eixos = useMemo(() => {
    const cursos = cursosData?.results ?? cursosData ?? []
    const values = new Set(cursos.map((curso) => curso.eixo_tecnologico).filter(Boolean))
    return [...values].sort()
  }, [cursosData])

  const cursos = cursosData?.results ?? cursosData ?? []
  const unidades = unidadesData?.results ?? unidadesData ?? []

  const handleBuscar = () => {
    setFiltroAtivo({ search, unidade, eixo })
  }

  const handleLimpar = () => {
    setSearch('')
    setUnidade('')
    setEixo('')
    setFiltroAtivo({ search: '', unidade: '', eixo: '' })
  }

  return (
    <>
      <div className="breadcrumb">
        <a href={dashboardHref}>Inicio</a>
        <span className="breadcrumb__sep">/</span>
        <a href="#">Cursos</a>
        <span className="breadcrumb__sep">/</span>
        <span className="breadcrumb__current">Buscar cursos</span>
      </div>

      <div className="portal-page">
        <div className="portal-page__header">
          <h1 className="portal-page__title">Buscar cursos</h1>
          <p className="portal-page__subtitle">
            Encontre o curso ideal no IDEP-ETEC e use os filtros para refinar a busca.
          </p>
        </div>

        <div className="search-card">
          <div className="search-card__title">Buscar cursos</div>

          <div style={{ position: 'relative' }}>
            <input
              className="search-card__main-input"
              type="text"
              placeholder="Digite o nome do curso..."
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              onKeyDown={(event) => event.key === 'Enter' && handleBuscar()}
            />
          </div>

          <div className="search-card__filters">
            <div className="filter-group">
              <label>Campus</label>
              <select value={unidade} onChange={(event) => setUnidade(event.target.value)}>
                <option value="">Todos os campi</option>
                {unidades.map((item) => (
                  <option key={item.id} value={item.id}>{item.nome}</option>
                ))}
              </select>
            </div>

            <div className="filter-group">
              <label>Eixo tecnologico</label>
              <select value={eixo} onChange={(event) => setEixo(event.target.value)}>
                <option value="">Todos os eixos</option>
                {eixos.map((item) => (
                  <option key={item} value={item}>{item}</option>
                ))}
              </select>
            </div>

            <div className="filter-group">
              <label>Nivel</label>
              <select>
                <option value="">Todos os niveis</option>
                <option value="tecnico">Tecnico</option>
                <option value="qualificacao">Qualificacao</option>
              </select>
            </div>
          </div>

          <div className="search-card__filters-row2">
            <div className="filter-group">
              <label>Turno</label>
              <select>
                <option value="">Todos os turnos</option>
                <option value="MANHA">Manha</option>
                <option value="TARDE">Tarde</option>
                <option value="NOITE">Noite</option>
                <option value="INTEGRAL">Integral</option>
              </select>
            </div>
            <div />
          </div>

          <div className="search-card__actions">
            <button className="btn btn--primary" onClick={handleBuscar}>
              Buscar cursos
            </button>
            <button className="btn btn--outline" onClick={handleLimpar}>
              Limpar filtros
            </button>
          </div>
        </div>

        {isLoading ? (
          <div className="loading-screen" style={{ minHeight: 200 }}>
            <div className="spinner" />
          </div>
        ) : (
          <>
            <p className="results-header">
              <strong>{cursos.length}</strong> curso{cursos.length !== 1 ? 's' : ''} encontrado{cursos.length !== 1 ? 's' : ''}
            </p>

            {cursos.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '48px 0', color: 'var(--color-gray-400)' }}>
                Nenhum curso encontrado para os filtros selecionados.
              </div>
            ) : (
              <div className="courses-grid">
                {cursos.map((curso) => (
                  <CourseCard key={curso.id} curso={curso} />
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </>
  )
}

function CourseCard({ curso }) {
  const nivel = curso.eixo_tecnologico ? 'Tecnico' : 'Qualificacao'
  const cargaHoras = curso.carga_horaria ? `${curso.carga_horaria}h` : null

  return (
    <div className="course-card">
      <div className="course-card__header">
        <h3 className="course-card__title">{curso.nome}</h3>
        <span className="course-card__badge">{nivel}</span>
      </div>

      <div className="course-card__body">
        <p className="course-card__desc">
          {curso.eixo_tecnologico
            ? `Curso voltado para o eixo tecnologico de ${curso.eixo_tecnologico}.`
            : 'Formacao tecnica e profissional pelo IDEP-ETEC.'}
        </p>

        <div className="course-card__info">
          {curso.unidade_nome && (
            <div className="course-card__info-item">
              <MapPin size={13} />
              <span>{curso.unidade_nome}</span>
            </div>
          )}
          {cargaHoras && (
            <div className="course-card__info-item">
              <Clock size={13} />
              <span>Carga horaria - {cargaHoras}</span>
            </div>
          )}
          {curso.eixo_tecnologico && (
            <div className="course-card__info-item">
              <BookOpen size={13} />
              <span>{curso.eixo_tecnologico}</span>
            </div>
          )}
          <div className="course-card__info-item">
            <Users size={13} />
            <span>Vagas disponiveis</span>
          </div>
        </div>
      </div>

      <div className="course-card__footer">
        <Link
          to={`/portal/cursos/${curso.id}`}
          className="btn btn--primary btn--full btn--sm"
        >
          Ver detalhes do curso
        </Link>
      </div>
    </div>
  )
}
