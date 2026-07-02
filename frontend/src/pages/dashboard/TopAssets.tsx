import type { DashboardAsset } from '@/types';


interface Props {

  assets: DashboardAsset[];

}



export function TopAssets({
  assets
}: Props) {


  return (

    <div>


      <h2>
        Top Assets
      </h2>


      {
        assets.map(player=>(


          <div
            key={player.player_id}
          >

            <b>
              {player.name}
            </b>


            {" "}
            {player.position}
            {" "}
            {player.team}


            <span>
              WAR:
              {" "}
              {player.roster_war.toFixed(2)}
            </span>


          </div>


        ))
      }


    </div>

  );

}