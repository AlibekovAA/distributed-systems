import pytest
from app.messaging import _parse_message


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        (b'{"user_id": 7}', {"user_id": 7}),
        (b"7", {"user_id": 7}),
        ('"7"', {"user_id": 7}),
    ],
)
def test_parse_message_accepts_current_and_legacy_formats(body: bytes | str, expected: dict[str, int]) -> None:
    assert _parse_message(body) == expected


def test_parse_message_rejects_unrelated_json_values() -> None:
    with pytest.raises(ValueError, match="JSON object or user ID"):
        _parse_message("[]")
