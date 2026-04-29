"""
Converts the 24 labeled examples from "Tenacious Style Guide v2" into bench tasks
and appends 18 to train.jsonl and 6 to dev.jsonl.

IDs: TB-ADV-006 through TB-ADV-029 (existing hand-authored max is TB-ADV-005).
source_mode: hand_authored
"""

from __future__ import annotations
import json
from pathlib import Path

TRAIN_FILE = Path("bench/tenacious_bench_v0.1/train.jsonl")
DEV_FILE   = Path("bench/tenacious_bench_v0.1/dev.jsonl")

SYSTEM_PROMPT_EXCERPT = (
    "You are a B2B SDR for Tenacious Consulting & Outsourcing. Write a concise [DRAFT] "
    "outreach email grounded in the enrichment_brief. Body ≤120 words cold / ≤200 warm. "
    "Tone: Direct, Grounded, Honest, Professional, Non-condescending. "
    "No banned phrases. Hedge when icp_confidence=low. No AI pitch if ai_maturity_score < 2."
)

# ---------------------------------------------------------------------------
# Task definitions — (enrichment_brief, candidate_output, ground_truth, partition)
# ---------------------------------------------------------------------------

TASKS_RAW = [

    # ── GOOD EXAMPLES ──────────────────────────────────────────────────────

    {   # GOOD #1 — Series A funding + role velocity, high signal
        "task_id": "TB-ADV-006",
        "category": "good_example_signal_grounding",
        "partition": "train",
        "input": {
            "company": "Luminary Software",
            "domain": "luminarysoftware.com",
            "warm": False,
            "contact_name": "Maya Chen",
            "contact_role": "VP of Engineering",
            "enrichment_brief": {
                "funding_round": "Series A",
                "funding_amount_m": 14,
                "funding_date": "2026-02-10",
                "open_roles_estimate": 7,
                "engineering_velocity": "high",
                "layoff_event": False,
                "icp_confidence": "high",
                "ai_maturity_score": 1,
                "low_peer_count": False,
            },
        },
        "candidate_output": {
            "email_subject": "[DRAFT] Request: 15 minutes on your Q3 Python hiring",
            "email_body": (
                "Hi Maya,\n\nYou closed your $14M Series A in February and your open Python "
                "engineering roles went from 2 to 7 in the last 60 days. The typical bottleneck "
                "for teams in that state is recruiting capacity, not budget.\n\nWe place dedicated "
                "Python and data engineers, managed by Tenacious, with a minimum three hours of "
                "synchronous overlap. We can plug a team in within 48 hours while you continue "
                "your full-time search.\n\nWould 15 minutes next week be useful? I'll bring two "
                "case studies from Series A SaaS clients who hit the same wall.\n\nBest,\nYabi"
            ),
        },
        "ground_truth": {
            "expected_behaviour": "Email names the funding amount, date, and exact role-count trend. "
                "One ask (15 minutes). No banned phrases. No 'bench'. Body ≤120 words.",
            "passing_conditions": {
                "signal_fidelity": "pass — high signal, no unsupported claims",
                "tone_compliance": "pass — no banned phrases",
                "segment_gate": "pass — no AI pitch; ai_maturity_score=1",
                "confidence_hedging": "n/a — icp_confidence=high",
                "format_compliance": "pass — [DRAFT] present, body ~89 words, subject ≤60",
            },
        },
    },

    {   # GOOD #2 — Post-layoff cost-pressure pitch
        "task_id": "TB-ADV-007",
        "category": "good_example_layoff_grounding",
        "partition": "train",
        "input": {
            "company": "Meridian Analytics",
            "domain": "meridiananalytics.io",
            "warm": False,
            "contact_name": "Daniel Park",
            "contact_role": "CTO",
            "enrichment_brief": {
                "open_roles_estimate": 2,
                "engineering_velocity": "low",
                "layoff_event": True,
                "layoff_pct": 12,
                "layoff_date": "2026-03-15",
                "icp_confidence": "high",
                "ai_maturity_score": 1,
                "low_peer_count": False,
            },
        },
        "candidate_output": {
            "email_subject": "[DRAFT] Context: lower-cost capacity post-restructure",
            "email_body": (
                "Hi Daniel,\n\nI saw the announcement that your team contracted by about 12% "
                "in March. Companies in your stage often need to maintain delivery output while "
                "reducing fully-loaded cost — that is the engagement pattern we run most often.\n\n"
                "Tenacious places managed engineering teams under our project management. Senior "
                "engineers in Python, data, and ML start from $X,XXX/month, with a one-month "
                "minimum and two-week extension blocks. No long-term commitment.\n\nIf you are "
                "scoping the next twelve months of delivery capacity, I can share two short case "
                "studies from mid-market clients who replaced a portion of their delivery cost "
                "this way.\n\nBest,\nYabi"
            ),
        },
        "ground_truth": {
            "expected_behaviour": "Acknowledges the layoff respectfully, uses conditional language "
                "('if you are scoping'), quotes only public pricing bands, avoids upbeat framing.",
            "passing_conditions": {
                "signal_fidelity": "pass — layoff named specifically, no unsupported growth claims",
                "tone_compliance": "pass — no banned phrases",
                "segment_gate": "pass — no AI pitch",
                "confidence_hedging": "n/a — icp_confidence=high",
                "format_compliance": "pass — [DRAFT] present, body ~100 words",
            },
        },
    },

    {   # GOOD #3 — New CTO 90-day window
        "task_id": "TB-ADV-008",
        "category": "good_example_leadership_change",
        "partition": "train",
        "input": {
            "company": "Helix Systems",
            "domain": "helixsystems.com",
            "warm": False,
            "contact_name": "Priya Nair",
            "contact_role": "CTO",
            "enrichment_brief": {
                "leadership_change": True,
                "leadership_change_role": "CTO",
                "leadership_change_date": "2026-04-11",
                "open_roles_estimate": 3,
                "engineering_velocity": "medium",
                "layoff_event": False,
                "icp_confidence": "high",
                "ai_maturity_score": 1,
                "low_peer_count": False,
            },
        },
        "candidate_output": {
            "email_subject": "[DRAFT] Context: a brief on offshore engineering models",
            "email_body": (
                "Hi Priya,\n\nWelcome to your new role at Helix — I saw the announcement on the "
                "14th. New engineering leaders typically reassess vendor and offshore mix in their "
                "first 90 days.\n\nI do not want to add to your inbox in week three of a new job. "
                "I will leave you with one thing: a one-page brief on the four offshore engagement "
                "models we see most often, with the trade-offs honestly laid out (including where "
                "each model fails).\n\nIf a 15-minute conversation in November would be useful, "
                "the calendar is at gettenacious.com/yabi. If not, no follow-up.\n\nBest,\nYabi"
            ),
        },
        "ground_truth": {
            "expected_behaviour": "Names the leadership-change date, lowers the ask, offers "
                "honest trade-off resource including where the model fails. Explicit no-follow-up.",
            "passing_conditions": {
                "signal_fidelity": "pass — leadership change named, no unsupported growth claims",
                "tone_compliance": "pass — no banned phrases",
                "segment_gate": "pass — no AI pitch",
                "confidence_hedging": "n/a — icp_confidence=high",
                "format_compliance": "pass — [DRAFT] present, body ~96 words",
            },
        },
    },

    {   # GOOD #4 — Capability gap, AI maturity 2, high confidence
        "task_id": "TB-ADV-009",
        "category": "good_example_seg4_correct",
        "partition": "train",
        "input": {
            "company": "LoyaltyLabs",
            "domain": "loyaltylabs.io",
            "warm": False,
            "contact_name": "Felix Auer",
            "contact_role": "VP Engineering",
            "enrichment_brief": {
                "open_roles_estimate": 4,
                "engineering_velocity": "medium",
                "layoff_event": False,
                "icp_confidence": "high",
                "ai_maturity_score": 2,
                "low_peer_count": False,
                "peer_mlops_openings": 3,
            },
        },
        "candidate_output": {
            "email_subject": "[DRAFT] Question: your MLOps function in 2026",
            "email_body": (
                "Hi Felix,\n\nThree companies adjacent to yours in the loyalty-platform space "
                "— A, B, and C — posted senior MLOps engineer roles in the last 90 days. Your "
                "team has not, at least not publicly. Two readings: a deliberate choice, or a "
                "function that has not yet been scoped.\n\nWe staff specialized squads (ML "
                "platform, agentic systems, data contracts) on fixed-scope project engagements, "
                "typically 3 to 4 months. Starter scopes from $XX,XXX. We do not pitch this "
                "where there is no real need.\n\nIf you have already scoped this and decided "
                "against it, I would genuinely be curious why. If not, 15 minutes is enough to "
                "walk through what those three peer companies are doing.\n\nBest,\nYabi"
            ),
        },
        "ground_truth": {
            "expected_behaviour": "AI pitch correct at ai_maturity_score=2. Frames gap as two "
                "readings. Asks for prospect's reasoning. One ask. ≤120 words.",
            "passing_conditions": {
                "signal_fidelity": "pass — peer data named, no unsupported growth claims",
                "tone_compliance": "pass — no banned phrases",
                "segment_gate": "pass — ai_maturity_score=2 permits Seg4 pitch",
                "confidence_hedging": "n/a — icp_confidence=high",
                "format_compliance": "pass — [DRAFT] present, body ~117 words",
            },
        },
    },

    {   # GOOD #5 — Weak signal, asks rather than asserts
        "task_id": "TB-ADV-010",
        "category": "good_example_weak_signal_hedging",
        "partition": "train",
        "input": {
            "company": "DataBridge Corp",
            "domain": "databridgecorp.com",
            "warm": False,
            "contact_name": "Tom Whitfield",
            "contact_role": "Head of Engineering",
            "enrichment_brief": {
                "open_roles_estimate": 2,
                "engineering_velocity": "low",
                "layoff_event": False,
                "icp_confidence": "low",
                "ai_maturity_score": 1,
                "low_peer_count": True,
            },
        },
        "candidate_output": {
            "email_subject": "[DRAFT] Question: are your data engineering hires keeping up?",
            "email_body": (
                "Hi Tom,\n\nTwo open data engineer roles on your careers page — I cannot tell "
                "from the outside whether that means hiring is keeping pace or whether the queue "
                "is longer than the postings suggest.\n\nWe place managed data and Python "
                "engineering teams, three-hour overlap with US time zones, one-month minimum. "
                "If the queue is longer than the posts, that is the pattern we solve most often.\n\n"
                "If two roles is the actual demand and you are well-staffed to meet it, ignore "
                "this. If the real number is higher, a 15-minute conversation costs you nothing.\n\n"
                "Best,\nYabi"
            ),
        },
        "ground_truth": {
            "expected_behaviour": "Honest about signal limits ('I cannot tell from the outside'). "
                "Interrogative framing throughout. Explicit out ('ignore this'). "
                "Hedging present for low-confidence signal.",
            "passing_conditions": {
                "signal_fidelity": "pass — no unsupported claims; signal acknowledged as limited",
                "tone_compliance": "pass — no banned phrases",
                "segment_gate": "pass — no AI pitch; ai_maturity_score=1",
                "confidence_hedging": "pass — hedging present (icp_confidence=low, low_peer_count=True)",
                "format_compliance": "pass — [DRAFT] present, body ~105 words",
            },
        },
    },

    {   # GOOD #6 — Value-add resource, no pitch
        "task_id": "TB-ADV-011",
        "category": "good_example_resource_touch",
        "partition": "train",
        "input": {
            "company": "Seedling AI",
            "domain": "seedlingai.com",
            "warm": False,
            "contact_name": "Ana Ferreira",
            "contact_role": "Founder & CTO",
            "enrichment_brief": {
                "funding_round": "Seed extension",
                "funding_date": "2026-10-15",
                "open_roles_estimate": 3,
                "engineering_velocity": "medium",
                "layoff_event": False,
                "icp_confidence": "medium",
                "ai_maturity_score": 1,
                "low_peer_count": True,
            },
        },
        "candidate_output": {
            "email_subject": "[DRAFT] Resource: Series A engineering scale-up checklist",
            "email_body": (
                "Hi Ana,\n\nYou closed your seed extension in October and your first three "
                "engineering hires are public on LinkedIn. The window between now and your "
                "Series A is the one where most teams' delivery process either compounds or "
                "stalls.\n\nI put together a one-page checklist of the seven decisions that "
                "determine which side a team lands on — including when offshore augmentation "
                "pays back and when it does not. Two of the items are arguments against hiring "
                "an outsourced team in your stage.\n\nWant me to send the PDF? No follow-up "
                "if you are not interested.\n\nBest,\nYabi"
            ),
        },
        "ground_truth": {
            "expected_behaviour": "Pure value-add first touch. Names specific public signals. "
                "Includes honest trade-offs (arguments against Tenacious). Lowest-friction ask.",
            "passing_conditions": {
                "signal_fidelity": "pass — seed extension and hire count cited",
                "tone_compliance": "pass — no banned phrases",
                "segment_gate": "pass — no AI pitch",
                "confidence_hedging": "pass — hedging present (low_peer_count=True)",
                "format_compliance": "pass — [DRAFT] present, body ~105 words",
            },
        },
    },

    {   # GOOD #7 — Warm reply, bench routing to human
        "task_id": "TB-ADV-012",
        "category": "good_example_warm_reply_routing",
        "partition": "train",
        "input": {
            "company": "Camila's Startup",
            "domain": "camila-startup.io",
            "warm": True,
            "contact_name": "Camila Reyes",
            "contact_role": "CTO",
            "enrichment_brief": {
                "open_roles_estimate": 5,
                "engineering_velocity": "high",
                "layoff_event": False,
                "icp_confidence": "high",
                "ai_maturity_score": 2,
                "low_peer_count": False,
            },
        },
        "candidate_output": {
            "email_subject": "[DRAFT] Re: scope of the three-engineer engagement",
            "email_body": (
                "Hi Camila,\n\nThanks for the reply and for the additional context on the "
                "December timeline.\n\nThree Python and one data engineer for a 6-month "
                "engagement is in our typical range. Our public-tier pricing for that mix "
                "starts from approximately $X,XXX/month per engineer at senior level, with "
                "a one-month minimum and two-week extension blocks thereafter.\n\nA specific "
                "quote depends on the exact stack, the timezone overlap requirement, and "
                "whether you want a Tenacious delivery lead embedded. The cleanest path is "
                "a 30-minute scoping call with our delivery lead, Arun, at "
                "gettenacious.com/arun.\n\nIf the December start date is firm, I would "
                "suggest booking this week so we can confirm capacity availability.\n\nBest,\nYabi"
            ),
        },
        "ground_truth": {
            "expected_behaviour": "Warm reply. Quotes only public pricing bands, routes specific "
                "quote to human delivery lead. Names why booking is recommended. Body ≤200 words.",
            "passing_conditions": {
                "signal_fidelity": "pass — warm context, no fabricated claims",
                "tone_compliance": "pass — no banned phrases, no 'bench' word",
                "segment_gate": "pass — ai_maturity_score=2",
                "confidence_hedging": "n/a — icp_confidence=high",
                "format_compliance": "pass — warm reply ≤200 words",
            },
        },
    },

    {   # GOOD #8 — Re-engagement with new content
        "task_id": "TB-ADV-013",
        "category": "good_example_reengagement",
        "partition": "train",
        "input": {
            "company": "VerticalSaaS Health",
            "domain": "verticalsaashealth.com",
            "warm": False,
            "contact_name": "Marcus Webb",
            "contact_role": "VP Engineering",
            "enrichment_brief": {
                "open_roles_estimate": 1,
                "engineering_velocity": "low",
                "layoff_event": False,
                "icp_confidence": "medium",
                "ai_maturity_score": 1,
                "low_peer_count": False,
                "sector_layoff_count_90d": 11,
                "prior_contact": True,
                "prior_contact_date": "2025-08-01",
            },
        },
        "candidate_output": {
            "email_subject": "[DRAFT] New: layoffs.fyi data on your sub-sector this quarter",
            "email_body": (
                "Hi Marcus,\n\nWhen we last spoke in August, you mentioned that the board "
                "had not yet pushed for cost rebalancing. Two new data points that may matter:\n\n"
                "First, the layoffs.fyi data shows your sub-sector (vertical SaaS for healthcare) "
                "had eleven announced contractions in the last 90 days, up from four in the prior "
                "quarter. Boards are reading the same data.\n\nSecond, three of those eleven "
                "companies are now using offshore-managed engineering teams within 60 days of "
                "restructure — that pattern is faster than it was a year ago.\n\nIf the "
                "conversation has reopened on your side, our managed engineering pricing has "
                "not changed. If not, no follow-up needed.\n\nBest,\nYabi"
            ),
        },
        "ground_truth": {
            "expected_behaviour": "Re-engagement carries new content, not guilt. Adds two "
                "specific verifiable data points. References prior conversation accurately. "
                "Explicit no-follow-up out.",
            "passing_conditions": {
                "signal_fidelity": "pass — layoffs.fyi data cited; sub-sector trend named",
                "tone_compliance": "pass — no banned phrases",
                "segment_gate": "pass — no AI pitch",
                "confidence_hedging": "pass — hedging words present (icp_confidence=medium)",
                "format_compliance": "pass — [DRAFT] present, body ~113 words",
            },
        },
    },

    {   # GOOD #9 — Bench-gated honest decline
        "task_id": "TB-ADV-014",
        "category": "good_example_bench_gate_decline",
        "partition": "train",
        "input": {
            "company": "ScaleForce",
            "domain": "scaleforce.io",
            "warm": True,
            "contact_name": "Will Hartman",
            "contact_role": "Head of Engineering",
            "enrichment_brief": {
                "open_roles_estimate": 15,
                "engineering_velocity": "high",
                "layoff_event": False,
                "icp_confidence": "high",
                "ai_maturity_score": 1,
                "low_peer_count": False,
                "bench_available_go": 6,
            },
        },
        "candidate_output": {
            "email_subject": "[DRAFT] Re: scaling to 15 engineers in 30 days",
            "email_body": (
                "Hi Will,\n\nThanks for the follow-up and for the trust to ask about the "
                "15-engineer ramp. Honest answer: 15 engineers across a Go and infra-heavy "
                "stack within 30 days is at the edge of what our current capacity can deliver "
                "responsibly.\n\nWhat we can confirm now: 6 to 8 engineers in that stack, "
                "starting within 21 days, with a Tenacious delivery lead embedded. Going to "
                "15 reliably requires a 60-day ramp window, with the back half of the team "
                "onboarding in weeks 5 and 6.\n\nIf the 30-day target is firm, I would rather "
                "refer you to a peer firm that fits the timeline than over-commit. Happy to "
                "introduce.\n\nBest,\nYabi"
            ),
        },
        "ground_truth": {
            "expected_behaviour": "Refuses to over-commit capacity beyond what bench supports. "
                "Names exactly what is available. Offers referral if timeline is not met. "
                "Body ≤200 words (warm reply).",
            "passing_conditions": {
                "signal_fidelity": "pass — capacity stated accurately (6-8 not 15)",
                "tone_compliance": "pass — no banned phrases, no 'bench' standalone",
                "segment_gate": "pass — ai_maturity_score=1, no AI pitch",
                "confidence_hedging": "n/a — icp_confidence=high",
                "format_compliance": "pass — warm reply ≤200 words, [DRAFT] present",
            },
        },
    },

    {   # GOOD #10 — AI maturity 0-1, Seg1 reframe
        "task_id": "TB-ADV-015",
        "category": "good_example_ai_maturity_low_reframe",
        "partition": "train",
        "input": {
            "company": "Axiom Backend",
            "domain": "axiombackend.com",
            "warm": False,
            "contact_name": "Sophia Larsen",
            "contact_role": "Founder & CTO",
            "enrichment_brief": {
                "funding_round": "Series A",
                "funding_amount_m": 9,
                "funding_date": "2026-03-01",
                "open_roles_estimate": 0,
                "engineering_velocity": "low",
                "layoff_event": False,
                "icp_confidence": "high",
                "ai_maturity_score": 0,
                "low_peer_count": False,
                "team_size": 10,
            },
        },
        "candidate_output": {
            "email_subject": "[DRAFT] Question: standing up your first AI function",
            "email_body": (
                "Hi Sophia,\n\nYou closed your $9M Series A in March, your team is ten "
                "engineers, and your public roles are all backend and product. No AI or ML "
                "postings yet — which is a normal place to be at your stage, not a gap.\n\n"
                "If your roadmap has an AI feature in the next twelve months, the first hire "
                "is usually the wrong unit. A small dedicated squad (ML engineer plus data "
                "platform engineer plus a Tenacious delivery lead) for a 3-month scoped "
                "project is faster, cheaper, and lets you test whether AI is core enough to "
                "your roadmap to justify a full-time function.\n\nIf that is on your roadmap, "
                "15 minutes to walk through what the first 90 days look like. If not, ignore "
                "this.\n\nBest,\nYabi"
            ),
        },
        "ground_truth": {
            "expected_behaviour": "ai_maturity_score=0 → use Seg1 'stand up first AI function' "
                "framing, not Seg4 capability-gap pitch. Honest ('normal place to be, not a gap'). "
                "Conditional language throughout.",
            "passing_conditions": {
                "signal_fidelity": "pass — funding and team size cited from brief",
                "tone_compliance": "pass — no banned phrases",
                "segment_gate": "pass — soft AI mention framed as 'first function', not Seg4 pitch",
                "confidence_hedging": "n/a — icp_confidence=high",
                "format_compliance": "pass — [DRAFT] present, body ~120 words",
            },
        },
    },

    {   # GOOD #11 — Mutual connection, specific stack
        "task_id": "TB-ADV-016",
        "category": "good_example_warm_intro",
        "partition": "dev",
        "input": {
            "company": "DataNexus",
            "domain": "datanexus.io",
            "warm": True,
            "contact_name": "Mei Zhang",
            "contact_role": "Head of Data Engineering",
            "enrichment_brief": {
                "open_roles_estimate": 3,
                "engineering_velocity": "medium",
                "layoff_event": False,
                "icp_confidence": "high",
                "ai_maturity_score": 2,
                "low_peer_count": False,
                "tech_stack": ["Snowflake", "dbt", "Airflow"],
                "warm_intro_from": "Arjun Krishnan",
            },
        },
        "candidate_output": {
            "email_subject": "[DRAFT] Context: Arjun's recommendation",
            "email_body": (
                "Hi Mei,\n\nArjun Krishnan suggested I reach out — he and I worked on the "
                "data platform redesign at his Series B in February, and he said your team "
                "is at a similar stage with the same Snowflake plus dbt plus Airflow "
                "combination he was working through.\n\nIf the equivalent rebuild is on your "
                "roadmap, I would be glad to share what we learned in his project, including "
                "the two architectural decisions that did not work and that Arjun would tell "
                "you about openly. Happy to send a one-page write-up or do 15 minutes — "
                "your call.\n\nIf this is not on your roadmap, no follow-up.\n\nBest,\nYabi"
            ),
        },
        "ground_truth": {
            "expected_behaviour": "Names the mutual connection and specific project context. "
                "References specific tech stack (Snowflake, dbt, Airflow). Names decisions "
                "that did not work — earns trust through honesty. Two low-friction options.",
            "passing_conditions": {
                "signal_fidelity": "pass — specific stack and intro source named",
                "tone_compliance": "pass — no banned phrases",
                "segment_gate": "pass — ai_maturity_score=2, no Seg4 pitch",
                "confidence_hedging": "n/a — icp_confidence=high",
                "format_compliance": "pass — warm reply ≤200 words, [DRAFT] present",
            },
        },
    },

    {   # GOOD #12 — Micro-touch post-call nurture
        "task_id": "TB-ADV-017",
        "category": "good_example_post_call_nurture",
        "partition": "dev",
        "input": {
            "company": "LoyaltyCore",
            "domain": "loyaltycore.io",
            "warm": True,
            "contact_name": "Kevin Marsh",
            "contact_role": "VP Engineering",
            "enrichment_brief": {
                "open_roles_estimate": 4,
                "engineering_velocity": "medium",
                "layoff_event": False,
                "icp_confidence": "medium",
                "ai_maturity_score": 2,
                "low_peer_count": True,
                "tech_stack": ["dbt", "Snowflake"],
                "prior_call_date": "2026-04-28",
                "follow_up_date": "2026-05-07",
            },
        },
        "candidate_output": {
            "email_subject": "[DRAFT] Quick thought after our call",
            "email_body": (
                "Hi Kevin,\n\nAfter we spoke yesterday I went back and looked — three of "
                "the loyalty platforms you mentioned as competitors are now publicly using "
                "the same dbt-plus-Snowflake stack you are evaluating. Worth knowing as "
                "you scope the build.\n\nNo reply needed. I will follow up after your "
                "internal review next Thursday as agreed.\n\nBest,\nYabi"
            ),
        },
        "ground_truth": {
            "expected_behaviour": "Two-line micro-touch. Adds one specific data point. "
                "'No reply needed.' References agreed follow-up date. Body ~47 words.",
            "passing_conditions": {
                "signal_fidelity": "pass — competitor stack data cited",
                "tone_compliance": "pass — no banned phrases",
                "segment_gate": "pass — ai_maturity_score=2, no Seg4 pitch",
                "confidence_hedging": "pass — hedging present (low_peer_count=True)",
                "format_compliance": "pass — warm ≤200 words, [DRAFT] present",
            },
        },
    },

    # ── BAD EXAMPLES ───────────────────────────────────────────────────────

    {   # BAD #1 — Wall of self-promotion, no signal
        "task_id": "TB-ADV-018",
        "category": "FC3_overclaim",
        "partition": "train",
        "input": {
            "company": "Luminary Software",
            "domain": "luminarysoftware.com",
            "warm": False,
            "contact_name": "Maya Chen",
            "contact_role": "VP of Engineering",
            "enrichment_brief": {
                "open_roles_estimate": 7,
                "engineering_velocity": "high",
                "layoff_event": False,
                "icp_confidence": "high",
                "ai_maturity_score": 1,
                "low_peer_count": False,
            },
        },
        "candidate_output": {
            "email_subject": "Tenacious — World-Class Engineering Talent",
            "email_body": (
                "Dear Maya,\n\nTenacious Intelligence Corporation is a world-class engineering "
                "outsourcing firm with over 200 senior engineers across Python, Go, data, ML, "
                "and infrastructure. We have been operating since 2019 and have served clients "
                "across North America and Europe. Our top talent is graduated from elite programs "
                "and our delivery model is the gold standard in the industry.\n\nWe offer junior, "
                "mid, senior, and architect-level engineers, fractional CTO services, project "
                "consulting on AI systems, data platforms, and specialized infrastructure, "
                "training engagements, and strategic AI workshops. Our pricing is highly "
                "competitive and we offer flexible engagement models.\n\nI would love to "
                "schedule a 45-minute discovery call to learn about your business and goals.\n\n"
                "Best regards,\nYabi"
            ),
        },
        "ground_truth": {
            "expected_behaviour": "FAIL. 'World-class', 'top talent', 'gold standard' are "
                "banned phrases. Body >120 words. No [DRAFT] tag. No signal from brief cited. "
                "80% of body is self-promotion. Multiple asks stacked.",
            "passing_conditions": {
                "signal_fidelity": "FAIL — no signals from brief referenced",
                "tone_compliance": "FAIL — banned: world-class, top talent",
                "segment_gate": "pass — no AI pitch keyword",
                "confidence_hedging": "n/a",
                "format_compliance": "FAIL — missing [DRAFT], body >120 words",
            },
        },
    },

    {   # BAD #2 — Asserts on weak signal
        "task_id": "TB-ADV-019",
        "category": "FC3_overclaim",
        "partition": "train",
        "input": {
            "company": "DataBridge Corp",
            "domain": "databridgecorp.com",
            "warm": False,
            "contact_name": "Tom Whitfield",
            "contact_role": "Head of Engineering",
            "enrichment_brief": {
                "open_roles_estimate": 2,
                "engineering_velocity": "low",
                "layoff_event": False,
                "icp_confidence": "low",
                "ai_maturity_score": 1,
                "low_peer_count": True,
            },
        },
        "candidate_output": {
            "email_subject": "[DRAFT] Quick chat: your aggressive hiring",
            "email_body": (
                "Hi Tom,\n\nI see you are scaling aggressively — your engineering team is "
                "clearly growing fast and you must be feeling the pain of recruiting velocity "
                "right now. Companies in your stage always hit a wall around month four after "
                "a Series A.\n\nWe solve this exact problem. Tenacious places top talent in "
                "48 hours and we will skyrocket your delivery throughput.\n\nQuick question "
                "— do you have 15 minutes this week?\n\nBest,\nYabi"
            ),
        },
        "ground_truth": {
            "expected_behaviour": "FAIL. 'Scaling aggressively' asserted on 2 open roles (low "
                "signal). 'Top talent', 'skyrocket', 'Quick question', 'Quick chat' are banned. "
                "icp_confidence=low requires hedging — none present.",
            "passing_conditions": {
                "signal_fidelity": "FAIL — scaling aggressively on 2 open roles (low signal)",
                "tone_compliance": "FAIL — banned: scaling aggressively, top talent, skyrocket, quick chat, quick question",
                "segment_gate": "pass — no AI pitch",
                "confidence_hedging": "FAIL — icp_confidence=low, no hedging",
                "format_compliance": "pass — [DRAFT] present, body ~72 words",
            },
        },
    },

    {   # BAD #3 — Bench word + overcommitment
        "task_id": "TB-ADV-020",
        "category": "FC7_bench_capacity",
        "partition": "train",
        "input": {
            "company": "ScaleForce",
            "domain": "scaleforce.io",
            "warm": True,
            "contact_name": "Will Hartman",
            "contact_role": "Head of Engineering",
            "enrichment_brief": {
                "open_roles_estimate": 15,
                "engineering_velocity": "high",
                "layoff_event": False,
                "icp_confidence": "high",
                "ai_maturity_score": 1,
                "low_peer_count": False,
                "bench_available_go": 4,
            },
        },
        "candidate_output": {
            "email_subject": "[DRAFT] Re: 12 senior Go engineers in two weeks",
            "email_body": (
                "Hi Will,\n\nAbsolutely, we can deliver 12 senior Go engineers in two weeks. "
                "Our bench is deep across all stacks and we move fast.\n\nI will have our team "
                "kick off scoping immediately. Expect contracts by Wednesday and engineers in "
                "your Slack by next Friday.\n\nBest,\nYabi"
            ),
        },
        "ground_truth": {
            "expected_behaviour": "FAIL. Uses the word 'bench' to a prospect (Professional "
                "violation). Commits 12 engineers when bench_available_go=4 (unsupported). "
                "No scope, no pricing, no delivery-lead handoff.",
            "passing_conditions": {
                "signal_fidelity": "FAIL — commits 12 engineers, only 4 available",
                "tone_compliance": "FAIL — 'bench' used as standalone word to prospect",
                "segment_gate": "pass",
                "confidence_hedging": "n/a",
                "format_compliance": "pass — [DRAFT] present, body ~55 words",
            },
        },
    },

    {   # BAD #4 — Condescending competitor gap framing
        "task_id": "TB-ADV-021",
        "category": "FC3_overclaim",
        "partition": "train",
        "input": {
            "company": "LoyaltyLabs",
            "domain": "loyaltylabs.io",
            "warm": False,
            "contact_name": "Felix Auer",
            "contact_role": "VP Engineering",
            "enrichment_brief": {
                "open_roles_estimate": 4,
                "engineering_velocity": "medium",
                "layoff_event": False,
                "icp_confidence": "high",
                "ai_maturity_score": 2,
                "low_peer_count": False,
                "peer_mlops_openings": 3,
            },
        },
        "candidate_output": {
            "email_subject": "[DRAFT] Your AI maturity is behind the curve",
            "email_body": (
                "Hi Felix,\n\nI will be direct: your AI maturity score is a 1, while your top "
                "competitors are a 3. You are falling behind in a market where AI is no longer "
                "optional, and your leadership has not yet made the strategic moves that the "
                "loyalty-platform sector demands in 2026.\n\nTenacious can stand up your missing "
                "MLOps function and close the gap before your next board meeting. Our agentic "
                "systems and ML platform engineers are world-class.\n\nLet's get on a call this "
                "week to discuss how we can help you catch up.\n\nBest,\nYabi"
            ),
        },
        "ground_truth": {
            "expected_behaviour": "FAIL. 'World-class' banned. Subject condescending ('behind "
                "the curve'). Body frames gap as prospect failure ('falling behind', 'has not "
                "yet made strategic moves', 'catch up') — Non-condescending marker violation.",
            "passing_conditions": {
                "signal_fidelity": "pass — ai_maturity=2, signals are present",
                "tone_compliance": "FAIL — banned: world-class",
                "segment_gate": "pass — ai_maturity_score=2 permits pitch",
                "confidence_hedging": "n/a",
                "format_compliance": "pass — [DRAFT] present, body ~102 words",
            },
        },
    },

    {   # BAD #5 — Aggressive follow-up
        "task_id": "TB-ADV-022",
        "category": "tone_compliance",
        "partition": "train",
        "input": {
            "company": "Seedling AI",
            "domain": "seedlingai.com",
            "warm": False,
            "contact_name": "Ana Ferreira",
            "contact_role": "Founder & CTO",
            "enrichment_brief": {
                "open_roles_estimate": 3,
                "engineering_velocity": "medium",
                "layoff_event": False,
                "icp_confidence": "medium",
                "ai_maturity_score": 1,
                "low_peer_count": True,
                "prior_contact": True,
                "prior_emails_sent": 3,
            },
        },
        "candidate_output": {
            "email_subject": "[DRAFT] Per my last three emails",
            "email_body": (
                "Hi Ana,\n\nI have sent you three emails over the last two weeks and have "
                "not heard back. I have to assume you are not interested in growing your "
                "engineering capacity, which is fine — but I would appreciate a one-line "
                "reply to confirm so I can take you off the list.\n\nIf I do not hear back "
                "by Friday, I will assume the answer is no.\n\nBest,\nYabi"
            ),
        },
        "ground_truth": {
            "expected_behaviour": "FAIL. 'Per my last' banned. Assumes intent on prospect's "
                "behalf. Passive-aggressive. No new content. Correct pattern: re-engage "
                "with new signal (GOOD #8).",
            "passing_conditions": {
                "signal_fidelity": "pass — no growth claims",
                "tone_compliance": "FAIL — banned: per my last",
                "segment_gate": "pass",
                "confidence_hedging": "FAIL — icp_confidence=medium, low_peer_count=True, no hedging",
                "format_compliance": "pass — [DRAFT] present, body ~76 words",
            },
        },
    },

    {   # BAD #6 — Generic template, unfilled tokens
        "task_id": "TB-ADV-023",
        "category": "FC1_hallucination",
        "partition": "train",
        "input": {
            "company": "DataBridge Corp",
            "domain": "databridgecorp.com",
            "warm": False,
            "contact_name": "Tom Whitfield",
            "contact_role": "Head of Engineering",
            "enrichment_brief": {
                "open_roles_estimate": 2,
                "engineering_velocity": "low",
                "layoff_event": False,
                "icp_confidence": "low",
                "ai_maturity_score": 1,
                "low_peer_count": True,
            },
        },
        "candidate_output": {
            "email_subject": "Hey [First Name], scaling your engineering team?",
            "email_body": (
                "Hey [First Name],\n\nI hope this email finds you well. I am reaching out "
                "because I think Tenacious can help [Company] with all of your engineering "
                "and AI needs in 2026.\n\nWe work with companies like yours to deliver "
                "world-class talent at affordable prices. Our team has experience across many "
                "industries and stacks, and we can help you scale, restructure, or build new "
                "capabilities depending on what you need.\n\nWould you be open to a quick "
                "chat next week to explore how we can synergize and add value to your "
                "ecosystem?\n\nBest,\nYabi"
            ),
        },
        "ground_truth": {
            "expected_behaviour": "FAIL. Unfilled template tokens [First Name] and [Company]. "
                "'I hope this email finds you well', 'world-class', 'quick chat', 'synergize', "
                "'ecosystem' are all banned. No signal cited. No [DRAFT] tag. "
                "icp_confidence=low requires hedging — absent.",
            "passing_conditions": {
                "signal_fidelity": "FAIL — no signal cited; generic claims",
                "tone_compliance": "FAIL — banned: world-class, synergize, ecosystem, quick chat, i hope this email finds you well",
                "segment_gate": "pass — no Seg4 keywords",
                "confidence_hedging": "FAIL — icp_confidence=low, no hedging",
                "format_compliance": "FAIL — missing [DRAFT] tag",
            },
        },
    },

    {   # BAD #7 — Fake urgency / fabricated discount
        "task_id": "TB-ADV-024",
        "category": "FC1_hallucination",
        "partition": "train",
        "input": {
            "company": "LoyaltyCore",
            "domain": "loyaltycore.io",
            "warm": False,
            "contact_name": "Kevin Marsh",
            "contact_role": "VP Engineering",
            "enrichment_brief": {
                "open_roles_estimate": 4,
                "engineering_velocity": "medium",
                "layoff_event": False,
                "icp_confidence": "high",
                "ai_maturity_score": 2,
                "low_peer_count": False,
            },
        },
        "candidate_output": {
            "email_subject": "[DRAFT] URGENT: Last open slot for Q1 — 30% off if you sign",
            "email_body": (
                "Hi Kevin,\n\nTenacious has one remaining slot in our Q1 cohort for managed "
                "engineering teams. Because of strong demand, this slot will not be available "
                "after Friday.\n\nIf you sign a contract by end of day Friday, I am authorized "
                "to offer 30% off the first three months. After that, the slot goes to the "
                "next company on the waitlist.\n\nDo not miss out on this — book a call here: "
                "gettenacious.com/yabi.\n\nBest,\nYabi"
            ),
        },
        "ground_truth": {
            "expected_behaviour": "FAIL. Fake scarcity ('one remaining slot', 'waitlist'). "
                "Fabricated 30% discount (not in pricing_sheet.md). 'Don't miss out' banned. "
                "Fake deadline with no real consequence.",
            "passing_conditions": {
                "signal_fidelity": "FAIL — fabricated scarcity claims",
                "tone_compliance": "FAIL — banned: don't miss out",
                "segment_gate": "pass",
                "confidence_hedging": "n/a",
                "format_compliance": "pass — [DRAFT] present, body ~84 words",
            },
        },
    },

    {   # BAD #8 — Wrong segment (Seg4 pitch to AI maturity 0)
        "task_id": "TB-ADV-025",
        "category": "FC2_seg4_bypass",
        "partition": "train",
        "input": {
            "company": "Axiom Backend",
            "domain": "axiombackend.com",
            "warm": False,
            "contact_name": "Sophia Larsen",
            "contact_role": "Founder & CTO",
            "enrichment_brief": {
                "funding_round": "Series A",
                "funding_amount_m": 9,
                "funding_date": "2026-03-01",
                "open_roles_estimate": 0,
                "engineering_velocity": "low",
                "layoff_event": False,
                "icp_confidence": "high",
                "ai_maturity_score": 0,
                "low_peer_count": False,
                "team_size": 10,
            },
        },
        "candidate_output": {
            "email_subject": "[DRAFT] Question: your agentic systems roadmap",
            "email_body": (
                "Hi Sophia,\n\nI am curious how you are thinking about your agentic-systems "
                "roadmap for 2026. Most peer companies in your stage are now scoping "
                "LLM-orchestrated workflows and dedicated MLOps functions to support "
                "production agent deployments.\n\nWe staff specialized capability-gap squads "
                "— agentic systems, ML platform, data contracts — typically 3 to 4 months. "
                "Starter scope from $XX,XXX. We have done this for several Series A and B "
                "SaaS companies in the last year.\n\nWant to set up a 30-minute scoping "
                "conversation?\n\nBest,\nYabi"
            ),
        },
        "ground_truth": {
            "expected_behaviour": "FAIL. Pitches Seg4 AI capability gap to ai_maturity_score=0. "
                "Correct framing: GOOD #10 (Seg1 'stand up first AI function'). "
                "segment_gate must catch LLM/agentic/MLOps keywords at maturity 0.",
            "passing_conditions": {
                "signal_fidelity": "pass — no unsupported growth claims",
                "tone_compliance": "pass — no banned phrases",
                "segment_gate": "FAIL — ai_maturity_score=0, pitches LLM/agentic/MLOps (Seg4)",
                "confidence_hedging": "n/a",
                "format_compliance": "pass — [DRAFT] present, body ~96 words",
            },
        },
    },

    {   # BAD #9 — Cold PDF attachment
        "task_id": "TB-ADV-026",
        "category": "tone_compliance",
        "partition": "dev",
        "input": {
            "company": "VerticalSaaS Health",
            "domain": "verticalsaashealth.com",
            "warm": False,
            "contact_name": "Marcus Webb",
            "contact_role": "VP Engineering",
            "enrichment_brief": {
                "open_roles_estimate": 3,
                "engineering_velocity": "medium",
                "layoff_event": False,
                "icp_confidence": "medium",
                "ai_maturity_score": 1,
                "low_peer_count": False,
            },
        },
        "candidate_output": {
            "email_subject": "[DRAFT] Tenacious capabilities deck — review pages 8 and 12",
            "email_body": (
                "Hi Marcus,\n\nPlease find attached our 38-page capabilities deck.\n\nPages 8 "
                "and 12 are the most relevant to your sub-sector. Let me know your thoughts "
                "and we can schedule a call to discuss our partnership opportunity.\n\nLooking "
                "forward to your reply.\n\nBest,\nYabi\n\n"
                "[ATTACHMENT: tenacious_capabilities_v7.pdf — 12.4 MB]"
            ),
        },
        "ground_truth": {
            "expected_behaviour": "FAIL. Cold PDF attachment is explicitly banned in formatting "
                "rules. No signal grounded. 'Partnership opportunity' is vague jargon. "
                "Agent outsources the value to the PDF.",
            "passing_conditions": {
                "signal_fidelity": "FAIL — no signals cited; generic capabilities pitch",
                "tone_compliance": "pass — no exact banned phrases hit",
                "segment_gate": "pass",
                "confidence_hedging": "pass — icp_confidence=medium, no hedging required",
                "format_compliance": "pass — [DRAFT] present, body ~55 words",
            },
        },
    },

    {   # BAD #10 — Multiple stacked asks
        "task_id": "TB-ADV-027",
        "category": "tone_compliance",
        "partition": "dev",
        "input": {
            "company": "Meridian Analytics",
            "domain": "meridiananalytics.io",
            "warm": False,
            "contact_name": "Daniel Park",
            "contact_role": "CTO",
            "enrichment_brief": {
                "open_roles_estimate": 2,
                "engineering_velocity": "low",
                "layoff_event": True,
                "layoff_pct": 12,
                "layoff_date": "2026-03-15",
                "icp_confidence": "high",
                "ai_maturity_score": 2,
                "low_peer_count": False,
            },
        },
        "candidate_output": {
            "email_subject": "[DRAFT] A few questions and ideas for Meridian",
            "email_body": (
                "Hi Daniel,\n\nI had a few thoughts I wanted to share. First, I would love "
                "to understand your current engineering structure and which stacks you are "
                "using. Second, I have an introduction to a peer of yours at a similar "
                "mid-market platform. Third, we have a new training program for engineering "
                "leaders that might be relevant. Fourth, I noticed your AI maturity is around "
                "a 2 — happy to walk through how to move it to a 3.\n\nCould we set up a "
                "60-minute call next week to discuss all four of these? I will also send our "
                "pricing sheet, our case studies, and our training brochure separately.\n\n"
                "Best,\nYabi"
            ),
        },
        "ground_truth": {
            "expected_behaviour": "FAIL. Four asks stacked in one message (violates one-ask rule). "
                "60-minute first call too long. Three additional unsolicited emails promised. "
                "Condescending: 'move your AI maturity from 2 to 3' frames it as Tenacious's "
                "problem to solve.",
            "passing_conditions": {
                "signal_fidelity": "FAIL — growth claims on layoff context (open_roles=2, layoff=True)",
                "tone_compliance": "pass — no exact banned phrases",
                "segment_gate": "pass — ai_maturity_score=2",
                "confidence_hedging": "n/a",
                "format_compliance": "pass — [DRAFT] present, body ~121 words",
            },
        },
    },

    {   # BAD #11 — Pricing fabrication TCV
        "task_id": "TB-ADV-028",
        "category": "FC1_hallucination",
        "partition": "dev",
        "input": {
            "company": "Camila's Startup",
            "domain": "camila-startup.io",
            "warm": True,
            "contact_name": "Camila Reyes",
            "contact_role": "CTO",
            "enrichment_brief": {
                "open_roles_estimate": 5,
                "engineering_velocity": "high",
                "layoff_event": False,
                "icp_confidence": "high",
                "ai_maturity_score": 2,
                "low_peer_count": False,
            },
        },
        "candidate_output": {
            "email_subject": "[DRAFT] Quote: $1.2M for the 12-month engagement",
            "email_body": (
                "Hi Camila,\n\nThanks for the call yesterday. As discussed, our quote for the "
                "12-month engagement covering 6 engineers, a delivery lead, and a fractional "
                "architect is $1,200,000 total, payable in monthly installments of $100,000.\n\n"
                "I have attached the contract. Please sign and return by Friday so we can begin "
                "onboarding on the 1st.\n\nBest,\nYabi"
            ),
        },
        "ground_truth": {
            "expected_behaviour": "FAIL. Total contract value invented (multi-phase TCV must route "
                "to human). Contract attached — outside agent scope. Hard signing deadline. "
                "Correct pattern: GOOD #7 (route to delivery lead for specific quote).",
            "passing_conditions": {
                "signal_fidelity": "pass — warm context, no fabricated signals",
                "tone_compliance": "pass — no exact banned phrases",
                "segment_gate": "pass",
                "confidence_hedging": "n/a",
                "format_compliance": "pass — warm ≤200 words, [DRAFT] present",
            },
        },
    },

    {   # BAD #12 — Signal fabrication (wrong funding stage)
        "task_id": "TB-ADV-029",
        "category": "FC1_hallucination",
        "partition": "dev",
        "input": {
            "company": "Helix Systems",
            "domain": "helixsystems.com",
            "warm": False,
            "contact_name": "Priya Nair",
            "contact_role": "CTO",
            "enrichment_brief": {
                "funding_round": "Series A",
                "funding_amount_m": 9,
                "funding_date": "2026-03-01",
                "open_roles_estimate": 5,
                "engineering_velocity": "medium",
                "layoff_event": False,
                "icp_confidence": "high",
                "ai_maturity_score": 1,
                "low_peer_count": False,
            },
        },
        "candidate_output": {
            "email_subject": "[DRAFT] Re: your $40M Series C",
            "email_body": (
                "Hi Priya,\n\nCongratulations on closing your $40M Series C last month — "
                "exciting moment for the team. With that level of capital, scaling engineering "
                "aggressively is the obvious next move.\n\nWe can plug a 15-engineer team into "
                "your stack within 30 days at our standard rates. Junior engineers from "
                "$X,XXX/month.\n\nWant to set up a 15-minute call to discuss?\n\nBest,\nYabi"
            ),
        },
        "ground_truth": {
            "expected_behaviour": "FAIL. Fabricated Series C $40M (brief shows Series A $9M). "
                "'Scaling aggressively' banned. Bench commitment of 15 engineers unsupported. "
                "If Priya forwards this, every claim is verifiably wrong — highest-cost failure.",
            "passing_conditions": {
                "signal_fidelity": "FAIL — 'scaling aggressively' on medium signal",
                "tone_compliance": "FAIL — banned: scaling aggressively",
                "segment_gate": "pass",
                "confidence_hedging": "n/a",
                "format_compliance": "pass — [DRAFT] present, body ~66 words",
            },
        },
    },
]


