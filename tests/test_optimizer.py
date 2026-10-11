"""
test_optimizer.py - Unit tests for candidate sites, greedy optimizer, and station ranking.
"""

from pathlib import Path
import pandas as pd
import geopandas as gpd


def test_optimizer_outputs_exist():
    out_dir = Path("data/output")
    assert (out_dir / "candidate_sites.csv").exists()
    assert (out_dir / "candidate_sites.gpkg").exists()
    assert (out_dir / "coverage_pairs.csv").exists()
    assert (out_dir / "selected_sites.csv").exists()
    assert (out_dir / "selected_sites.gpkg").exists()
    assert (out_dir / "station_ranking.csv").exists()
    assert (out_dir / "sensitivity.csv").exists()


def test_greedy_optimizer_monotonicity():
    df = pd.read_csv("data/output/selected_sites.csv")
    assert len(df) > 0
    
    # Check that marginal gain is non-increasing (diminishing returns)
    gains = df["marginal_gain"].tolist()
    for i in range(len(gains) - 1):
        assert gains[i] >= gains[i+1], f"Marginal gain increased at step {i+1}: {gains[i]} -> {gains[i+1]}"
        
    # Check that cumulative coverage is non-decreasing
    cum = df["cumulative_feeder_pop"].tolist()
    for i in range(len(cum) - 1):
        assert cum[i] <= cum[i+1]


def test_station_ranking_consistency():
    df = pd.read_csv("data/output/station_ranking.csv")
    assert len(df) == 10
    
    # Check ranks are 1 to 10 sorted by score
    assert list(df["rank"]) == list(range(1, 11))
    scores = df["priority_score"].tolist()
    for i in range(len(scores) - 1):
        assert scores[i] >= scores[i+1]


def test_context_stations_excluded_from_ranking():
    """Verify that western boundary context stations are strictly excluded from ranking."""
    df = pd.read_csv("data/output/station_ranking.csv")
    assert len(df) == 10
    # Context station IDs or names must not appear
    for sid in df["station_id"]:
        assert not sid.startswith("CTX_"), f"Context station found in ranking: {sid}"
    for name in df["name"]:
        assert name not in ["Singayyanapalya", "Krishnarajapura"]
        
    # Total uncovered need across the 10 stations must sum to corridor unserved need
    total_need = df["walk_uncovered_need"].sum()
    cells = pd.read_csv("data/output/cells.csv")
    c_unserved = cells[(cells["is_corridor_assigned"] == True) & (cells["walk_covered"] == False)]["population"].sum()
    assert round(total_need, 1) == round(c_unserved, 1)


def test_coverage_pairs_corridor_isolation():
    """Verify that coverage pairs only target cells within the core corridor."""
    pairs = pd.read_csv("data/output/coverage_pairs.csv")
    cells = pd.read_csv("data/output/cells.csv")
    merged = pairs.merge(cells[["cell_id", "is_corridor_assigned"]], on="cell_id")
    assert merged["is_corridor_assigned"].all(), "Found coverage pairs targeting context absorber cells"
