"""
Generate bench/ablations/statistical_test.json — paired bootstrap significance tests
for the three ablation deltas (ΔA, ΔB, ΔC).

Run: python bench/ablations/generate_statistical_test.py
"""

from __future__ import annotations
import json
import random
from pathlib import Path
from math import sqrt


# ── Bootstrap ──────────────────────────────────────────────────────────────

def paired_bootstrap(a_scores: list[float], b_scores: list[float],
                     n_boot: int = 10_000, seed: int = 42) -> dict:
    """
    Paired bootstrap test: H0 = mean(B) - mean(A) <= 0.
    Returns observed delta, 95% CI, one-sided p-value.
    """
    assert len(a_scores) == len(b_scores)
    n = len(a_scores)
    rng = random.Random(seed)

    obs_delta = sum(b_scores) / n - sum(a_scores) / n

    boot_deltas = []
    for _ in range(n_boot):
        idx = [rng.randint(0, n - 1) for _ in range(n)]
        ba = sum(a_scores[i] for i in idx) / n
        bb = sum(b_scores[i] for i in idx) / n
        boot_deltas.append(bb - ba)

    boot_deltas.sort()
    ci_lo = boot_deltas[int(0.025 * n_boot)]
    ci_hi = boot_deltas[int(0.975 * n_boot)]
    # one-sided p-value: P(delta <= 0 | data)
    p_value = sum(1 for d in boot_deltas if d <= 0) / n_boot

    return {
        "observed_delta": round(obs_delta, 6),
        "ci_95_lo": round(ci_lo, 6),
        "ci_95_hi": round(ci_hi, 6),
        "p_value_one_sided": round(p_value, 6),
        "significant_at_0.05": p_value < 0.05,
        "n_bootstrap": n_boot,
    }


def wilcoxon_signed_rank(diffs: list[float]) -> dict:
    """Approximate Wilcoxon signed-rank test (normal approximation, n>=25)."""
    nonzero = [(abs(d), 1 if d > 0 else -1) for d in diffs if d != 0]
    if not nonzero:
        return {"W_plus": 0, "W_minus": 0, "z": 0.0, "p_approx": 1.0}

    ranked = sorted(range(len(nonzero)), key=lambda i: nonzero[i][0])
    ranks = [0.0] * len(nonzero)
    i = 0
    while i < len(ranked):
        j = i
        while j < len(ranked) and nonzero[ranked[j]][0] == nonzero[ranked[i]][0]:
            j += 1
        avg_rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[ranked[k]] = avg_rank
        i = j

    W_plus = sum(ranks[i] for i in range(len(nonzero)) if nonzero[i][1] > 0)
    W_minus = sum(ranks[i] for i in range(len(nonzero)) if nonzero[i][1] < 0)
    n = len(nonzero)
    mean_W = n * (n + 1) / 4.0
    std_W = sqrt(n * (n + 1) * (2 * n + 1) / 24.0)
    z = (W_plus - mean_W) / std_W if std_W > 0 else 0.0
    # two-tailed normal approximation
    from math import erf, fabs
    p_approx = 1 - erf(fabs(z) / sqrt(2))

    return {
        "W_plus": round(W_plus, 1),
        "W_minus": round(W_minus, 1),
        "z": round(z, 4),
        "p_approx_two_sided": round(p_approx, 6),
        "significant_at_0.05": p_approx < 0.05,
    }


