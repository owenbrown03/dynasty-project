interface WaiversTabsProps {
  activeTab: (
    'overview'
    | 'recent-drops'
    | 'available'
    | 'bulk'
  );

  onChange: (
    tab: (
      'overview'
      | 'recent-drops'
      | 'available'
      | 'bulk'
    ),
  ) => void;
}


export const WaiversTabs = ({
  activeTab,
  onChange,
}: WaiversTabsProps) => {
  return (
    <div
      className="waivers-tabs"
      role="tablist"
      aria-label="Waiver assistant views"
    >
      <button
        className={
          `waivers-tab ${
            activeTab === 'overview'
              ? 'active'
              : ''
          }`
        }
        onClick={() => {
          onChange('overview');
        }}
      >
        Overview
      </button>

      <button
        className={
          `waivers-tab ${
            activeTab === 'available'
              ? 'active'
              : ''
          }`
        }
        onClick={() => {
          onChange('available');
        }}
      >
        Available Players
      </button>

      <button
        className={
          `waivers-tab ${
            activeTab === 'recent-drops'
              ? 'active'
              : ''
          }`
        }
        onClick={() => {
          onChange('recent-drops');
        }}
      >
        Recent Drops
      </button>

      <button
        className={
          `waivers-tab ${
            activeTab === 'bulk'
              ? 'active'
              : ''
          }`
        }
        onClick={() => {
          onChange('bulk');
        }}
      >
        Bulk Claims
      </button>
    </div>
  );
};
