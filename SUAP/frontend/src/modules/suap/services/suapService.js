import { suapModules, findSuapPage } from '../config/suapModules'

export const suapService = {
  listarModulos() {
    return suapModules
  },
  listarPaginasModulo(modulePath) {
    return suapModules.find((mod) => mod.path === modulePath)?.children || []
  },
  buscarDadosPublicos() {
    return Promise.resolve({ modules: suapModules })
  },
  abrirServicoPublico(pathname) {
    return findSuapPage(pathname)
  },
  async consultarApiSuap() {
    throw new Error('Endpoint SUAP ainda n?o configurado para esta funcionalidade')
  },
  async autenticarSuap() {
    throw new Error('Autentica??o SUAP depende de acesso/autoriza??o espec?fica')
  },
}
