import type { DashboardLeague } from '@/types';

import { useNavigate } from 'react-router';


interface Props {

  leagues: DashboardLeague[];

}



export function DashboardLeagues({
  leagues
}: Props) {


  const navigate = useNavigate();



  return (

    <div className="league-dashboard-list">


      {
        leagues.map((league)=>(


          <div

            key={
              league.league_id
            }

            className="league-dashboard-card"

            onClick={() =>
              navigate(
                '/leagues',
                {
                  state:{
                    leagueId: league.league_id
                  }
                }
              )
            }

          >


            <h3>
              {league.league_name}
            </h3>


            <div>
              KTC:
              {" "}
              {league.ktc_value.toLocaleString()}
              {" "}
              #{league.ktc_rank}
            </div>


            <div>
              FC:
              {" "}
              {league.fc_value.toLocaleString()}
              {" "}
              #{league.fc_rank}
            </div>


            <div>
              Dynasty Starter WAR:
              {" "}
              {league.dynasty_starter_war.toFixed(2)}
              {" "}
              #{league.dynasty_starter_war_rank}
            </div>


            <div>
              Dynasty Roster WAR:
              {" "}
              {league.dynasty_roster_war.toFixed(2)}
              {" "}
              #{league.dynasty_roster_war_rank}
            </div>


            <div>
              Redraft Starter WAR:
              {" "}
              {league.redraft_starter_war.toFixed(2)}
              {" "}
              #{league.redraft_starter_war_rank}
            </div>


            <div>
              Redraft Roster WAR:
              {" "}
              {league.redraft_roster_war.toFixed(2)}
              {" "}
              #{league.redraft_roster_war_rank}
            </div>


            <div>
              Age:
              {" "}
              {
                league.average_age
                ?
                league.average_age.toFixed(1)
                :
                "N/A"
              }
            </div>


          </div>


        ))
      }


    </div>

  );

}