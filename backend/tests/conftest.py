from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.database import initialize_database
from app.main import create_app


@pytest.fixture
def database_path(tmp_path: Path) -> Path:
    path = tmp_path / "expedia_lite_test.sqlite3"
    initialize_database(path)
    return path


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    application = create_app(tmp_path / "expedia_lite_api_test.sqlite3")
    with TestClient(application) as test_client:
        yield test_client
