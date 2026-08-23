import pytest
from fastapi import HTTPException

from app.schemas.advisor import (
    ACTION_VALUES_DOWNGRADE,
    AdvisorFeedbackRequest,
    AdvisorPreferenceSummary,
)
from app.services.advisor.feedback import (
    build_preference_summary,
    validate_feedback_request,
)


def _request(**overrides) -> AdvisorFeedbackRequest:
    payload = {
        "sentiment": "dislike",
        "reason": "I would exceed roster limits",
        "tags": ["roster_limit_concern"],
    }
    payload.update(overrides)
    return AdvisorFeedbackRequest(**payload)


def test_validate_accepts_valid_request():
    validate_feedback_request(_request())


def test_validate_rejects_bad_sentiment():
    with pytest.raises(HTTPException) as exc:
        validate_feedback_request(
            _request(sentiment="meh"),
        )

    assert exc.value.status_code == 422


def test_validate_rejects_unknown_tags():
    with pytest.raises(HTTPException) as exc:
        validate_feedback_request(
            _request(tags=["make_me_a_sandwich"]),
        )

    assert exc.value.status_code == 422
    assert "Unknown feedback tags" in exc.value.detail


def test_validate_rejects_long_reason():
    with pytest.raises(HTTPException):
        validate_feedback_request(
            _request(reason="x" * 1500),
        )


class _Row:
    def __init__(
        self,
        sentiment,
        reason=None,
        tags=None,
        action_taken=None,
    ):
        self.sentiment = sentiment
        self.reason = reason
        self.tags = tags or []
        self.action_taken = action_taken


def test_preference_summary_buckets_by_sentiment():
    rows = [
        _Row("like", "Love buying rookie WRs"),
        _Row("dislike", "No injured players", ["avoid_injured"]),
        _Row(
            "dislike",
            None,
            ["calculator_not_bible"],
            action_taken=ACTION_VALUES_DOWNGRADE,
        ),
    ]

    summary = build_preference_summary(rows)

    assert summary.likes == ["Love buying rookie WRs"]
    assert summary.dislikes == [
        "No injured players; tags: avoid_injured"
    ]
    assert summary.tags == {"avoid_injured": 1}


def test_preference_summary_empty():
    summary = AdvisorPreferenceSummary()

    assert summary.likes == []
    assert summary.dislikes == []
