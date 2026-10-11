"""
test_config.py - Unit tests for Step S1 configuration loader.
"""

import pytest
from src.config import load_config, ConfigError


def test_load_config_valid():
    cfg = load_config("config/params.yaml")
    assert "study" in cfg
    assert cfg["grid"]["h3_resolution"] == 9
    assert cfg["speeds_kmh"]["walk"] == 4.5
    assert cfg["speeds_kmh"]["ebike"] == 13.5
    assert cfg["thresholds"]["T_min"] == 15
    assert cfg["study"]["metric_crs"] == "EPSG:32643"
    assert len(cfg["study"]["stations_pilot"]) == 10


def test_load_config_missing_file():
    with pytest.raises(FileNotFoundError):
        load_config("non_existent_file.yaml")
