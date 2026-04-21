import schemas

def schema_to_db(schema) -> dict:
    return schema.model_dump()

def league_to_db(schema: schemas.SleeperLeague) -> dict:
    flat_data = schema.model_dump(exclude={'settings', 'scoring_settings', 'roster_positions'})
    flat_data.update(schema.settings.model_dump())
    flat_data.update(schema.scoring_settings.model_dump())
    flat_data['roster_positions'] = schema.roster_positions
    return flat_data

def roster_to_db(schema: schemas.SleeperRoster) -> dict:
    flat_data = schema.model_dump(exclude={'settings'})
    flat_data.update(schema.settings.model_dump())
    return flat_data

def tx_to_db(schema: schemas.SleeperTransaction, league: schemas.SleeperLeague) -> tuple[dict, list[dict], list[dict], list[dict]]:
    transaction = {
        "transaction_id": schema.transaction_id,
        "type": schema.type,
        "time_ms": schema.status_updated,
        "league_id": league.league_id
    }

    movements = []
    for p_id, r_id in (schema.adds or {}).items():
        movements.append({
            "transaction_id": schema.transaction_id,
            "player_id": p_id,
            "roster_id": r_id,
            "action": "ADD"
        })
    for p_id, r_id in (schema.drops or {}).items():
        movements.append({
            "transaction_id": schema.transaction_id,
            "player_id": p_id,
            "roster_id": r_id,
            "action": "DROP"
        })

    waivers = []
    for waiver in schema.waiver_budget:
        waivers.append({
            "transaction_id": schema.transaction_id,
            "sender": waiver.sender,
            "receiver": waiver.receiver,
            "amount": waiver.amount,
        })

    picks = []
    for pick in schema.draft_picks:
        picks.append({
            "transaction_id": schema.transaction_id,
            "season": pick.season,
            "round": pick.round,
            "new_owner_id": pick.owner_id,
            "old_owner_id": pick.previous_owner_id
        })

    return transaction, movements, waivers, picks