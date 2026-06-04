MUTATIONS = {
    "propose_trade": """
        mutation propose_trade(
            $league_id: String!,
            $k_adds: [String],
            $v_adds: [Int],
            $k_drops: [String],
            $v_drops: [Int],
            $draft_picks: [String],
            $waiver_budget: [Int],
            $expires_at: Int
        ) {
            propose_trade(
                league_id: $league_id,
                k_adds: $k_adds,
                v_adds: $v_adds,
                k_drops: $k_drops,
                v_drops: $v_drops,
                draft_picks: $draft_picks,
                waiver_budget: $waiver_budget,
                expires_at: $expires_at
            ) {
                transaction_id
            }
        }
    """,

    "submit_waiver_claim": """
        mutation submit_waiver_claim(
            $league_id: String!,
            $k_adds: [String],
            $v_adds: [Int],
            $k_drops: [String],
            $v_drops: [Int],
            $k_settings: [String],
            $v_settings: [Int]
        ) {
            submit_waiver_claim(
                league_id: $league_id,
                k_adds: $k_adds,
                v_adds: $v_adds,
                k_drops: $k_drops,
                v_drops: $v_drops,
                k_settings: $k_settings,
                v_settings: $v_settings
            ) {
                transaction_id
            }
        }
    """
}