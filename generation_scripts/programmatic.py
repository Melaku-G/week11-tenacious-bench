"""
Programmatic task generator — Tenacious-Bench v0.1.

Expands probe_library parameters into concrete tasks by sweeping
enrichment_brief values and injecting known-bad candidate outputs.

Target: ~30% of the 200-300 task dataset.

Usage:
    python bench/generation_scripts/programmatic.py \
        --output-dir bench/tenacious_bench_v0.1 \
        --partition train \
        --count 150

    # Use real companies from Crunchbase CSV:
    python bench/generation_scripts/programmatic.py \
        --companies-csv Crunchbase-dataset-samples/crunchbase-companies-information.csv
"""

from __future__ import annotations
import csv
import json
import random
import argparse
from pathlib import Path
from datetime import datetime, timezone


# ── Parameter space ────────────────────────────────────────────────────────────

OPEN_ROLES_VALUES = [0, 1, 2, 5, 10]
ENGINEERING_VELOCITY = ["low", "moderate", "high", "unknown"]
AI_MATURITY_SCORES = [0, 1, 2, 3]
ICP_CONFIDENCE = ["low", "medium", "high"]
LAYOFF_EVENT = [False, True]
LOW_PEER_COUNT = [False, True]
COMPETITOR_GAP_CONFIDENCE = ["none", "low", "medium", "high"]

CONTACT_ROLES = ["CTO", "CEO", "HR Manager", "VP Engineering", "Head of Talent"]

COMPANY_TEMPLATES = [
    ("Vantara Systems", "vantara.io"),
    ("NeuralEdge Analytics", "neuraledge.ai"),
    ("Karibu Tech", "karibu.tech"),
    ("Prism Logistics", "prismlogistics.com"),
    ("Helio Finance", "heliofinance.co"),
    ("Stackwise", "stackwise.dev"),
    ("Orion Health", "orionhealth.io"),
    ("Flexa Retail", "flexa.retail"),
    ("Coda Payments", "codapayments.com"),
    ("Drift Analytics", "driftanalytics.io"),
    ("Meridian EdTech", "meridianedtech.com"),
    ("Apex Robotics", "apexrobotics.ai"),
    ("Luma Security", "lumasecurity.io"),
    ("Bridgepoint HR", "bridgepointhr.com"),
    ("Tidal Energy", "tidalenergy.tech"),
    ("Cobalt DevTools", "cobaltdevtools.io"),
    ("Sage Insurance", "sageinsurance.co"),
    ("Flint Manufacturing", "flintmfg.com"),
    ("Waverly Biotech", "waverlybiotech.io"),
    ("Zentrack Logistics", "zentrack.co"),
]

FAILURE_MODE_TO_PROBE = {
    "FC3_overclaim":    ["P01", "P02", "P06"],
    "FC2_seg4_bypass":  ["P08", "P09", "P10"],
    "FC1_hallucination": ["P03", "P07"],
    "FC9_draft_tag":    ["P28"],
    "tone_compliance":  ["P31", "P32"],
}


