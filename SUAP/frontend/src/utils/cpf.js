export function normalizeCpf(value) {
  return String(value || '').replace(/\D/g, '').slice(0, 11)
}

export function formatCpf(value) {
  const digits = normalizeCpf(value)

  if (digits.length <= 3) return digits
  if (digits.length <= 6) return `${digits.slice(0, 3)}.${digits.slice(3)}`
  if (digits.length <= 9) return `${digits.slice(0, 3)}.${digits.slice(3, 6)}.${digits.slice(6)}`

  return `${digits.slice(0, 3)}.${digits.slice(3, 6)}.${digits.slice(6, 9)}-${digits.slice(9)}`
}

export function validateCpf(value) {
  const digits = normalizeCpf(value)

  if (digits.length !== 11) return false

  // Rejeita sequências repetidas (000...0, 111...1, etc.)
  if (/^(\d)\1{10}$/.test(digits)) return false

  function calcDigit(partial) {
    const weight = partial.length + 1
    const sum = partial.split('').reduce((acc, d, i) => acc + Number(d) * (weight - i), 0)
    const remainder = 11 - (sum % 11)
    return remainder >= 10 ? 0 : remainder
  }

  const d1 = calcDigit(digits.slice(0, 9))
  const d2 = calcDigit(digits.slice(0, 9) + d1)

  return Number(digits[9]) === d1 && Number(digits[10]) === d2
}