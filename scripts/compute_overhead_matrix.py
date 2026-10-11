"""
compute_overhead_matrix.py - Parametric sensitivity across vehicle access/unlock overhead
Varies overhead at 3.0, 5.0 (baseline), and 7.0 minutes for both T=15 and T=20 min,
capturing the walk baseline, e-bike uplift, combined walk+bike reach, e-auto upper bound,
and union coverage for the core 10-station corridor (453,687 residents).
"""

from pathlib import Path
import geopandas as gpd
import pandas as pd
import numpy as np

def run_overhead_sensitivity():
    cells = gpd.read_file("data/output/cells.gpkg")
    corr_cells = cells[cells["is_corridor_assigned"] == True].copy()
    c_pop = float(corr_cells["population"].sum())

    overheads = [3.0, 5.0, 7.0]
    thresholds = [15.0, 20.0]
    records = []

    print("==================================================================================================")
    print("OVERHEAD SENSITIVITY GRID: ACCESS/UNLOCK OVERHEAD (3, 5, 7 MIN) x TIME THRESHOLD (15, 20 MIN)")
    print(f"Core Corridor Territory: {c_pop:,.0f} residents")
    print("==================================================================================================")

    for ov in overheads:
        # Scale vehicle times by replacing 5.0 min default overhead with ov
        e_time_ov = np.maximum(0.0, corr_cells["ebike_time_min"] - 5.0) + ov
        a_time_ov = np.maximum(0.0, corr_cells["eauto_time_min"] - 5.0) + ov
        w_time = corr_cells["walk_time_min"]

        for t in thresholds:
            w_cov = w_time <= t
            e_cov = e_time_ov <= t
            a_cov = a_time_ov <= t

            e_up = e_cov & (~w_cov)
            wb_comb = w_cov | e_cov
            a_up = a_cov & (~w_cov) & (~e_cov)
            comb = w_cov | e_cov | a_cov
            res = ~comb

            w_pop = round(float(corr_cells[w_cov]["population"].sum()), 1)
            e_up_pop = round(float(corr_cells[e_up]["population"].sum()), 1)
            wb_pop = round(float(corr_cells[wb_comb]["population"].sum()), 1)
            a_up_pop = round(float(corr_cells[a_up]["population"].sum()), 1)
            comb_pop = round(float(corr_cells[comb]["population"].sum()), 1)
            res_pop = round(float(corr_cells[res]["population"].sum()), 1)

            rec = {
                "overhead_min": ov,
                "threshold_T_min": t,
                "corridor_population": round(c_pop, 0),
                "walk_baseline_pop": w_pop,
                "walk_baseline_pct": round(w_pop / c_pop * 100, 1),
                "ebike_uplift_pop": e_up_pop,
                "ebike_uplift_pct": round(e_up_pop / c_pop * 100, 1),
                "walk_ebike_reach_pop": wb_pop,
                "walk_ebike_reach_pct": round(wb_pop / c_pop * 100, 1),
                "eauto_extra_pop": a_up_pop,
                "eauto_extra_pct": round(a_up_pop / c_pop * 100, 1),
                "combined_union_pop": comb_pop,
                "combined_union_pct": round(comb_pop / c_pop * 100, 1),
                "residual_unserved_pop": res_pop,
                "residual_unserved_pct": round(res_pop / c_pop * 100, 1),
            }
            records.append(rec)

            print(f"Overhead={ov:.0f}m | T={t:.0f}m: Walk={w_pop:6,.0f} ({rec['walk_baseline_pct']:4.1f}%) | "
                  f"E-Bike Up=+{e_up_pop:6,.0f} (+{rec['ebike_uplift_pct']:4.1f}%) | "
                  f"Walk+Bike={wb_pop:6,.0f} ({rec['walk_ebike_reach_pct']:4.1f}%) | "
                  f"E-Auto Up=+{a_up_pop:6,.0f} (+{rec['eauto_extra_pct']:4.1f}%) | "
                  f"Union={comb_pop:6,.0f} ({rec['combined_union_pct']:4.1f}%)")

    out_df = pd.DataFrame(records)
    out_path = Path("data/output/overhead_sensitivity_matrix.csv")
    out_df.to_csv(out_path, index=False)
    print(f"\nOverhead sensitivity matrix saved to {out_path}!")
    return out_df

if __name__ == "__main__":
    run_overhead_sensitivity()
