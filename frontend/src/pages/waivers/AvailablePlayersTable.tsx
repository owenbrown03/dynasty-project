import { Send } from 'lucide-react';

import { PlayerAvatar } from '@/components/players/PlayerAvatar';
import type {
  ValueBasis,
  WaiverAvailablePlayer,
  WaiverAvailablePlayersResponse,
} from '@/types';

import {
  formatAge,
  formatMarketValue,
  formatSelectedValue,
  formatWar,
} from './waiver.formatters';


interface AvailablePlayersTableProps {
  data: WaiverAvailablePlayersResponse;
  canWrite: boolean;
  claimDisabledReason?: string;

  onClaim: (
    player: WaiverAvailablePlayer,
  ) => void;
}


interface AvailablePlayersRowProps {
  player: WaiverAvailablePlayer;
  valueBasis: ValueBasis;
  valueLabel: string;
  canWrite: boolean;
  claimDisabledReason?: string;

  onClaim: (
    player: WaiverAvailablePlayer,
  ) => void;
}


const AvailablePlayersRow = ({
  player,
  valueBasis,
  valueLabel,
  canWrite,
  claimDisabledReason,
  onClaim,
}: AvailablePlayersRowProps) => {
  return (
    <tr>
      <td className="available-player-name-cell">
        <div className="player-with-avatar">
          <PlayerAvatar
            playerId={player.player_id}
            name={player.name}
            size="sm"
          />

          <div className="player-with-avatar-copy">
            <strong>
              {player.name}
            </strong>

            <span>
              {player.underdog_position_rank ?? '—'}
            </span>
          </div>
        </div>
      </td>

      <td>
        {player.position ?? '—'}
      </td>

      <td>
        {player.team ?? 'FA'}
      </td>

      <td>
        {formatAge(player.age)}
      </td>

      <td className="available-selected-value">
        <strong>
          {
            formatSelectedValue(
              player.selected_value,
              valueBasis,
            )
          }
        </strong>

        <span>
          {valueLabel}
        </span>
      </td>

      <td>
        {formatMarketValue(player.ktc_value)}
      </td>

      <td>
        {formatMarketValue(player.fc_value)}
      </td>

      <td>
        {formatWar(player.dynasty_roster_war)}
      </td>

      <td>
        {formatWar(player.redraft_roster_war)}
      </td>

      <td>
        <button
          className="button-secondary available-claim-button"
          onClick={() => {
            onClaim(player);
          }}
          disabled={!canWrite}
          title={
            claimDisabledReason
            ?? (
              canWrite
                ? 'Build a waiver claim'
                : 'Enable Sleeper write access to submit claims'
            )
          }
        >
          <Send size={13} />
          Claim
        </button>
      </td>
    </tr>
  );
};


export const AvailablePlayersTable = ({
  data,
  canWrite,
  claimDisabledReason,
  onClaim,
}: AvailablePlayersTableProps) => {
  return (
    <div className="available-players-table-wrapper">
      <table className="available-players-table">
        <thead>
          <tr>
            <th>Player</th>
            <th>Pos</th>
            <th>Team</th>
            <th>Age</th>
            <th>{data.value_label}</th>
            <th>KTC</th>
            <th>FC</th>
            <th>Dynasty WAR</th>
            <th>Redraft WAR</th>
            <th />
          </tr>
        </thead>

        <tbody>
          {
            data.players.map((player) => (
              <AvailablePlayersRow
                key={player.player_id}
                player={player}
                valueBasis={data.value_basis}
                valueLabel={data.value_label}
                canWrite={canWrite}
                claimDisabledReason={claimDisabledReason}
                onClaim={onClaim}
              />
            ))
          }
        </tbody>
      </table>
    </div>
  );
};
