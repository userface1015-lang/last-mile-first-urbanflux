"""
config.py - Central configuration loader for the Metro Feeder Zone Screening Tool.
Loads, validates, and provides typed access to config/params.yaml.
"""

from pathlib import Path
from typing import Any, Dict, List
import yaml


class ConfigError(Exception):
    """Raised when configuration is missing required keys or contains invalid types."""
    pass


def load_config(config_path: str | Path = "config/params.yaml") -> Dict[str, Any]:
    """
    Load and strictly validate the configuration YAML file.
    
    Returns:
        Dict[str, Any]: Verified configuration dictionary.
    """
    path = Path(config_path)
    if not path.is_file():
        raise FileNotFoundError(f"Configuration file not found at: {path.resolve()}")

    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    if not isinstance(cfg, dict):
        raise ConfigError(f"Expected YAML file at {path} to parse into a dictionary.")

    # Validate mandatory top-level sections
    required_sections = ["study", "grid", "speeds_kmh", "overhead_min", "thresholds", "safety_filter", "optimiser", "paths", "seed"]
    for section in required_sections:
        if section not in cfg:
            raise ConfigError(f"Missing required configuration section: '{section}'")

    # Validate study
    study = cfg["study"]
    if not isinstance(study.get("stations_pilot"), list):
        raise ConfigError("'study.stations_pilot' must be a list of station names.")
    if not isinstance(study.get("core_buffer_m"), (int, float)) or study["core_buffer_m"] <= 0:
        raise ConfigError("'study.core_buffer_m' must be a positive number.")
    if not isinstance(study.get("margin_m"), (int, float)) or study["margin_m"] < 0:
        raise ConfigError("'study.margin_m' must be a non-negative number.")
    if not str(study.get("metric_crs", "")).startswith("EPSG:"):
        raise ConfigError(f"Invalid metric CRS: {study.get('metric_crs')}. Expected 'EPSG:XXXXX'.")

    # Validate grid
    grid = cfg["grid"]
    if not isinstance(grid.get("h3_resolution"), int) or not (0 <= grid["h3_resolution"] <= 15):
        raise ConfigError("'grid.h3_resolution' must be an integer between 0 and 15.")

    # Validate speeds
    speeds = cfg["speeds_kmh"]
    for mode in ["walk", "ebike"]:
        if mode not in speeds or not isinstance(speeds[mode], (int, float)) or speeds[mode] <= 0:
            raise ConfigError(f"'speeds_kmh.{mode}' must be a positive number.")
    # eauto is optional but validated if present
    if "eauto" in speeds and (not isinstance(speeds["eauto"], (int, float)) or speeds["eauto"] <= 0):
        raise ConfigError("'speeds_kmh.eauto' must be a positive number.")

    # Validate overhead
    overhead = cfg["overhead_min"]
    if "ebike" not in overhead or not isinstance(overhead["ebike"], (int, float)) or overhead["ebike"] < 0:
        raise ConfigError("'overhead_min.ebike' must be a non-negative number.")
    if "eauto" in overhead and (not isinstance(overhead["eauto"], (int, float)) or overhead["eauto"] < 0):
        raise ConfigError("'overhead_min.eauto' must be a non-negative number.")

    # Validate thresholds
    thresholds = cfg["thresholds"]
    if "T_min" not in thresholds or not isinstance(thresholds["T_min"], (int, float)) or thresholds["T_min"] <= 0:
        raise ConfigError("'thresholds.T_min' must be a positive number.")
    if "walk_to_zone_max_min" not in thresholds or not isinstance(thresholds["walk_to_zone_max_min"], (int, float)):
        raise ConfigError("'thresholds.walk_to_zone_max_min' must be a number.")

    # Validate paths
    paths = cfg["paths"]
    for p in ["raw", "interim", "output"]:
        if p not in paths:
            raise ConfigError(f"Missing path configuration for '{p}'.")

    return cfg


def get_meters_per_minute(speed_kmh: float) -> float:
    """Convert speed from km/h to meters per minute."""
    return float(speed_kmh) * 1000.0 / 60.0


if __name__ == "__main__":
    cfg = load_config()
    print("Configuration loaded and validated successfully:")
    print(f"  Pilot stations ({len(cfg['study']['stations_pilot'])}): {cfg['study']['stations_pilot']}")
    print(f"  Speeds: Walk = {cfg['speeds_kmh']['walk']} km/h ({get_meters_per_minute(cfg['speeds_kmh']['walk']):.1f} m/min), E-bike = {cfg['speeds_kmh']['ebike']} km/h ({get_meters_per_minute(cfg['speeds_kmh']['ebike']):.1f} m/min)")
    print(f"  Metric CRS: {cfg['study']['metric_crs']}, H3 Res: {cfg['grid']['h3_resolution']}")
    print(f"  Threshold T: {cfg['thresholds']['T_min']} min, Overhead: {cfg['overhead_min']['ebike']} min")