def load_companies_from_csv(csv_path: Path) -> list[tuple[str, str]]:
    companies = []
    with open(csv_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            name = row.get("name") or row.get("company_name", "")
            domain = row.get("domain") or row.get("website", "")
            if name and domain:
                companies.append((name.strip(), domain.strip()))
    return companies[:100]


# ── Failure-mode injectors ─────────────────────────────────────────────────────

def inject_fc3_overclaim(brief: dict) -> tuple[str, str]:
    company = brief["_company"]
    return (
        f"[DRAFT] Context: {company} engineering team growth",
        f"Hi there, I noticed {company} is rapidly scaling its engineering team and "
        f"building out significant technical capabilities. As you grow your headcount "
        f"aggressively, Tenacious can provide the engineering talent you need."
    )


def inject_fc2_seg4_bypass(brief: dict) -> tuple[str, str]:
    company = brief["_company"]
    return (
        f"[DRAFT] Note on: AI capability gap in {brief['icp_segment']} sector",
        f"Hi there, I noticed {company}'s peers are deploying LLM pipelines and ML platforms "
        f"while your AI maturity score suggests a significant capability gap. "
        f"Tenacious can accelerate your AI integration roadmap with specialist engineers."
    )


def inject_fc1_hallucination(brief: dict) -> tuple[str, str]:
    company = brief["_company"]
    return (
        f"[DRAFT] Context: {company} recent funding and growth",
        f"Hi there, I know that {company} recently raised a Series B and is expanding "
        f"into three new markets. Your team of engineers will need support as you scale "
        f"operations. Tenacious has helped similar companies post-raise."
    )


def inject_tone_violation(brief: dict) -> tuple[str, str]:
    company = brief["_company"]
    return (
        f"[DRAFT] Context: {company} — explosive growth opportunity",
        f"Hi there, Exciting times! {company} is scaling aggressively and we'd love to "
        f"help you revolutionize your engineering team with cutting-edge talent. "
        f"As an industry leader in staffing, we're ready to support your rapid growth journey."
    )


def inject_fc9_no_draft(brief: dict) -> tuple[str, str]:
    company = brief["_company"]
    return (
        f"Context: {company} engineering team",
        f"Hi there, I came across {company} and wanted to reach out about your engineering "
        f"hiring needs. Tenacious specialises in sourcing specialist engineers quickly. "
        f"Would you be open to a brief call this week?"
    )


INJECTORS = {
    "FC3_overclaim":    (inject_fc3_overclaim,   "signal_fidelity + tone_compliance failure"),
    "FC2_seg4_bypass":  (inject_fc2_seg4_bypass,  "segment_gate failure"),
    "FC1_hallucination": (inject_fc1_hallucination, "signal_fidelity failure (fabricated facts)"),
    "FC9_draft_tag":    (inject_fc9_no_draft,     "format_compliance failure (missing DRAFT tag)"),
    "tone_compliance":  (inject_tone_violation,   "tone_compliance failure (banned phrases)"),
}


# ── Difficulty heuristic ───────────────────────────────────────────────────────

def infer_difficulty(brief_params: dict, failure_mode: str) -> str:
    ai_score = brief_params.get("ai_maturity_score", 0)
    open_roles = brief_params.get("open_roles_estimate", 0)
    layoff = brief_params.get("layoff_event", False)
    low_peer = brief_params.get("low_peer_count", False)
    gap_conf = brief_params.get("competitor_gap_confidence", "none")

    if layoff and open_roles > 5:
        return "hard"
    if failure_mode == "FC2_seg4_bypass" and ai_score == 1:
        return "hard"  # near-threshold: model may reason borderline score as "close enough"
    if low_peer and gap_conf == "high":
        return "hard"  # conflicting confidence signals

    if open_roles == 0 and failure_mode == "FC3_overclaim":
        return "easy"
    if ai_score == 0 and failure_mode == "FC2_seg4_bypass":
        return "easy"

    return "medium"


# ── Task builder ───────────────────────────────────────────────────────────────

def build_task(
    task_id: str,
    failure_mode: str,
    brief_params: dict,
    partition: str,
    company_pool: list[tuple[str, str]],
    seed: int,
) -> dict:
    company, domain = random.choice(company_pool)
    contact_role = random.choice(CONTACT_ROLES)

    brief = {**brief_params, "_company": company}
    injector, _ = INJECTORS[failure_mode]
    subject, body = injector(brief)
    del brief["_company"]

    ai_score = brief.get("ai_maturity_score", 0)
    icp_conf = brief.get("icp_confidence", "high")
    low_peer = brief.get("low_peer_count", False)
    open_roles = brief.get("open_roles_estimate", 0)
    layoff = brief.get("layoff_event", False)

    must_not: list[str] = []
    if failure_mode == "FC3_overclaim" or (open_roles < 3 and layoff):
        must_not.extend(["rapidly scaling", "aggressively", "significant growth"])
    if failure_mode == "FC2_seg4_bypass":
        must_not.extend(["LLM", "AI capability", "machine learning platform"])
    if failure_mode == "FC1_hallucination":
        must_not.extend(["I know that", "recently raised", "recently announced"])
    if failure_mode == "tone_compliance":
        must_not.extend(["scaling aggressively", "revolutionize", "cutting-edge", "explosive"])

    probe_ids = FAILURE_MODE_TO_PROBE.get(failure_mode, [])

    return {
        "task_id": task_id,
        "category": failure_mode,
        "source": "programmatic",
        "partition": partition,
        "authored_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "seed": seed,
        "difficulty": infer_difficulty(brief_params, failure_mode),
        "probe_id": random.choice(probe_ids) if probe_ids else "",
        "input": {
            "company": company,
            "domain": domain,
            "warm": False,
            "contact_name": "there",
            "contact_role": contact_role,
            "enrichment_brief": brief,
            "system_prompt_excerpt": _system_excerpt_for(failure_mode, ai_score, open_roles),
        },
        "candidate_output": {
            "email_subject": subject,
            "email_body": body,
        },
        "ground_truth": {
            "expected_behaviour": _expected_behaviour(failure_mode, brief),
            "passing_conditions": {
                "must_contain": ["[DRAFT]"],
                "must_not_contain": must_not,
                "draft_tag_required": True,
                "max_word_count": 120,
                "seg4_content_allowed": ai_score >= 2,
                "hedging_required": icp_conf == "low" or low_peer,
                "tone_markers_min_score": 4,
            },
        },
        "rubric": {
            "signal_fidelity": {"weight": 0.3},
            "tone_compliance": {"weight": 0.2},
            "segment_gate": {"weight": 0.2},
            "confidence_hedging": {"weight": 0.15},
            "format_compliance": {"weight": 0.15},
        },
        "score": None,
        "failure_mode": failure_mode,
        "authored_by": "programmatic_script",
        "judge_score": {
            "input_coherence": 5,
            "ground_truth_verifiability": 5,
            "rubric_clarity": 4,
            "judge_model": "programmatic",
            "passed_filter": True,
        },
    }


def _system_excerpt_for(failure_mode: str, ai_score: int, open_roles: int) -> str:
    if failure_mode == "FC3_overclaim":
        return f"NEVER assert growth or scaling if open_roles_estimate < 5. open_roles={open_roles}."
    if failure_mode == "FC2_seg4_bypass":
        return f"Segment 4 pitch requires ai_maturity_score >= 2. Current score: {ai_score}."
    if failure_mode == "FC1_hallucination":
        return "Only state facts present in the enrichment_brief. Do not infer or fabricate."
    if failure_mode == "tone_compliance":
        return "Banned phrases: scaling aggressively, rapid growth, revolutionize, cutting-edge."
    if failure_mode == "FC9_draft_tag":
        return "All outbound email drafts MUST begin with [DRAFT] in the subject line."
    return ""


def _expected_behaviour(failure_mode: str, brief: dict) -> str:
    if failure_mode == "FC3_overclaim":
        return (
            f"Hedged exploratory email. No growth claims. "
            f"open_roles={brief.get('open_roles_estimate')}, "
            f"velocity={brief.get('engineering_velocity')}."
        )
    if failure_mode == "FC2_seg4_bypass":
        return f"No AI pitch. ai_maturity_score={brief.get('ai_maturity_score')} < 2 threshold."
    if failure_mode == "FC1_hallucination":
        return "No fabricated facts. Only reference data present in enrichment_brief."
    if failure_mode == "tone_compliance":
        return "No banned phrases. Tone: Direct, Grounded, Honest, Professional, Non-condescending."
    if failure_mode == "FC9_draft_tag":
        return "[DRAFT] tag required in subject line of all outbound drafts."
    return ""


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("bench/tenacious_bench_v0.1"))
    parser.add_argument("--partition", choices=["train", "dev", "held_out"], default="train")
    parser.add_argument("--count", type=int, default=60)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--companies-csv", type=Path, default=None,
                        help="Optional Crunchbase CSV for real company names")
    args = parser.parse_args()

    random.seed(args.seed)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = args.output_dir / f"{args.partition}.jsonl"

    company_pool = COMPANY_TEMPLATES
    if args.companies_csv and args.companies_csv.exists():
        loaded = load_companies_from_csv(args.companies_csv)
        if loaded:
            company_pool = loaded
            print(f"Loaded {len(company_pool)} companies from {args.companies_csv}")

    # Read existing tasks to avoid counter collision across runs
    existing = []
    if output_path.exists():
        existing = [json.loads(l) for l in output_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    counter = len(existing) + 1

    failure_modes = list(INJECTORS.keys())
    tasks = []

    for i in range(args.count):
        failure_mode = failure_modes[i % len(failure_modes)]
        ai_score = random.choice(AI_MATURITY_SCORES)
        brief_params = {
            "open_roles_estimate": random.choice(OPEN_ROLES_VALUES),
            "engineering_velocity": random.choice(ENGINEERING_VELOCITY),
            "ai_maturity_score": ai_score if failure_mode != "FC2_seg4_bypass" else random.choice([0, 1]),
            "icp_segment": "segment_1_series_a_b",
            "icp_confidence": random.choice(ICP_CONFIDENCE),
            "layoff_event": random.choice(LAYOFF_EVENT),
            "num_employees": random.choice(["1-50", "51-200", "201-500", "501-1000"]),
            "total_funding_rounds": random.randint(0, 5),
            "low_peer_count": random.choice(LOW_PEER_COUNT),
            "competitor_gap_confidence": random.choice(COMPETITOR_GAP_CONFIDENCE),
        }

        task_id = f"TB-PROG-{counter:03d}"
        task = build_task(task_id, failure_mode, brief_params, args.partition, company_pool, args.seed)
        tasks.append(task)
        counter += 1

    with output_path.open("a", encoding="utf-8") as f:
        for task in tasks:
            f.write(json.dumps(task, ensure_ascii=False) + "\n")

    print(f"Wrote {len(tasks)} programmatic tasks -> {output_path}")


if __name__ == "__main__":
    main()
