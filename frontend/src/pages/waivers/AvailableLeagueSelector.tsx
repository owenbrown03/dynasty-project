import type { WaiverLeagueOption } from '@/types';


interface AvailableLeagueSelectorProps {
  leagues: WaiverLeagueOption[];
  selectedLeagueId: string | undefined;
  onChange: (
    leagueId: string,
  ) => void;
}


export const AvailableLeagueSelector = ({
  leagues,
  selectedLeagueId,
  onChange,
}: AvailableLeagueSelectorProps) => {
  return (
    <label className="available-league-selector">
      <span>League</span>

      <select
        value={selectedLeagueId ?? ''}
        onChange={(event) => {
          onChange(event.target.value);
        }}
      >
        {
          leagues.map((league) => (
            <option
              key={league.league_id}
              value={league.league_id}
            >
              {league.league_name}
            </option>
          ))
        }
      </select>
    </label>
  );
};