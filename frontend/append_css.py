import sys

css = """
/* ===== Bulk Offers league-block redesign ===== */

.bulk-trade-league-block {
  border: 1px solid var(--color-border);
  border-radius: 10px;
  background: var(--color-surface);
  overflow: hidden;
  transition: border-color 0.15s;
}

.bulk-trade-league-block.selected {
  border-color: var(--color-accent, #6366f1);
  background: var(--color-accent-subtle, rgba(99, 102, 241, 0.05));
}

.bulk-trade-league-block-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-bottom: 1px solid var(--color-border);
  cursor: pointer;
  user-select: none;
}

.bulk-trade-league-block.selected .bulk-trade-league-block-header {
  border-bottom-color: var(--color-accent-border, rgba(99, 102, 241, 0.25));
}

.bulk-trade-league-check {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.bulk-trade-league-check input[type="checkbox"] {
  flex-shrink: 0;
  width: 15px;
  height: 15px;
  accent-color: var(--color-accent, #6366f1);
  cursor: pointer;
}

.bulk-trade-league-copy {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.bulk-trade-league-copy strong {
  font-size: 13px;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.bulk-trade-league-copy small {
  color: var(--color-text-muted);
  font-size: 11px;
  white-space: nowrap;
}

.bulk-trade-league-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.bulk-trade-select-all,
.bulk-trade-select-none {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  border: 1px solid var(--color-border);
  border-radius: 5px;
  background: transparent;
  color: var(--color-text-muted);
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: color 0.1s, border-color 0.1s;
}

.bulk-trade-select-all:hover,
.bulk-trade-select-none:hover {
  color: var(--color-text);
  border-color: var(--color-text-muted);
}

.bulk-trade-select-all:disabled,
.bulk-trade-select-none:disabled {
  opacity: 0.4;
  cursor: default;
  pointer-events: none;
}

.bulk-trade-counterparty-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.bulk-trade-counterparty {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 14px;
  border-bottom: 1px solid var(--color-border);
  cursor: pointer;
  transition: background 0.1s;
}

.bulk-trade-counterparty:last-child {
  border-bottom: none;
}

.bulk-trade-counterparty:hover {
  background: var(--color-surface-raised);
}

.bulk-trade-counterparty.selected {
  background: var(--color-accent-subtle, rgba(99, 102, 241, 0.06));
}

.bulk-trade-counterparty-check {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.bulk-trade-counterparty-check input[type="checkbox"] {
  flex-shrink: 0;
  width: 14px;
  height: 14px;
  accent-color: var(--color-accent, #6366f1);
  cursor: pointer;
}

.bulk-trade-result-copy {
  display: flex;
  flex-direction: column;
  gap: 2px;
  line-height: 1.35;
}

.bulk-trade-result-copy small {
  color: var(--color-text-muted);
  font-size: 11px;
}
"""

with open('/var/folders/6l/bynnpxf56fv8ml6lr_1l6gj00000gn/T/opencode/worktrees/wt-rosterlab/frontend/src/pages/trades/TradesPage.css', 'a') as f:
    f.write(css)

print("Appended CSS")
