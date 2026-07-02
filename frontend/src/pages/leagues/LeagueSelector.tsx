import type { LeagueOverview } from '@/types';


interface Props {

  leagues: LeagueOverview[];

  selectedLeague?: string;

  onSelect:
    (league_id:string)=>void;

}



export function LeagueSelector({

  leagues,

  selectedLeague,

  onSelect

}:Props){


  return (

    <select

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

              {league.league_name}

            </option>

          )
        )
      }


    </select>

  );

}