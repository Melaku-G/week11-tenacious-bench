"""Generate R3 human annotation sheet for IRA."""
from __future__ import annotations
import json
from pathlib import Path

DIMS = ["signal_fidelity", "tone_compliance", "segment_gate", "confidence_hedging", "format_compliance"]

ids = json.loads(Path("bench/ira_sample_ids.json").read_text(encoding="utf-8"))
r2 = {r["task_id"]: r for r in json.loads(Path("bench/ira_r2_results.json").read_text(encoding="utf-8"))}
index: dict[str, dict] = {}
for part in ("train", "dev", "held_out"):
    for line in Path(f"bench/tenacious_bench_v0.1/{part}.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            t = json.loads(line)
            index[t["task_id"]] = t

lines = [
    "# R3 Human Annotation Sheet — Tenacious-Bench v0.1 IRA",
    "",
    "**Annotator:** ___________________  **Date:** 2026-04-30",
    "",
    "## Instructions",
    "",
    "For each task: read the enrichment brief and candidate email, score each",
    "dimension 0 or 1. Write a one-sentence justification. Do NOT look at R1/R2 scores first.",
    "",
    "### Rubric Quick Reference",
    "",
    "| Dimension | FAIL (0) | PASS (1) |",
    "|-----------|----------|----------|",
    "| signal_fidelity | Email claims growth not supported by brief | Claims match brief |",
    "| tone_compliance | Any banned phrase present | Zero banned phrases |",
    "| segment_gate | AI/LLM pitch when ai_maturity_score < 2 | No AI pitch or score >= 2 |",
    "| confidence_hedging | icp_confidence=low OR low_peer_count=True AND no hedging words | Hedging present when required |",
    "| format_compliance | Missing [DRAFT], body > 120 words, or bench capacity commitment | All format conditions met |",
    "",
    "**Banned phrases:** scaling aggressively, rapid growth, explosive growth, industry leader,"
    " cutting-edge, revolutionize",
    "",
    "**Hedging words:** may, might, some indication, limited data, based on available signals,"
    " appears to, suggests",
    "",
    "---",
    "",
]

for i, tid in enumerate(ids, 1):
    task = index.get(tid, {})
    brief = task.get("input", {}).get("enrichment_brief", {})
    out = task.get("candidate_output", {})
    r1_ds = task.get("dimension_scores", {})
    r2_data = r2.get(tid, {})
    r2_ds = r2_data.get("r2_dimension_scores", {})

    disputes = []
    for d in DIMS:
        r1_val = r1_ds.get(d, {})
        r1_score = int(r1_val.get("score", 0)) if isinstance(r1_val, dict) else int(r1_val)
        if r1_score != r2_ds.get(d, 0):
            disputes.append(d)

    body = out.get("email_body", "")
    wc = len(body.split())

    lines.append(f"## Task {i:02d}: {tid}")
    lines.append(
        f"**Category:** {task.get('category', '?')} | "
        f"**Source:** {task.get('source', '?')} | "
        f"**Dispute dims:** {', '.join(disputes) if disputes else 'none'}"
    )
    lines.append("")
    lines.append("### Enrichment Brief")
    lines.append("```")
    for k, v in brief.items():
        lines.append(f"  {k}: {v}")
    lines.append("```")
    lines.append("")
    lines.append("### Candidate Email")
    lines.append(f"**Subject:** `{out.get('email_subject', '')}`")
    lines.append("")
    lines.append(f"**Body** ({wc} words):")
    lines.append("")
    lines.append(body.strip())
    lines.append("")
    lines.append("### Scores")
    lines.append("| Dimension | R1 | R2 | **R3** | R3 Justification |")
    lines.append("|-----------|----|----|--------|------------------|")
    for d in DIMS:
        r1_val = r1_ds.get(d, {})
        r1_score = int(r1_val.get("score", 0)) if isinstance(r1_val, dict) else int(r1_val)
        r2_score = r2_ds.get(d, "?")
        flag = " ← DISPUTE" if d in disputes else ""
        lines.append(f"| {d} | {r1_score} | {r2_score} | ____{flag} | |")
    lines.append("")
    lines.append("---")
    lines.append("")

out_path = Path("bench/ira_r3_annotation_sheet.md")
out_path.write_text("\n".join(lines), encoding="utf-8")
print(f"Written {out_path} ({len(ids)} tasks, {sum(1 for l in lines if 'DISPUTE' in l)} disputed cells)")
