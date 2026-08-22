from __future__ import annotations

from app.schemas.base import Base


class AdvisorPlayerRef(Base):
    player_id: str
    name: str
    position: str | None = None
    team: str | None = None
    age: float | None = None
    ktc_value: float | None = None
    personal_war: float | None = None
    market_war: float | None = None
    delta_war: float | None = None


class AdvisorProposal(Base):
    league_id: str
    league_name: str
    counterparty_id: str
    counterparty_name: str
    send: list[AdvisorPlayerRef]
    receive: list[AdvisorPlayerRef]
    market_send_total: float | None = None
    market_receive_total: float | None = None
    personal_send_total: float | None = None
    personal_receive_total: float | None = None

    @property
    def asymmetry(self) -> str | None:
        if (
            self.market_receive_total is None
            or self.market_send_total is None
            or self.market_send_total == 0
        ):
            return None

        ratio = self.market_receive_total / self.market_send_total

        if self.personal_gain() > 0 and ratio >= 0.9:
            return "win_win"

        if self.personal_gain() > 0 and ratio < 0.9:
            return "value_trap"

        if self.personal_gain() <= 0 and ratio >= 1.1:
            return "market_favor"

        return "unfavorable"

    def personal_gain(self) -> float | None:
        if (
            self.personal_receive_total is None
            or self.personal_send_total is None
        ):
            return None

        return self.personal_receive_total - self.personal_send_total


class AdvisorRosterContext(Base):
    league_id: str
    league_name: str
    season: int
    total_rosters: int
    wins: int | None = None
    losses: int | None = None
    ties: int | None = None
    points_for: float | None = None
    position_counts: dict[str, int] = {}
    avg_age: float | None = None


class AdvisorSignalSummary(Base):
    buy_targets: list[str] = []
    sell_candidates: list[str] = []


class AdvisorDossier(Base):
    username: str
    proposals: list[AdvisorProposal]
    roster_contexts: list[AdvisorRosterContext]
    signals: AdvisorSignalSummary
    scope_league_id: str | None = None


class AdvisorRecommendation(Base):
    headline: str
    reasoning: str
    confidence: str
    proposal: AdvisorProposal | None = None


class AdvisorSynthesisResponse(Base):
    summary: str
    recommendations: list[AdvisorRecommendation]
    roster_advice: list[AdvisorRecommendation] = []
    generated_at: str
    model: str
    cached: bool = False


ALLOWED_FEEDBACK_SENTIMENTS = {"like", "dislike"}

ALLOWED_FEEDBACK_TAGS = {
    "avoid_injured",
    "roster_limit_concern",
    "calculator_not_bible",
    "prefer_picks",
    "avoid_player",
    "position_need",
    "age_window",
}

ACTION_VALUES_DOWNGRADE = "values_downgrade_requested"
ACTION_GITHUB_ISSUE = "github_issue_drafted"


class AdvisorFeedbackRequest(Base):
    sentiment: str
    reason: str | None = None
    tags: list[str] = []
    league_id: str | None = None
    counterparty_id: str | None = None
    player_ids: list[str] = []
    proposal_snapshot: dict = {}
    action_taken: str | None = None


class AdvisorFeedbackResponse(Base):
    id: int
    sentiment: str
    reason: str | None = None
    tags: list[str] = []
    resolved: bool
    created_at: str


class AdvisorPreferenceSummary(Base):
    likes: list[str] = []
    dislikes: list[str] = []
    tags: dict[str, int] = {}
    notes: list[str] = []
