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
            player_map
            status
            league_id
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

GET_DM_BY_MEMBERS_QUERY = """
    query get_dm_by_members($members: [String]) {
        get_dm_by_members(members: $members) {
            dm_id
            dm_type
            hidden_at
            last_author_avatar
            last_author_display_name
            last_author_real_name
            last_author_id
            last_message_id
            last_message_text
            last_message_text_map
            last_message_time
            last_pinned_message_id
            last_read_id
            member_can_invite
            recent_users
            title
        }
    }
"""

CREATE_DM_MUTATION = """
    mutation create_dm($dm_type: String, $members: [String]) {
        create_dm(dm_type: $dm_type, members: $members) {
            dm_id
            dm_type
            last_author_avatar
            last_author_display_name
            last_author_real_name
            last_author_id
            last_message_id
            last_message_text
            last_message_text_map
            last_message_time
            last_pinned_message_id
            last_read_id
            member_can_invite
            hidden_at
            recent_users
            title
        }
    }
"""

CREATE_MESSAGE_MUTATION = """
    mutation create_message(
        $parent_id: String,
        $client_id: String,
        $parent_type: String,
        $text: String,
        $attachment_type: String,
        $k_attachment_data: [String],
        $v_attachment_data: [String]
    ) {
        create_message(
            parent_id: $parent_id,
            client_id: $client_id,
            parent_type: $parent_type,
            text: $text,
            shard_min: null,
            shard_max: null,
            attachment_type: $attachment_type,
            k_attachment_data: $k_attachment_data,
            v_attachment_data: $v_attachment_data
        ) {
            attachment
            author_avatar
            author_display_name
            author_real_name
            author_id
            author_is_bot
            author_role_id
            client_id
            created
            message_id
            parent_id
            parent_type
            pinned
            reactions
            user_reactions
            text
            text_map
        }
    }
"""

MUTATIONS: dict[str, str] = {
    "create_verification_code": CREATE_VERIFICATION_CODE_MUTATION,
    "login": LOGIN_QUERY,
    "propose_trade": PROPOSE_TRADE_MUTATION,
    "submit_waiver_claim": SUBMIT_WAIVER_CLAIM_MUTATION,
    "get_dm_by_members": GET_DM_BY_MEMBERS_QUERY,
    "create_dm": CREATE_DM_MUTATION,
    "create_message": CREATE_MESSAGE_MUTATION,
}