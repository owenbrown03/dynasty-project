from app.schemas.waivers import WaiverClaimRequest


def build_waiver_claim_variables(
    claim: WaiverClaimRequest,
) -> dict:
    has_drop = claim.drop_player_id is not None

    return {
        "k_adds": [
            claim.add_player_id,
        ],
        "v_adds": [
            claim.roster_id,
        ],
        "k_drops": (
            [claim.drop_player_id]
            if has_drop
            else []
        ),
        "v_drops": (
            [claim.roster_id]
            if has_drop
            else []
        ),
        "k_settings": [
            "waiver_bid",
        ],
        "v_settings": [
            claim.bid,
        ],
    }