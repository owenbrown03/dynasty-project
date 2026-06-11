CREATE_VERIFICATION_CODE_MUTATION = """
    mutation create_verification_code(
        $email_or_phone: String!,
        $captcha: String
    ) {
        create_verification_code(
            email_or_phone: $email_or_phone,
            captcha: $captcha
        )
    }
"""

LOGIN_QUERY = """
    query login(
        $email_or_phone_or_username: String!,
        $password: String!,
        $captcha: String
    ) {
        login(
            email_or_phone_or_username: $email_or_phone_or_username,
            password: $password,
            captcha: $captcha
        ) {
            token
        }
    }
"""

PROPOSE_TRADE_MUTATION = """
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
"""

SUBMIT_WAIVER_CLAIM_MUTATION = """
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

MUTATIONS: dict[str, str] = {
    "create_verification_code": CREATE_VERIFICATION_CODE_MUTATION,
    "login": LOGIN_QUERY,
    "propose_trade": PROPOSE_TRADE_MUTATION,
    "submit_waiver_claim": SUBMIT_WAIVER_CLAIM_MUTATION,
}