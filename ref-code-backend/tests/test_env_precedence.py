import os
import sys
import importlib.util
from pathlib import Path

import pytest

# Dynamically load config_loader from backend/config/config_loader.py
CONFIG_DIR = Path(__file__).resolve().parents[1] / "config"
CONFIG_LOADER_PATH = CONFIG_DIR / "config_loader.py"

spec = importlib.util.spec_from_file_location("config_loader", CONFIG_LOADER_PATH)
config_loader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_loader)  # type: ignore


@pytest.fixture(autouse=True)
def clear_env(monkeypatch):
    # Ensure tests start from a clean slate for relevant vars
    for key in [
        "ACCOUNT_ENV",
        "PROJECT_ID",
        "GOOGLE_CLOUD_LOCATION",
    ]:
        monkeypatch.delenv(key, raising=False)


def test_env_precedence_falls_back_to_account_defaults(monkeypatch):
    # Use TechTrend account defaults
    monkeypatch.setenv("ACCOUNT_ENV", "tt")

    cfg = config_loader.load_config("tt")

    # Mimic server precedence logic
    effective_project = os.getenv("PROJECT_ID") or cfg.PROJECT_ID
    effective_location = os.getenv("GOOGLE_CLOUD_LOCATION") or cfg.LOCATION

    assert effective_project == cfg.PROJECT_ID
    assert effective_location == cfg.LOCATION


def test_env_precedence_uses_env_over_account(monkeypatch):
    # Set env overrides different from account defaults
    monkeypatch.setenv("ACCOUNT_ENV", "tt")
    monkeypatch.setenv("PROJECT_ID", "override-project")
    monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", "us-central1")

    cfg = config_loader.load_config("tt")

    # Mimic server precedence logic
    effective_project = os.getenv("PROJECT_ID") or cfg.PROJECT_ID
    effective_location = os.getenv("GOOGLE_CLOUD_LOCATION") or cfg.LOCATION

    assert effective_project == "override-project"
    assert effective_location == "us-central1"
