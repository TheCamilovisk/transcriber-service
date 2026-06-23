from datetime import timezone

from app.utils.time import utc_now


def test_utc_now_is_timezone_aware() -> None:
    now = utc_now()
    assert now.tzinfo is not None
    assert now.tzinfo == timezone.utc


def test_utc_now_returns_utc() -> None:
    now = utc_now()
    assert now.utcoffset() == timezone.utc.utcoffset(now)
