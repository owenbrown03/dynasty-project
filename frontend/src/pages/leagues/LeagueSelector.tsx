import type { LeagueSelectorItem } from '@/types';

interface Props {
  leagues: LeagueSelectorItem[];
  selectedLeague?: string;
  onSelect: (league_id: string) => void;
}



export function LeagueSelector({
  leagues,
  selectedLeague,
  onSelect
}:Props){
  return (
    <select
      className="leagues-selector-input"
      value={
        selectedLeague ?? ''
      }
      onChange={
        e =>
          onSelect(
            e.target.value
          )
      }

    >


      <option value="">
        Select League
      </option>
      {
        leagues.map(
          league => (
            <option
              key={
                league.league_id
              }
              value={
                league.league_id
              }
            >
              {league.is_focused ? '\u2605 ' : ''}
              {league.league_name}
              {league.is_hidden ? ' (hidden)' : ''}
              {league.season ? ` - ${league.season}` : ''}
            </option>
          )
        )
      }
    </select>
  );
}
