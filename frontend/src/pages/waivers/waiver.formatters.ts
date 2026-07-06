import type { ValueBasis } from '@/types';


export function formatSelectedValue(
  value: number | null,
  basis: ValueBasis,
): string {
  if (value === null) {
    return '—';
  }

  const isMarketValue = (
    basis === 'ktc'
    || basis === 'fantasycalc'
  );

  if (isMarketValue) {
    return Math.round(value).toLocaleString();
  }

  return value.toFixed(3);
}


export function formatAge(
  age: number | null,
): string {
  if (age === null) {
    return '—';
  }

  return age.toFixed(1);
}


export function formatMarketValue(
  value: number | null,
): string {
  if (value === null) {
    return '—';
  }

  return Math.round(value).toLocaleString();
}


export function formatWar(
  value: number | null,
): string {
  if (value === null) {
    return '—';
  }

  return value.toFixed(3);
}