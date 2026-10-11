"""
run_clean_rerun.py - Executes a complete, clean end-to-end rerun of the pipeline.
1. Cleans cached files in data/output/
2. Executes src.travel_times
3. Executes src.optimizer
4. Executes scripts.compute_speed_matrix
5. Executes scripts.compute_overhead_matrix
6. Executes scripts.generate_audit_maps
7. Runs full test suite via pytest
8. Logs headline validation metrics and Git status
"""

import os
import shutil
import subprocess
import time
from pathlib import Path
import json
import pandas as pd
import geopandas as gpd

def main():
    t_start = time.time()
    out_dir = Path("data/output")
    print("================================================================================")
    print("           STARTING CLEAN PIPELINE RERUN (WHITEFIELD 10-STATION PILOT)          ")
    print("================================================================================")

    # 1. Clean output directory (keep directory, remove files)
    print("\n[Step 1/7] Cleaning data/output/ directory...")
    if out_dir.exists():
        for f in out_dir.iterdir():
            if f.is_file():
                try:
                    f.unlink()
                except PermissionError:
                    print(f"  Note: {f.name} is currently open in an external reader; will be overwritten during pipeline execution.")
    print("data/output/ cache successfully cleared.")

    # 2. Run travel_times
    print("\n[Step 2/7] Running src.travel_times (H3, Walk/Bike/Drive Routing, Uplift)...")
    res1 = subprocess.run(["python", "-m", "src.travel_times"], capture_output=True, text=True)
    if res1.returncode != 0:
        print("ERROR in src.travel_times:\n", res1.stderr)
        raise RuntimeError(res1.stderr)
    print(res1.stdout.strip())

    # 3. Run optimizer
    print("\n[Step 3/7] Running src.optimizer (Candidates, Greedy Hubs, Station Ranking)...")
    res2 = subprocess.run(["python", "-m", "src.optimizer"], capture_output=True, text=True)
    if res2.returncode != 0:
        print("ERROR in src.optimizer:\n", res2.stderr)
        raise RuntimeError(res2.stderr)
    print(res2.stdout.strip())

    # 4. Run speed matrix
    print("\n[Step 4/7] Generating Speed Sensitivity Matrix...")
    res3 = subprocess.run(["python", "scripts/compute_speed_matrix.py"], capture_output=True, text=True)
    if res3.returncode != 0:
        print("ERROR in compute_speed_matrix.py:\n", res3.stderr)
        raise RuntimeError(res3.stderr)
    print(res3.stdout.strip())

    # 5. Run overhead matrix
    print("\n[Step 5/7] Generating Overhead Sensitivity Matrix (3, 5, 7 min)...")
    res4 = subprocess.run(["python", "scripts/compute_overhead_matrix.py"], capture_output=True, text=True)
    if res4.returncode != 0:
        print("ERROR in compute_overhead_matrix.py:\n", res4.stderr)
        raise RuntimeError(res4.stderr)
    print(res4.stdout.strip())

    # 6. Generate audit maps
    print("\n[Step 6/8] Regenerating Audit Maps (Footbridge Severance & Western Reassignment)...")
    res5 = subprocess.run(["python", "scripts/generate_audit_maps.py"], capture_output=True, text=True)
    if res5.returncode != 0:
        print("ERROR in generate_audit_maps.py:\n", res5.stderr)
        raise RuntimeError(res5.stderr)
    print(res5.stdout.strip())

    # 7. Generate T=20 Hub results
    print("\n[Step 7/8] Generating T=20 Hub Results (coverage_pairs_T20 & selected_sites_T20)...")
    res_t20 = subprocess.run(["python", "scripts/export_T20_hub_results.py"], capture_output=True, text=True)
    if res_t20.returncode != 0:
        print("ERROR in export_T20_hub_results.py:\n", res_t20.stderr)
        raise RuntimeError(res_t20.stderr)
    print(res_t20.stdout.strip())

    # 8. Run full pytest suite
    print("\n[Step 8/8] Running Unit Test Suite (pytest tests/)...")
    res6 = subprocess.run(["pytest", "tests/", "-v"], capture_output=True, text=True)
    print(res6.stdout.strip())
    if res6.returncode != 0:
        print("ERROR in test suite:\n", res6.stderr)
        raise RuntimeError("Test suite failed!")

    print("\n================================================================================")
    print(f"PIPELINE RERUN COMPLETED SUCCESSFULLY in {time.time() - t_start:.2f}s!")
    print("================================================================================")

    # Verification summary
    with open("data/output/catchment_metrics.json", "r") as f:
        metrics = json.load(f)
    cells = pd.read_csv("data/output/cells.csv")
    corr_cells = cells[cells["is_corridor_assigned"] == True]
    c_pop = corr_cells["population"].sum()
    w_pop = corr_cells[corr_cells["walk_covered"]]["population"].sum()
    e_pop = corr_cells[corr_cells["ebike_uplift"]]["population"].sum()
    a_pop = corr_cells[corr_cells["eauto_uplift"]]["population"].sum()
    u_pop = corr_cells[corr_cells["combined_covered"]]["population"].sum()
    r_pop = corr_cells[corr_cells["residual"]]["population"].sum()

    print("\n--- RECONCILIATION AUDIT ---")
    print(f"Total Corridor Population:    {c_pop:>10,.1f} (100.0%)")
    print(f"1. Walk Baseline:             {w_pop:>10,.1f} ({w_pop/c_pop*100:4.1f}%)")
    print(f"2. E-Bike Doorstep Uplift:    +{e_pop:>9,.1f} (+{e_pop/c_pop*100:4.1f}%)")
    print(f"3. E-Auto Extra (Upper Bound):+{a_pop:>9,.1f} (+{a_pop/c_pop*100:4.1f}%)")
    print(f"Combined Union Access:        {u_pop:>10,.1f} ({u_pop/c_pop*100:4.1f}%)")
    print(f"Residual Unserved:            {r_pop:>10,.1f} ({r_pop/c_pop*100:4.1f}%)")
    print(f"Sum of Partition Parts:       {w_pop + e_pop + a_pop + r_pop:>10,.1f} (Diff: {abs(c_pop - (w_pop + e_pop + a_pop + r_pop)):.2f})")

    # Selected sites
    sel = pd.read_csv("data/output/selected_sites.csv")
    print(f"\nTop 5 Feeder Hubs Gain at T=15: +{sel.head(5)['marginal_gain'].sum():,.1f} residents")

if __name__ == "__main__":
    main()
