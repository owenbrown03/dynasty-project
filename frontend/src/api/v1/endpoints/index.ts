import { client } from '../client';
import { adpEndpoints } from './adp.endpoints';
import { authEndpoints } from './auth.endpoints';
import { bootstrapEndpoints } from './bootstrap.endpoints';
import { authEndpoints as sleeperAuthEndpoints } from './sleeper/auth.endpoints';
import { connectionEndpoints } from './sleeper/connection.endpoints';
import { leaguesEndpoints } from './sleeper/leagues.endpoints';
import { personalValuesEndpoints } from './sleeper/personal-values.endpoints';
import { playerEndpoints } from './sleeper/player.endpoints';
import { tradeEndpoints } from './sleeper/trade.endpoints';
import { userEndpoints } from './sleeper/user.endpoints';
import { waiversEndpoints } from './sleeper/waivers.endpoints';

export const api = {
  adp: adpEndpoints(client, '/adp'),
  auth: authEndpoints(client, '/auth'),
  bootstrap: bootstrapEndpoints(client, '/bootstrap'),
  sleeper_auth: sleeperAuthEndpoints(client, '/sleeper/auth'),
  connection: connectionEndpoints(client, '/sleeper/connection'),
  leagues: leaguesEndpoints(client, '/sleeper/leagues'),
  personal_values: personalValuesEndpoints(client, '/sleeper/personal-values'),
  players: playerEndpoints(client, '/sleeper/players'),
  trades: tradeEndpoints(client, '/sleeper/trades'),
  users: userEndpoints(client, '/sleeper/users'),
  waivers: waiversEndpoints(client, '/sleeper/waivers'),
};