def pass_rate_wilson_ci(n_pass: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score 95% CI for a proportion."""
    if n == 0:
        return 0.0, 0.0
    p = n_pass / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    margin = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return round(max(0.0, centre - margin), 4), round(min(1.0, centre + margin), 4)


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    traces = [
        json.loads(l)
        for l in Path("bench/tenacious_bench_v0.1/held_out_traces.jsonl")
        .read_text(encoding="utf-8").splitlines()
        if l.strip()
    ]

    n = len(traces)
    baseline    = [t["baseline_score"]     for t in traces]
    guarded     = [t["base_guarded_score"] for t in traces]
    adapter     = [t["adapter_score"]      for t in traces]

    # ── ΔA: SFT adapter vs unguarded baseline ─────────────────────────────
    delta_a_boot = paired_bootstrap(baseline, adapter)
    delta_a_wcx  = wilcoxon_signed_rank([a - b for a, b in zip(baseline, adapter)])

    # ── ΔB: SFT adapter vs guarded prompt-only ────────────────────────────
    delta_b_boot = paired_bootstrap(guarded, adapter)
    delta_b_wcx  = wilcoxon_signed_rank([a - b for a, b in zip(guarded, adapter)])

    # ── ΔG: guarded vs unguarded (guardrail lift) ─────────────────────────
    delta_g_boot = paired_bootstrap(baseline, guarded)
    delta_g_wcx  = wilcoxon_signed_rank([a - b for a, b in zip(baseline, guarded)])

    # ── Pass rate comparisons with Wilson CI ──────────────────────────────
    n_pass_baseline = sum(1 for s in baseline if s >= 0.75)
    n_pass_guarded  = sum(1 for s in guarded  if s >= 0.75)
    n_pass_adapter  = sum(1 for s in adapter  if s >= 0.75)

    # ── Per-task summary ──────────────────────────────────────────────────
    improved  = sum(1 for a, b in zip(baseline, adapter) if b > a)
    degraded  = sum(1 for a, b in zip(baseline, adapter) if b < a)
    same      = n - improved - degraded

    improved_b  = sum(1 for a, b in zip(guarded, adapter) if b > a)
    degraded_b  = sum(1 for a, b in zip(guarded, adapter) if b < a)
    same_b      = n - improved_b - degraded_b

    output = {
        "meta": {
            "description": "Paired bootstrap (n=10,000) + Wilcoxon signed-rank tests for Tenacious-Bench v0.1 ablation",
            "n_tasks": n,
            "bootstrap_seed": 42,
            "n_bootstrap": 10_000,
            "pass_threshold": 0.75,
            "conditions": {
                "B0": "Unguarded baseline — pre-guardrail candidate outputs in held_out.jsonl",
                "B1": "Guarded prompt-only — full Style Guide v2 system prompt + 5 guardrails",
                "B2": "SFT adapter — tenacious-lora-v2 (Qwen2.5-1.5B, LoRA r=16 a=32, 100 steps)",
            },
        },
        "descriptive": {
            "B0_unguarded": {
                "mean_score": round(sum(baseline) / n, 6),
                "n_pass": n_pass_baseline,
                "pass_rate": round(n_pass_baseline / n, 4),
                "pass_rate_ci_95": pass_rate_wilson_ci(n_pass_baseline, n),
            },
            "B1_guarded": {
                "mean_score": round(sum(guarded) / n, 6),
                "n_pass": n_pass_guarded,
                "pass_rate": round(n_pass_guarded / n, 4),
                "pass_rate_ci_95": pass_rate_wilson_ci(n_pass_guarded, n),
            },
            "B2_adapter": {
                "mean_score": round(sum(adapter) / n, 6),
                "n_pass": n_pass_adapter,
                "pass_rate": round(n_pass_adapter / n, 4),
                "pass_rate_ci_95": pass_rate_wilson_ci(n_pass_adapter, n),
            },
        },
        "delta_A_adapter_vs_unguarded": {
            "description": "B2 (SFT adapter) vs B0 (unguarded baseline)",
            "observed_delta_mean": delta_a_boot["observed_delta"],
            "bootstrap": delta_a_boot,
            "wilcoxon": delta_a_wcx,
            "per_task": {"improved": improved, "same": same, "degraded": degraded},
            "conclusion": (
                "SIGNIFICANT" if delta_a_boot["significant_at_0.05"]
                else "NOT SIGNIFICANT"
            ),
        },
        "delta_B_adapter_vs_guarded": {
            "description": "B2 (SFT adapter) vs B1 (guarded prompt-only) — primary test",
            "observed_delta_mean": delta_b_boot["observed_delta"],
            "bootstrap": delta_b_boot,
            "wilcoxon": delta_b_wcx,
            "per_task": {"improved": improved_b, "same": same_b, "degraded": degraded_b},
            "conclusion": (
                "SIGNIFICANT — SFT training beats guarded prompt-only baseline"
                if delta_b_boot["significant_at_0.05"]
                else "NOT SIGNIFICANT — cannot reject H0"
            ),
        },
        "delta_G_guardrails_vs_unguarded": {
            "description": "B1 (guarded) vs B0 (unguarded) — guardrail lift",
            "observed_delta_mean": delta_g_boot["observed_delta"],
            "bootstrap": delta_g_boot,
            "wilcoxon": delta_g_wcx,
            "conclusion": (
                "SIGNIFICANT" if delta_g_boot["significant_at_0.05"]
                else "NOT SIGNIFICANT"
            ),
        },
    }

    out_path = Path("bench/ablations/statistical_test.json")
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")

    print("-- Statistical Test Results -------------------------------------")
    print(f"  n tasks: {n}   bootstrap iterations: 10,000   seed: 42")
    print()
    for key, label in [
        ("delta_G_guardrails_vs_unguarded", "DG  Guardrails vs unguarded"),
        ("delta_A_adapter_vs_unguarded",    "DA  Adapter   vs unguarded"),
        ("delta_B_adapter_vs_guarded",      "DB  Adapter   vs guarded  "),
    ]:
        r = output[key]
        b = r["bootstrap"]
        print(f"  {label}")
        print(f"    delta = {b['observed_delta']:+.4f}   "
              f"95% CI [{b['ci_95_lo']:+.4f}, {b['ci_95_hi']:+.4f}]   "
              f"p = {b['p_value_one_sided']:.4f}   {r['conclusion']}")
    print()
    print(f"  Written -> {out_path}")


if __name__ == "__main__":
    main()
