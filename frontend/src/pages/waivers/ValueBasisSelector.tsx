import type { ValueBasis } from '@/types';
import { useBootstrapContext } from '@/context/useBootstrapContext';

import { getValueBasisOptions } from './waiver.constants';


interface ValueBasisSelectorProps {
  valueBasis: ValueBasis;
  onChange: (valueBasis: ValueBasis) => void;
}


export const ValueBasisSelector = ({
  valueBasis,
  onChange,
}: ValueBasisSelectorProps) => {
  const { bootstrap } = useBootstrapContext();
  const options = getValueBasisOptions(
    bootstrap?.authenticated ?? false,
  );

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
          options.map((option) => (
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
