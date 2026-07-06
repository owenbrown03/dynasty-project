import type { ValueBasis } from '@/types';

import { VALUE_BASIS_OPTIONS } from './waiver.constants';


interface ValueBasisSelectorProps {
  valueBasis: ValueBasis;
  onChange: (valueBasis: ValueBasis) => void;
}


export const ValueBasisSelector = ({
  valueBasis,
  onChange,
}: ValueBasisSelectorProps) => {
  return (
    <label className="waivers-value-selector">
      <span>Value Basis</span>

      <select
        value={valueBasis}
        onChange={(event) => {
          onChange(
            event.target.value as ValueBasis,
          );
        }}
      >
        {
          VALUE_BASIS_OPTIONS.map((option) => (
            <option
              key={option.value}
              value={option.value}
            >
              {option.label}
            </option>
          ))
        }
      </select>
    </label>
  );
};