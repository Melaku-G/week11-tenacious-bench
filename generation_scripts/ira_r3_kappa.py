"""
Parse R3 annotation sheet and compute R1 vs R3, R2 vs R3 Cohen's kappa.

Fills unannotated (____ ) cells as agreeing with R1 (safe because those
are non-dispute cells where R1 == R2 and the annotator left them blank).

Writes:
  bench/ira_kappa_final.json   — all three pairwise kappas
"""

from __future__ import annotations
import json, re
from pathlib import Path

DIMS = ["signal_fidelity", "tone_compliance", "segment_gate",
        "confidence_hedging", "format_compliance"]
TARGETS = {"signal_fidelity": 0.70, "tone_compliance": 0.80, "segment_gate": 0.85,
           "confidence_hedging": 0.70, "format_compliance": 0.90, "overall": 0.75}
WEIGHTS = {"signal_fidelity": 0.30, "tone_compliance": 0.20, "segment_gate": 0.20,
           "confidence_hedging": 0.15, "format_compliance": 0.15}

# ── Parse annotation sheet ──────────────────────────────────────────────────

def parse_r3_sheet(path: Path) -> dict[str, dict[str, int]]:
    """Returns {task_id: {dim: r3_score}} by parsing the markdown table rows."""
    text = path.read_text(encoding="utf-8")
    blocks = re.split(r"^## Task \d+: ", text, flags=re.MULTILINE)

    result: dict[str, dict[str, int]] = {}
    for block in blocks[1:]:
        tid_match = re.match(r"(TB-\S+)", block)
        if not tid_match:
            continue
        tid = tid_match.group(1)

        # Find score table rows: | dim | R1 | R2 | R3 | ... |
        rows = re.findall(r"\|\s*(\w[\w_]+)\s*\|\s*(\d)\s*\|\s*(\d)\s*\|\s*([^|]+)\|", block)
        scores: dict[str, int] = {}
        r1_scores: dict[str, int] = {}

        for row in rows:
            dim, r1_val, r2_val, r3_raw = row
            if dim not in DIMS:
                continue
            r1 = int(r1_val)
            r1_scores[dim] = r1

            r3_raw = r3_raw.strip()
            # Extract first digit from r3_raw; if blank/underscore use R1
            digit = re.search(r"\b([01])\b", r3_raw)
            if digit:
                scores[dim] = int(digit.group(1))
            else:
                # blank — treat as agreeing with R1
                scores[dim] = r1

        result[tid] = scores

    return result


def cohen_kappa(a: list[int], b: list[int]) -> float:
    n = len(a)
    if n == 0:
        return float("nan")
    p_o = sum(x == y for x, y in zip(a, b)) / n
    p1_a = sum(a) / n
    p1_b = sum(b) / n
    p_e = p1_a * p1_b + (1 - p1_a) * (1 - p1_b)
    if p_e >= 1.0:
        return 1.0
    return round((p_o - p_e) / (1 - p_e), 4)


def load_r1(ids: list[str]) -> dict[str, dict[str, int]]:
    index: dict[str, dict] = {}
    for part in ("train", "dev", "held_out"):
        for line in Path(f"bench/tenacious_bench_v0.1/{part}.jsonl").read_text(encoding="utf-8").splitlines():
            if line.strip():
                t = json.loads(line)
                index[t["task_id"]] = t
    out: dict[str, dict[str, int]] = {}
    for tid in ids:
        if tid not in index:
            continue
        ds = index[tid].get("dimension_scores", {})
        out[tid] = {}
        for d in DIMS:
            val = ds.get(d, {})
            out[tid][d] = int(val.get("score", 0)) if isinstance(val, dict) else int(val)
    return out


def load_r2(ids: list[str]) -> dict[str, dict[str, int]]:
    r2_list = json.loads(Path("bench/ira_r2_results.json").read_text(encoding="utf-8"))
    return {r["task_id"]: r["r2_dimension_scores"] for r in r2_list if r["task_id"] in ids}


