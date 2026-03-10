import { Component } from 'react'
import { debugLog, normalizeError } from '@/utils/debug'

export default class AppErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    debugLog('error', 'react.error_boundary.triggered', {
      error: normalizeError(error),
      componentStack: errorInfo?.componentStack,
    })
  }

  handleRetry = () => {
    debugLog('info', 'react.error_boundary.retry')
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (!this.state.hasError) {
      return this.props.children
    }

    return (
      <div className="page-error" role="alert">
        <h2 className="page-error__title">Nao foi possivel carregar esta tela.</h2>
        <p className="page-error__description">
          O layout foi mantido ativo para evitar a tela branca. Tente abrir a pagina novamente.
        </p>
        {this.state.error?.message ? (
          <pre className="page-error__details">{this.state.error.message}</pre>
        ) : null}
        <div className="page-error__actions">
          <button type="button" className="btn btn--primary" onClick={this.handleRetry}>
            Tentar novamente
          </button>
          <button type="button" className="btn" onClick={() => window.location.reload()}>
            Recarregar aplicacao
          </button>
        </div>
      </div>
    )
  }
}