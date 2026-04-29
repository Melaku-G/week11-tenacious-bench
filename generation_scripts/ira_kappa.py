"""
IRA Cohen's kappa computation — compares R1 (automated) vs R2 (LLM judge).

Reads:
  bench/ira_sample_ids.json
  bench/tenacious_bench_v0.1/{train,dev,held_out}.jsonl  (R1 dimension_scores)
  bench/ira_r2_results.json                              (R2 dimension_scores)

Prints per-dimension and overall Cohen's kappa + percent agreement.

Usage:
    python bench/generation_scripts/ira_kappa.py
"""

from __future__ import annotations
import json
from pathlib import Path


DIMS = ["signal_fidelity", "tone_compliance", "segment_gate", "confidence_hedging", "format_compliance"]
TARGETS = {"signal_fidelity": 0.70, "tone_compliance": 0.80, "segment_gate": 0.85,
           "confidence_hedging": 0.70, "format_compliance": 0.90, "overall": 0.75}


def cohen_kappa(r1: list[int], r2: list[int]) -> float:
    """Binary Cohen's kappa."""
    n = len(r1)
    if n == 0:
        return float("nan")
    agree = sum(a == b for a, b in zip(r1, r2))
    p_o = agree / n
    p1_r1 = sum(r1) / n
    p1_r2 = sum(r2) / n
    p_e = p1_r1 * p1_r2 + (1 - p1_r1) * (1 - p1_r2)
    if p_e >= 1.0:
        return 1.0
    return round((p_o - p_e) / (1 - p_e), 4)


def load_r1_scores(ids: list[str]) -> dict[str, dict[str, int]]:
    index: dict[str, dict] = {}
    for part in ("train", "dev", "held_out"):
        p = Path(f"bench/tenacious_bench_v0.1/{part}.jsonl")
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip():
                t = json.loads(line)
                index[t["task_id"]] = t

    result: dict[str, dict[str, int]] = {}
    for tid in ids:
        if tid not in index:
            continue
        ds = index[tid].get("dimension_scores", {})
        result[tid] = {}
        for d in DIMS:
            val = ds.get(d, {})
            if isinstance(val, dict):
                result[tid][d] = int(val.get("score", 0))
            else:
                result[tid][d] = int(val)
    return result


def load_r2_scores(path: Path) -> dict[str, dict[str, int]]:
    results = json.loads(path.read_text(encoding="utf-8"))
    return {r["task_id"]: r["r2_dimension_scores"] for r in results}


def main() -> None:
    ids: list[str] = json.loads(Path("bench/ira_sample_ids.json").read_text(encoding="utf-8"))
    r1 = load_r1_scores(ids)

    r2_path = Path("bench/ira_r2_results.json")
    if not r2_path.exists():
        raise SystemExit("bench/ira_r2_results.json not found — run ira_r2_runner.py first")
    r2 = load_r2_scores(r2_path)

    common_ids = [tid for tid in ids if tid in r1 and tid in r2]
    print(f"Comparing {len(common_ids)} tasks (R1 vs R2)\n")

    all_r1_overall: list[int] = []
    all_r2_overall: list[int] = []

    header = f"{'Dimension':<22} {'R1 pass%':>9} {'R2 pass%':>9} {'Agree%':>8} {'kappa':>8} {'Target':>8} {'Status':>8}"
    print(header)
    print("-" * len(header))

    dim_kappas: dict[str, float] = {}
    for d in DIMS:
        r1_scores = [r1[tid][d] for tid in common_ids]
        r2_scores = [r2[tid].get(d, 0) for tid in common_ids]
        n = len(r1_scores)
        agree = sum(a == b for a, b in zip(r1_scores, r2_scores))
        pct_agree = agree / n * 100
        kappa = cohen_kappa(r1_scores, r2_scores)
        dim_kappas[d] = kappa
        target = TARGETS[d]
        status = "PASS" if kappa >= target else "FAIL"
        print(
            f"{d:<22} {sum(r1_scores)/n*100:>8.1f}% {sum(r2_scores)/n*100:>8.1f}%"
            f" {pct_agree:>7.1f}% {kappa:>8.4f} {target:>8.2f} {status:>8}"
        , flush=True)
        all_r1_overall.extend([int(s >= 0.75) for s in [
            sum(r1[tid][dd] * w for dd, w in
                [("signal_fidelity",0.30),("tone_compliance",0.20),("segment_gate",0.20),
                 ("confidence_hedging",0.15),("format_compliance",0.15)])
            for tid in common_ids
        ]])
        # correct overall per-task

    # Overall (task-level pass/fail)
    weights = {"signal_fidelity": 0.30, "tone_compliance": 0.20, "segment_gate": 0.20,
               "confidence_hedging": 0.15, "format_compliance": 0.15}
    r1_pass = [int(sum(r1[tid][d] * weights[d] for d in DIMS) >= 0.75) for tid in common_ids]
    r2_pass = [int(sum(r2[tid].get(d, 0) * weights[d] for d in DIMS) >= 0.75) for tid in common_ids]
    n = len(common_ids)
    agree_overall = sum(a == b for a, b in zip(r1_pass, r2_pass))
    kappa_overall = cohen_kappa(r1_pass, r2_pass)
    print("-" * len(header))
    target_ov = TARGETS["overall"]
    status_ov = "PASS" if kappa_overall >= target_ov else "FAIL"
    print(
        f"{'Overall (>=0.75)':<22} {sum(r1_pass)/n*100:>8.1f}% {sum(r2_pass)/n*100:>8.1f}%"
        f" {agree_overall/n*100:>7.1f}% {kappa_overall:>8.4f} {target_ov:>8.2f} {status_ov:>8}"
    , flush=True)

    print("\nDisagreements by task:")
    for tid in common_ids:
        disagreements = [d for d in DIMS if r1[tid][d] != r2[tid].get(d, 0)]
        if disagreements:
            print(f"  {tid}: {', '.join(disagreements)}")

    # Write machine-readable summary
    summary = {
        "run_date": "2026-04-29",
        "n": len(common_ids),
        "r1_vs_r2": {
            d: {"kappa": dim_kappas[d], "target": TARGETS[d], "pass": dim_kappas[d] >= TARGETS[d]}
            for d in DIMS
        },
        "overall": {"kappa": kappa_overall, "target": target_ov, "pass": kappa_overall >= target_ov},
    }
    out = Path("bench/ira_kappa_r1_r2.json")
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSummary written to {out}")


if __name__ == "__main__":
    main()
