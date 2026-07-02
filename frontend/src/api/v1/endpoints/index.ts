import { client } from '../client';
import { authEndpoints } from './auth.endpoints';
import { bootstrapEndpoints } from './bootstrap.endpoints';
import { authEndpoints as sleeperAuthEndpoints } from './sleeper/auth.endpoints';
import { connectionEndpoints } from './sleeper/connection.endpoints';
import { leaguesEndpoints } from './sleeper/leagues.endpoints';
import { playerEndpoints } from './sleeper/player.endpoints';
import { tradeEndpoints } from './sleeper/trade.endpoints';
import { userEndpoints } from './sleeper/user.endpoints';
import { writeEndpoints } from './sleeper/write.endpoints';

export const api = {
  auth: authEndpoints(client, '/auth'),
  bootstrap: bootstrapEndpoints(client, '/bootstrap'),
  sleeper_auth: sleeperAuthEndpoints(client, '/sleeper/auth'),
  connection: connectionEndpoints(client, '/sleeper/connection'),
  leagues: leaguesEndpoints(client, '/sleeper/leagues'),
  players: playerEndpoints(client, '/sleeper/players'),
  trades: tradeEndpoints(client, '/sleeper/trades'),
  users: userEndpoints(client, '/sleeper/users'),
  write: writeEndpoints(client, '/sleeper/write'),
};