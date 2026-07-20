import {
  addPayoutRow,
  ordinal,
  parseAmount,
  type FinanceSettingsDraft,
} from './finance.utils';

interface FinancePayoutEditorProps<TDraft extends FinanceSettingsDraft> {
  draft: TDraft;
  onChange: (
    nextDraft: TDraft,
  ) => void;
}

export function FinancePayoutEditor<TDraft extends FinanceSettingsDraft>({
  draft,
  onChange,
}: FinancePayoutEditorProps<TDraft>) {
  return (
    <div className="finance-payout-editor">
      <div className="finance-payout-editor-header">
        <span>Payout structure</span>

        <button
          type="button"
          className="button-secondary"
          onClick={() => {
            const nextRows = addPayoutRow(draft).payoutStructure;
            onChange(
              {
                ...draft,
                payoutStructure: nextRows,
              },
            );
          }}
        >
          Add place
        </button>
      </div>

      <div className="finance-payout-rows">
        {
          draft.payoutStructure.map((row, index) => (
            <div
              key={`${row.place}-${index}`}
              className="finance-payout-row"
            >
              <label>
                <span>Place</span>
                <input
                  type="number"
                  min="1"
                  step="1"
                  value={row.place}
                  onChange={(event) => {
                    const nextRows = [...draft.payoutStructure];
                    nextRows[index] = {
                      ...row,
                      place: event.target.value,
                    };
                    onChange({
                      ...draft,
                      payoutStructure: nextRows,
                    });
                  }}
                />
              </label>

              <label>
                <span>{ordinal(parseAmount(row.place) || 1)} payout</span>
                <input
                  type="number"
                  min="0"
                  step="1"
                  value={row.amount}
                  onChange={(event) => {
                    const nextRows = [...draft.payoutStructure];
                    nextRows[index] = {
                      ...row,
                      amount: event.target.value,
                    };
                    onChange({
                      ...draft,
                      payoutStructure: nextRows,
                    });
                  }}
                />
              </label>

              <button
                type="button"
                className="button-secondary"
                disabled={draft.payoutStructure.length === 1}
                onClick={() => {
                  onChange({
                    ...draft,
                    payoutStructure: draft.payoutStructure.filter(
                      (_, rowIndex) => rowIndex !== index,
                    ),
                  });
                }}
              >
                Remove
              </button>
            </div>
          ))
        }
      </div>
    </div>
  );
}
