from pathlib import Path

import pytest

from app import config


@pytest.mark.parametrize(
    ("env_contents", "expected_status"),
    [
        (None, "key is not configured"),
        ("GEOAPIFY_API_KEY=\n", "key is not configured"),
        ("GEOAPIFY_API_KEY='   '\n", "key is not configured"),
        ("GEOAPIFY_API_KEY=test-key\n", "key is configured"),
    ],
)
def test_geoapify_key_status_handles_missing_and_blank_values(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    env_contents: str | None,
    expected_status: str,
) -> None:
    env_path = tmp_path / ".env"
    if env_contents is not None:
        env_path.write_text(env_contents, encoding="utf-8")

    monkeypatch.setattr(config, "ENV_FILE_PATH", env_path)
    monkeypatch.delenv("GEOAPIFY_API_KEY", raising=False)

    assert config.get_geoapify_api_key_status() == expected_status
