export function fmtINR(value) {
  const num = parseFloat(value)
  if (isNaN(num)) return '—'
  return '₹' + num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
