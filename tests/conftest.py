from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MODULES_TO_CLEAR = [
    "app",
    "bootstrap",
    "db",
    "deps",
    "models",
    "roleplay_api",
    "roleplay_engine",
    "roleplay_referee",
    "schemas",
    "security",
    "services",
    "settings",
    "tracking",
    "routers.admin",
    "routers.admin_monitor",
    "routers.auth",
    "routers.me",
    "routers.tracking",
]


@pytest.fixture(scope="session")
def app_module(tmp_path_factory):
    db_dir = tmp_path_factory.mktemp("backend-tests")
    db_path = db_dir / "test.db"

    os.environ["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"
    os.environ["JWT_SECRET"] = "test-secret"
    os.environ["OPENAI_API_KEY"] = "test-openai-key"
    os.environ["QDRANT_URL"] = "http://127.0.0.1:9"
    os.environ["QDRANT_COLLECTION"] = "bizeng"
    os.environ["AZURE_OPENAI_KEY"] = ""
    os.environ["AZURE_OPENAI_ENDPOINT"] = ""
    os.environ["AZURE_OPENAI_EMBEDDING_KEY"] = ""
    os.environ["AZURE_OPENAI_EMBEDDING_ENDPOINT"] = ""
    os.environ["AZURE_SPEECH_KEY"] = ""
    os.environ["AZURE_SPEECH_REGION"] = "eastasia"

    for module_name in MODULES_TO_CLEAR:
        sys.modules.pop(module_name, None)

    return importlib.import_module("app")


@pytest.fixture(scope="session")
def client(app_module):
    with TestClient(app_module.app) as test_client:
        yield test_client
