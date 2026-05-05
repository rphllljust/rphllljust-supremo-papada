// T048/T059: validação de tipo e tamanho de arquivo antes do upload

const ALLOWED_TYPES = new Set(['application/pdf', 'image/jpeg', 'image/jpg', 'image/png'])
const ALLOWED_EXTENSIONS = new Set(['.pdf', '.jpg', '.jpeg', '.png'])
const MAX_SIZE_BYTES = 5 * 1024 * 1024 // 5 MB

/**
 * Valida tipo e tamanho de um File antes do envio ao backend.
 * @param {File} file
 * @returns {{ valid: boolean, error: string|null }}
 */
export function validateUploadFile(file) {
  if (!file) return { valid: false, error: 'Nenhum arquivo selecionado.' }

  const ext = '.' + file.name.split('.').pop().toLowerCase()
  const mimeOk = ALLOWED_TYPES.has(file.type)
  const extOk = ALLOWED_EXTENSIONS.has(ext)

  if (!mimeOk || !extOk) {
    return {
      valid: false,
      error: `Tipo de arquivo não permitido: "${ext}". Use: PDF, JPG ou PNG.`,
    }
  }

  if (file.size > MAX_SIZE_BYTES) {
    const sizeMB = (file.size / 1024 / 1024).toFixed(1)
    return {
      valid: false,
      error: `Arquivo muito grande: ${sizeMB} MB. Limite máximo: 5 MB.`,
    }
  }

  return { valid: true, error: null }
}
