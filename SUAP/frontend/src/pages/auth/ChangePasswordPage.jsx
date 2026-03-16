import { useMutation } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { KeyRound, ShieldCheck } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'

import { authApi } from '@/api/endpoints'
import { useAuth } from '@/context/AuthContext'

function getErrorMessage(error) {
  const data = error?.response?.data
  if (!data) {
    return 'Nao foi possivel alterar a senha.'
  }

  if (typeof data.detail === 'string') {
    return data.detail
  }

  const firstValue = Object.values(data)[0]
  return Array.isArray(firstValue) ? firstValue[0] : (firstValue || 'Nao foi possivel alterar a senha.')
}

export default function ChangePasswordPage() {
  const navigate = useNavigate()
  const { user, refreshUser } = useAuth()
  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors },
  } = useForm({
    defaultValues: {
      current_password: '',
      new_password: '',
      new_password_confirm: '',
    },
  })

  const newPassword = watch('new_password')

  const changePasswordMutation = useMutation({
    mutationFn: (payload) => authApi.changePassword(payload),
    onSuccess: async () => {
      await refreshUser()
      reset()
      toast.success('Senha alterada com sucesso.')
      navigate('/dashboard', { replace: true })
    },
    onError: (error) => {
      toast.error(getErrorMessage(error))
    },
  })

  return (
    <div className="page page--narrow">
      <nav className="profile-breadcrumb">
        <Link to="/dashboard">Inicio</Link>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <span>Comum</span>
        <span className="profile-breadcrumb__sep">&gt;</span>
        <span>Alterar senha</span>
      </nav>

      <div className="page-header">
        <div>
          <h1 className="page-title">Alterar senha</h1>
          <p className="page-subtitle">{user?.must_change_password ? 'Este e o seu primeiro acesso. Defina uma nova senha para continuar.' : 'Atualize sua credencial de acesso ao SUAP.'}</p>
        </div>
      </div>

      <section className="dashboard-card password-card">
        <div className="password-card__hero">
          <div className="password-card__icon"><KeyRound size={28} /></div>
          <div>
            <h2>Seguranca da conta</h2>
            <p>Informe sua senha atual e defina uma nova senha para continuar usando o sistema.</p>
          </div>
        </div>

        <form className="password-form" onSubmit={handleSubmit((values) => changePasswordMutation.mutate(values))}>
          <div className="form-field">
            <label htmlFor="current_password">Senha atual</label>
            <input
              id="current_password"
              type="password"
              autoComplete="current-password"
              {...register('current_password', { required: 'Informe sua senha atual.' })}
              aria-invalid={Boolean(errors.current_password)}
            />
            {errors.current_password ? <span className="field-error">{errors.current_password.message}</span> : null}
          </div>

          <div className="form-field">
            <label htmlFor="new_password">Nova senha</label>
            <input
              id="new_password"
              type="password"
              autoComplete="new-password"
              {...register('new_password', {
                required: 'Informe a nova senha.',
                minLength: { value: 8, message: 'A nova senha deve ter pelo menos 8 caracteres.' },
              })}
              aria-invalid={Boolean(errors.new_password)}
            />
            {errors.new_password ? <span className="field-error">{errors.new_password.message}</span> : null}
          </div>

          <div className="form-field">
            <label htmlFor="new_password_confirm">Confirmacao da nova senha</label>
            <input
              id="new_password_confirm"
              type="password"
              autoComplete="new-password"
              {...register('new_password_confirm', {
                required: 'Confirme a nova senha.',
                validate: (value) => value === newPassword || 'A confirmacao deve ser igual a nova senha.',
              })}
              aria-invalid={Boolean(errors.new_password_confirm)}
            />
            {errors.new_password_confirm ? <span className="field-error">{errors.new_password_confirm.message}</span> : null}
          </div>

          <div className="password-card__tip">
            <ShieldCheck size={18} />
            <span>Use uma senha forte, diferente da atual e com pelo menos 8 caracteres.</span>
          </div>

          <div className="page-header__actions">
            <button type="submit" className="btn btn--primary" disabled={changePasswordMutation.isPending}>
              {changePasswordMutation.isPending ? 'Alterando senha...' : 'Salvar nova senha'}
            </button>
            <Link to="/dashboard" className="btn btn--outline">Cancelar</Link>
          </div>
        </form>
      </section>
    </div>
  )
}