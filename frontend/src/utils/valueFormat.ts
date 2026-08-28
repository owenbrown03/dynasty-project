import type { ValueBasis } from '@/types';

export function isMarketValueBasis(
  basis: ValueBasis,
) {
  return (
    basis === 'ktc'
    || basis === 'fantasycalc'
    || basis === 'adp'
    || basis === 'ktc_redraft'
    || basis === 'fantasycalc_redraft'
  );
}

export function formatSelectedValue(
  value: number | null | undefined,
  basis: ValueBasis,
): string {
  if (value == null) {
    return '—';
  }

  if (isMarketValueBasis(basis)) {
    return Math.round(value).toLocaleString();
  }

  return value.toFixed(2);
}

export function formatAge(
  age: number | null | undefined,
): string {
  if (age == null) {
    return '—';
  }

  return age.toFixed(1);
}

export function formatMarketValue(
  value: number | null | undefined,
): string {
  if (value == null) {
    return '—';
  }

  return Math.round(value).toLocaleString();
}

export function formatWar(
  value: number | null | undefined,
): string {
  if (value == null) {
    return '—';
  }

  return value.toFixed(2);
}

export function formatDollarAmount(
  value: number | null | undefined,
): string {
  if (value == null) {
    return '--';
  }

  return `$${Math.round(value).toLocaleString()}`;
}
