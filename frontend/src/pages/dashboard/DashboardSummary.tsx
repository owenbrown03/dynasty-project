import type { DashboardSummary } from '@/types';


interface Props {

  summary: DashboardSummary;

}


export function DashboardSummary({
  summary
}: Props) {


  return (

    <div className="summary-grid">


      <div className="summary-card">
        <h3>Leagues</h3>
        <p>{summary.league_count}</p>
      </div>


      <div className="summary-card">
        <h3>Players</h3>
        <p>{summary.player_count}</p>
      </div>


      <div className="summary-card">
        <h3>Total KTC</h3>
        <p>
          {summary.total_ktc_value.toLocaleString()}
        </p>
      </div>


      <div className="summary-card">
        <h3>Total FC</h3>
        <p>
          {summary.total_fc_value.toLocaleString()}
        </p>
      </div>


      <div className="summary-card">
        <h3>Starter WAR</h3>
        <p>
          {summary.total_starter_war.toFixed(2)}
        </p>
      </div>


      <div className="summary-card">
        <h3>Roster WAR</h3>
        <p>
          {summary.total_roster_war.toFixed(2)}
        </p>
      </div>


      <div className="summary-card">
        <h3>Average Age</h3>
        <p>
          {summary.average_age.toFixed(1)}
        </p>
      </div>


    </div>

  );

}