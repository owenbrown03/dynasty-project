export function formatNumber(value: number | null | undefined, decimals = 2) {
  if (value === null || value === undefined) return '-';
  return value.toFixed(decimals);
}