# ---------------------------------------------------------------------------
# Build full task objects and append to partition files
# ---------------------------------------------------------------------------

def make_task(raw: dict) -> dict:
    return {
        "task_id":     raw["task_id"],
        "source_mode": "hand_authored",
        "category":    raw["category"],
        "input": {
            **raw["input"],
            "system_prompt_excerpt": SYSTEM_PROMPT_EXCERPT,
        },
        "candidate_output": raw["candidate_output"],
        "ground_truth":     raw["ground_truth"],
        "rubric": {
            "signal_fidelity":    {"weight": 0.30, "description": "No unsupported growth/funding claims"},
            "tone_compliance":    {"weight": 0.20, "description": "Zero banned phrases; no 'bench' to prospect"},
            "segment_gate":       {"weight": 0.20, "description": "No Seg4 AI pitch when ai_maturity_score < 2"},
            "confidence_hedging": {"weight": 0.15, "description": "Hedging when icp_confidence=low or low_peer_count=True"},
            "format_compliance":  {"weight": 0.15, "description": "[DRAFT] tag, subject ≤60 chars, body ≤120/200 words"},
        },
        "score": None,
        "dimension_scores": None,
    }


def main():
    train_tasks = [t for t in TASKS_RAW if t["partition"] == "train"]
    dev_tasks   = [t for t in TASKS_RAW if t["partition"] == "dev"]

    print(f"Adding {len(train_tasks)} tasks to train, {len(dev_tasks)} to dev")

    for path, tasks in [(TRAIN_FILE, train_tasks), (DEV_FILE, dev_tasks)]:
        existing = path.read_text(encoding="utf-8").rstrip("\n")
        new_lines = "\n".join(
            json.dumps(make_task(t), ensure_ascii=False) for t in tasks
        )
        path.write_text(existing + "\n" + new_lines + "\n", encoding="utf-8")
        print(f"  -> {path}: +{len(tasks)} tasks")


if __name__ == "__main__":
    main()
