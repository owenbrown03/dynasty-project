import { client } from '../client';
import { authEndpoints } from './auth.endpoints';
import { userEndpoints } from './user.endpoints';
import { tradeEndpoints } from './trade.endpoints';
import { playerEndpoints } from './player.endpoints';

export const api = {
  auth: authEndpoints(client, '/auth'),
  users: userEndpoints(client, '/users'),
  trades: tradeEndpoints(client, '/trades'),
  players: playerEndpoints(client, '/players'),
};