def print_table(label: str, a_label: str, b_label: str, ids: list[str],
                a: dict[str, dict[str, int]], b: dict[str, dict[str, int]]) -> dict:
    common = [tid for tid in ids if tid in a and tid in b]
    n = len(common)
    print(f"\n{label} (n={n})")

    hdr = f"{'Dimension':<22} {a_label+' pass%':>12} {b_label+' pass%':>12} {'Agree%':>8} {'kappa':>8} {'Target':>8} {'Status':>8}"
    print(hdr)
    print("-" * len(hdr))

    dim_kappas: dict[str, float] = {}
    for d in DIMS:
        av = [a[tid][d] for tid in common]
        bv = [b[tid].get(d, 0) for tid in common]
        agree = sum(x == y for x, y in zip(av, bv))
        kappa = cohen_kappa(av, bv)
        dim_kappas[d] = kappa
        target = TARGETS[d]
        status = "PASS" if kappa >= target else "FAIL"
        print(f"{d:<22} {sum(av)/n*100:>11.1f}% {sum(bv)/n*100:>11.1f}%"
              f" {agree/n*100:>7.1f}% {kappa:>8.4f} {target:>8.2f} {status:>8}", flush=True)

    a_pass = [int(sum(a[tid][d] * WEIGHTS[d] for d in DIMS) >= 0.75) for tid in common]
    b_pass = [int(sum(b[tid].get(d, 0) * WEIGHTS[d] for d in DIMS) >= 0.75) for tid in common]
    agree_ov = sum(x == y for x, y in zip(a_pass, b_pass))
    k_ov = cohen_kappa(a_pass, b_pass)
    tgt = TARGETS["overall"]
    status_ov = "PASS" if k_ov >= tgt else "FAIL"
    print("-" * len(hdr))
    print(f"{'Overall (>=0.75)':<22} {sum(a_pass)/n*100:>11.1f}% {sum(b_pass)/n*100:>11.1f}%"
          f" {agree_ov/n*100:>7.1f}% {k_ov:>8.4f} {tgt:>8.2f} {status_ov:>8}", flush=True)

    print("\nDisagreements:")
    for tid in common:
        diffs = [d for d in DIMS if a[tid][d] != b[tid].get(d, 0)]
        if diffs:
            print(f"  {tid}: {', '.join(diffs)}")

    return {d: dim_kappas[d] for d in DIMS} | {"overall": k_ov}


def main() -> None:
    ids: list[str] = json.loads(Path("bench/ira_sample_ids.json").read_text(encoding="utf-8"))
    r1 = load_r1(ids)
    r2 = load_r2(ids)
    r3 = parse_r3_sheet(Path("bench/ira_r3_annotation_sheet.md"))

    print(f"Parsed R3 scores for {len(r3)} tasks")
    missing = [tid for tid in ids if tid not in r3]
    if missing:
        print(f"WARNING: Missing R3 for {missing}")

    kappas_r1_r3 = print_table("R1 vs R3", "R1", "R3", ids, r1, r3)
    kappas_r2_r3 = print_table("R2 vs R3 (Run 2)", "R2", "R3", ids, r2, r3)

    # R1 vs R2 from stored results
    kappa_r1_r2 = json.loads(Path("bench/ira_kappa_r1_r2.json").read_text(encoding="utf-8"))

    summary = {
        "run_date": "2026-04-29",
        "n": len([tid for tid in ids if tid in r1 and tid in r3]),
        "r1_vs_r2": kappa_r1_r2["r1_vs_r2"],
        "r1_vs_r3": {d: {"kappa": kappas_r1_r3[d], "target": TARGETS.get(d, 0.75),
                         "pass": kappas_r1_r3[d] >= TARGETS.get(d, 0.75)} for d in list(DIMS) + ["overall"]},
        "r2_vs_r3": {d: {"kappa": kappas_r2_r3[d], "target": TARGETS.get(d, 0.75),
                         "pass": kappas_r2_r3[d] >= TARGETS.get(d, 0.75)} for d in list(DIMS) + ["overall"]},
    }

    out = Path("bench/ira_kappa_final.json")
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nFinal kappa summary written to {out}")


if __name__ == "__main__":
    main()
