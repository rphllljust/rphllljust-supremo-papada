/**
 * Página de Login — usa React Hook Form + AuthContext.
 * Redireciona para /app/dashboard após login bem-sucedido.
 */
import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { formatCpf } from '@/utils/cpf'
import toast from 'react-hot-toast'

const PERFIL_OPTIONS = [
  { value: 'SECRETARIA', label: 'Secretaria' },
  { value: 'COORDENACAO', label: 'Coordenacao/Consulta' },
  { value: 'PROFESSOR', label: 'Professor' },
  { value: 'ADMIN', label: 'Administrador' },
]

export default function LoginPage() {
  const { login, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const nextPath = searchParams.get('next') || '/dashboard'

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm()

  const cpfField = register('cpf', { required: 'Informe o CPF' })

  const handleCpfChange = (event) => {
    const formattedValue = formatCpf(event.target.value)
    setValue('cpf', formattedValue, { shouldDirty: true, shouldTouch: true, shouldValidate: true })
  }

  const handleCpfPaste = (event) => {
    event.preventDefault()
    const pastedText = event.clipboardData?.getData('text') || ''
    const formattedValue = formatCpf(pastedText)
    setValue('cpf', formattedValue, { shouldDirty: true, shouldTouch: true, shouldValidate: true })
  }

  useEffect(() => {
    if (isAuthenticated) navigate(nextPath, { replace: true })
  }, [isAuthenticated, navigate, nextPath])

  const onSubmit = async (formData) => {
    try {
      await login(formData)
      toast.success('Login realizado com sucesso!')
      navigate(nextPath, { replace: true })
    } catch (err) {
      const data = err.response?.data
      const msg = data?.detail || data?.cpf?.[0] || data?.perfil?.[0] || 'Credenciais inválidas.'
      toast.error(msg)
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-card__header">
          <div className="login-card__logo">SUAP</div>
          <h1 className="login-card__title">Sistema Unificado de Administração Pública</h1>
          <p className="login-card__subtitle">IDEP — Instituto de Desenvolvimento e Educação Profissional</p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="login-form">
          <div className="form-field">
            <label htmlFor="cpf">CPF</label>
            <input
              id="cpf"
              type="text"
              autoComplete="username"
              placeholder="000.000.000-00"
              inputMode="numeric"
              maxLength={14}
              {...cpfField}
              onChange={handleCpfChange}
              onPaste={handleCpfPaste}
              aria-invalid={!!errors.cpf}
            />
            {errors.cpf && (
              <span className="field-error">{errors.cpf.message}</span>
            )}
          </div>

          <div className="form-field">
            <label htmlFor="perfil">Perfil</label>
            <select
              id="perfil"
              className="select"
              defaultValue="SECRETARIA"
              {...register('perfil', { required: 'Selecione o perfil' })}
              aria-invalid={!!errors.perfil}
            >
              {PERFIL_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
            {errors.perfil && (
              <span className="field-error">{errors.perfil.message}</span>
            )}
          </div>

          <div className="form-field">
            <label htmlFor="password">Senha</label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              placeholder="Senha"
              {...register('password', { required: 'Informe a senha' })}
              aria-invalid={!!errors.password}
            />
            {errors.password && (
              <span className="field-error">{errors.password.message}</span>
            )}
          </div>

          <button type="submit" className="btn btn--primary btn--full" disabled={isSubmitting}>
            {isSubmitting ? 'Entrando...' : 'Entrar'}
          </button>
        </form>
      </div>
    </div>
  )
}
