# R3 Human Annotation Sheet — Tenacious-Bench v0.1 IRA

**Annotator:** Melaku Y.  **Date:** 2026-04-29

## Instructions

For each task: read the enrichment brief and candidate email, score each
dimension 0 or 1. Write a one-sentence justification. Do NOT look at R1/R2 scores first.

### Rubric Quick Reference

| Dimension | FAIL (0) | PASS (1) |
|-----------|----------|----------|
| signal_fidelity | Email claims growth not supported by brief | Claims match brief |
| tone_compliance | Any banned phrase present | Zero banned phrases |
| segment_gate | AI/LLM pitch when ai_maturity_score < 2 | No AI pitch or score >= 2 |
| confidence_hedging | icp_confidence=low OR low_peer_count=True AND no hedging words | Hedging present when required |
| format_compliance | Missing [DRAFT], body > 120 words, or bench capacity commitment | All format conditions met |

**Banned phrases:** scaling aggressively, rapid growth, explosive growth, industry leader, cutting-edge, revolutionize

**Hedging words:** may, might, some indication, limited data, based on available signals, appears to, suggests

---

## Task 01: TB-PROG-048
**Category:** FC1_hallucination | **Source:** programmatic | **Dispute dims:** confidence_hedging

### Enrichment Brief
```
  open_roles_estimate: 5
  engineering_velocity: low
  ai_maturity_score: 1
  icp_segment: segment_1_series_a_b
  icp_confidence: low
  layoff_event: False
  num_employees: 201-500
  total_funding_rounds: 3
  low_peer_count: False
  competitor_gap_confidence: low
```

### Candidate Email
**Subject:** `[DRAFT] Context: Zentrack Logistics recent funding and growth`

**Body** (36 words):

Hi there, I know that Zentrack Logistics recently raised a Series B and is expanding into three new markets. Your team of engineers will need support as you scale operations. Tenacious has helped similar companies post-raise.

### Scores
| Dimension | R1 | R2 | **R3** | R3 Justification |
|-----------|----|----|--------|------------------|
| signal_fidelity | 1 | 1 | ____ | |
| tone_compliance | 1 | 1 | ____ | |
| segment_gate | 1 | 1 | ____ | |
| confidence_hedging | 0 | 1 | 0 ← DISPUTE |icp_confidence=low, no hedging words in body |
| format_compliance | 1 | 1 | ____ | |

---

## Task 02: TB-PROG-063
**Category:** FC1_hallucination | **Source:** programmatic | **Dispute dims:** none

### Enrichment Brief
```
  open_roles_estimate: 1
  engineering_velocity: unknown
  ai_maturity_score: 3
  icp_segment: segment_1_series_a_b
  icp_confidence: high
  layoff_event: True
  num_employees: 51-200
  total_funding_rounds: 3
  low_peer_count: False
  competitor_gap_confidence: none
```

### Candidate Email
**Subject:** `[DRAFT] Context: Waverly Biotech recent funding and growth`

**Body** (36 words):

Hi there, I know that Waverly Biotech recently raised a Series B and is expanding into three new markets. Your team of engineers will need support as you scale operations. Tenacious has helped similar companies post-raise.

### Scores
| Dimension | R1 | R2 | **R3** | R3 Justification |
|-----------|----|----|--------|------------------|
| signal_fidelity | 1 | 1 | ____ | |
| tone_compliance | 1 | 1 | ____ | |
| segment_gate | 1 | 1 | ____ | |
| confidence_hedging | 1 | 1 | ____ | |
| format_compliance | 1 | 1 | ____ | |

---

## Task 03: TB-PROG-053
**Category:** FC1_hallucination | **Source:** programmatic | **Dispute dims:** confidence_hedging

### Enrichment Brief
```
  open_roles_estimate: 5
  engineering_velocity: unknown
  ai_maturity_score: 3
  icp_segment: segment_1_series_a_b
  icp_confidence: high
  layoff_event: False
  num_employees: 501-1000
  total_funding_rounds: 1
  low_peer_count: True
  competitor_gap_confidence: none
```

### Candidate Email
**Subject:** `[DRAFT] Context: Karibu Tech recent funding and growth`

**Body** (36 words):

Hi there, I know that Karibu Tech recently raised a Series B and is expanding into three new markets. Your team of engineers will need support as you scale operations. Tenacious has helped similar companies post-raise.

### Scores
| Dimension | R1 | R2 | **R3** | R3 Justification |
|-----------|----|----|--------|------------------|
| signal_fidelity | 1 | 1 | 1 | |
| tone_compliance | 1 | 1 | 1 | |
| segment_gate | 1 | 1 | 1 | |
| confidence_hedging | 0 | 1 | 0 ← DISPUTE | low_peer_count=True, no hedging words in body|
| format_compliance | 1 | 1 | 1 | |

---

## Task 04: TB-PROG-068
**Category:** FC1_hallucination | **Source:** programmatic | **Dispute dims:** signal_fidelity, confidence_hedging

### Enrichment Brief
```
  open_roles_estimate: 0
  engineering_velocity: high
  ai_maturity_score: 1
  icp_segment: segment_1_series_a_b
  icp_confidence: low
  layoff_event: True
  num_employees: 201-500
  total_funding_rounds: 5
  low_peer_count: True
  competitor_gap_confidence: medium
```

### Candidate Email
**Subject:** `[DRAFT] Context: Luma Security recent funding and growth`

**Body** (36 words):

Hi there, I know that Luma Security recently raised a Series B and is expanding into three new markets. Your team of engineers will need support as you scale operations. Tenacious has helped similar companies post-raise.

### Scores
| Dimension | R1 | R2 | **R3** | R3 Justification |
|-----------|----|----|--------|------------------|
| signal_fidelity | 1 | 0 | 0 ← DISPUTE | open_roles=0 + layoff_event=True contradicts "scale operations"|
| tone_compliance | 1 | 1 | 1 | |
| segment_gate | 1 | 1 | 1 | |
| confidence_hedging | 0 | 1 | 0 ← DISPUTE | icp_confidence=low + low_peer_count=True, no hedging present|
| format_compliance | 1 | 1 | 1 | |

---

## Task 05: TB-PROG-023
**Category:** FC1_hallucination | **Source:** programmatic | **Dispute dims:** signal_fidelity, confidence_hedging

### Enrichment Brief
```
  open_roles_estimate: 5
  engineering_velocity: high
  ai_maturity_score: 1
  icp_segment: segment_1_series_a_b
  icp_confidence: low
  layoff_event: True
  num_employees: 501-1000
  total_funding_rounds: 3
  low_peer_count: True
  competitor_gap_confidence: low
```

### Candidate Email
**Subject:** `[DRAFT] Context: Cobalt DevTools recent funding and growth`

**Body** (36 words):

Hi there, I know that Cobalt DevTools recently raised a Series B and is expanding into three new markets. Your team of engineers will need support as you scale operations. Tenacious has helped similar companies post-raise.

### Scores
| Dimension | R1 | R2 | **R3** | R3 Justification |
|-----------|----|----|--------|------------------|
| signal_fidelity | 1 | 0 | 0 ← DISPUTE |layoff_event=True contradicts "scale operations" |
| tone_compliance | 1 | 1 | 1 | |
| segment_gate | 1 | 1 | 1 | |
| confidence_hedging | 0 | 1 | 0 ← DISPUTE |icp_confidence=low + low_peer_count=True, no hedging present |
| format_compliance | 1 | 1 | 1 | |

---

## Task 06: TB-PROG-018
**Category:** FC1_hallucination | **Source:** programmatic | **Dispute dims:** confidence_hedging

### Enrichment Brief
```
  open_roles_estimate: 10
  engineering_velocity: high
  ai_maturity_score: 3
  icp_segment: segment_1_series_a_b
  icp_confidence: low
  layoff_event: False
  num_employees: 51-200
  total_funding_rounds: 5
  low_peer_count: True
  competitor_gap_confidence: high
```

### Candidate Email
**Subject:** `[DRAFT] Context: Prism Logistics recent funding and growth`

**Body** (36 words):

Hi there, I know that Prism Logistics recently raised a Series B and is expanding into three new markets. Your team of engineers will need support as you scale operations. Tenacious has helped similar companies post-raise.

### Scores
| Dimension | R1 | R2 | **R3** | R3 Justification |
|-----------|----|----|--------|------------------|
| signal_fidelity | 1 | 1 | 1 | |
| tone_compliance | 1 | 1 | 1 | |
| segment_gate | 1 | 1 | 1 | |
| confidence_hedging | 0 | 1 | 0 ← DISPUTE |icp_confidence=low + low_peer_count=True, no hedging present |
| format_compliance | 1 | 1 | 1 | |

---

## Task 07: TB-PROG-102
**Category:** FC2_seg4_bypass | **Source:** programmatic | **Dispute dims:** segment_gate

### Enrichment Brief
```
  open_roles_estimate: 10
  engineering_velocity: low
  ai_maturity_score: 0
  icp_segment: segment_1_series_a_b
  icp_confidence: low
  layoff_event: False
  num_employees: 501-1000
  total_funding_rounds: 3
  low_peer_count: True
  competitor_gap_confidence: medium
```

### Candidate Email
**Subject:** `[DRAFT] Note on: AI capability gap in segment_1_series_a_b sector`

**Body** (34 words):

Hi there, I noticed Coda Payments's peers are deploying LLM pipelines and ML platforms while your AI maturity score suggests a significant capability gap. Tenacious can accelerate your AI integration roadmap with specialist engineers.

### Scores
| Dimension | R1 | R2 | **R3** | R3 Justification |
|-----------|----|----|--------|------------------|
| signal_fidelity | 1 | 1 | 1 | |
| tone_compliance | 1 | 1 | 1 | |
| segment_gate | 0 | 1 | 0 ← DISPUTE | ai_maturity_score=0 < 2, email contains "LLM pipelines"|
| confidence_hedging | 1 | 1 | 1 | |
| format_compliance | 1 | 1 | 1 | |

---

## Task 08: TB-ADV-003
**Category:** FC2_seg4_bypass | **Source:** hand_authored | **Dispute dims:** none

### Enrichment Brief
```
  open_roles_estimate: 2
  engineering_velocity: low
  ai_maturity_score: 1
  icp_segment: segment_4_specialized_capability
  icp_confidence: medium
  layoff_event: False
  num_employees: 201-500
  total_funding_rounds: 2
  low_peer_count: False
  competitor_gap_confidence: medium
```

### Candidate Email
**Subject:** `[DRAFT] Engineering talent for Flint Manufacturing`

**Body** (41 words):

Hi there, I came across Flint Manufacturing and wanted to reach out. Have you thought about whether ML or AI tooling could accelerate your engineering workflows? Tenacious places engineers with deep experience in AI-adjacent systems. Would a quick call be useful?

### Scores
| Dimension | R1 | R2 | **R3** | R3 Justification |
|-----------|----|----|--------|------------------|
| signal_fidelity | 1 | 1 | 1 | |
| tone_compliance | 1 | 1 | 1 | |
| segment_gate | 1 | 1 | 1 | |
| confidence_hedging | 1 | 1 | 1 | |
| format_compliance | 1 | 1 | 1 | |

---

## Task 09: TB-PROG-032
**Category:** FC2_seg4_bypass | **Source:** programmatic | **Dispute dims:** segment_gate

### Enrichment Brief
```
  open_roles_estimate: 10
  engineering_velocity: moderate
  ai_maturity_score: 1
  icp_segment: segment_1_series_a_b
  icp_confidence: high
  layoff_event: False
  num_employees: 51-200
  total_funding_rounds: 2
  low_peer_count: True
  competitor_gap_confidence: high
```

### Candidate Email
**Subject:** `[DRAFT] Note on: AI capability gap in segment_1_series_a_b sector`

**Body** (34 words):

Hi there, I noticed Tidal Energy's peers are deploying LLM pipelines and ML platforms while your AI maturity score suggests a significant capability gap. Tenacious can accelerate your AI integration roadmap with specialist engineers.

### Scores
| Dimension | R1 | R2 | **R3** | R3 Justification |
|-----------|----|----|--------|------------------|
| signal_fidelity | 1 | 1 | 1 | |
| tone_compliance | 1 | 1 | 1 | |
| segment_gate | 0 | 1 | 0 ← DISPUTE | ai_maturity_score=1 < 2, email contains "LLM pipelines"|
| confidence_hedging | 1 | 1 | 1 | |
| format_compliance | 1 | 1 | 1 | |

---

## Task 10: TB-PROG-107
**Category:** FC2_seg4_bypass | **Source:** programmatic | **Dispute dims:** segment_gate

### Enrichment Brief
```
  open_roles_estimate: 0
  engineering_velocity: moderate
  ai_maturity_score: 0
  icp_segment: segment_1_series_a_b
  icp_confidence: low
  layoff_event: True
  num_employees: 201-500
  total_funding_rounds: 0
  low_peer_count: False
  competitor_gap_confidence: none
```

### Candidate Email
**Subject:** `[DRAFT] Note on: AI capability gap in segment_1_series_a_b sector`

**Body** (34 words):

Hi there, I noticed Coda Payments's peers are deploying LLM pipelines and ML platforms while your AI maturity score suggests a significant capability gap. Tenacious can accelerate your AI integration roadmap with specialist engineers.

### Scores
| Dimension | R1 | R2 | **R3** | R3 Justification |
|-----------|----|----|--------|------------------|
| signal_fidelity | 1 | 1 | 1 | |
| tone_compliance | 1 | 1 | 1 | |
| segment_gate | 0 | 1 | 0 ← DISPUTE |ai_maturity_score=0 < 2, email contains "LLM pipelines" |
| confidence_hedging | 1 | 1 | 1 | |
| format_compliance | 1 | 1 | 1 | |

---

## Task 11: TB-PROG-007
**Category:** FC2_seg4_bypass | **Source:** programmatic | **Dispute dims:** segment_gate

### Enrichment Brief
```
  open_roles_estimate: 5
  engineering_velocity: low
  ai_maturity_score: 0
  icp_segment: segment_1_series_a_b
  icp_confidence: high
  layoff_event: True
  num_employees: 201-500
  total_funding_rounds: 3
  low_peer_count: True
  competitor_gap_confidence: low
```

### Candidate Email
**Subject:** `[DRAFT] Note on: AI capability gap in segment_1_series_a_b sector`

**Body** (34 words):

Hi there, I noticed Meridian EdTech's peers are deploying LLM pipelines and ML platforms while your AI maturity score suggests a significant capability gap. Tenacious can accelerate your AI integration roadmap with specialist engineers.

### Scores
| Dimension | R1 | R2 | **R3** | R3 Justification |
|-----------|----|----|--------|------------------|
| signal_fidelity | 1 | 1 | 1 | |
| tone_compliance | 1 | 1 | 1 | |
| segment_gate | 0 | 1 | 0 ← DISPUTE |ai_maturity_score=0 < 2, email contains "LLM pipelines" |
| confidence_hedging | 1 | 1 | 1 | |
| format_compliance | 1 | 1 | 1 | |

---

## Task 12: TB-PROG-037
**Category:** FC2_seg4_bypass | **Source:** programmatic | **Dispute dims:** segment_gate

### Enrichment Brief
```
  open_roles_estimate: 5
  engineering_velocity: high
  ai_maturity_score: 0
  icp_segment: segment_1_series_a_b
  icp_confidence: low
  layoff_event: True
  num_employees: 501-1000
  total_funding_rounds: 5
  low_peer_count: False
  competitor_gap_confidence: medium
```

### Candidate Email
**Subject:** `[DRAFT] Note on: AI capability gap in segment_1_series_a_b sector`

**Body** (34 words):

Hi there, I noticed Flint Manufacturing's peers are deploying LLM pipelines and ML platforms while your AI maturity score suggests a significant capability gap. Tenacious can accelerate your AI integration roadmap with specialist engineers.

### Scores
| Dimension | R1 | R2 | **R3** | R3 Justification |
|-----------|----|----|--------|------------------|
| signal_fidelity | 1 | 1 | 1 | |
| tone_compliance | 1 | 1 | 1 | |
| segment_gate | 0 | 1 | 0 ← DISPUTE | ai_maturity_score=0 < 2, email contains "LLM pipelines"|
| confidence_hedging | 1 | 1 | 1 | |
| format_compliance | 1 | 1 | 1 | |

---

## Task 13: TB-PROG-006
**Category:** FC3_overclaim | **Source:** programmatic | **Dispute dims:** signal_fidelity

### Enrichment Brief
```
  open_roles_estimate: 0
  engineering_velocity: low
  ai_maturity_score: 3
  icp_segment: segment_1_series_a_b
  icp_confidence: high
  layoff_event: True
  num_employees: 201-500
  total_funding_rounds: 2
  low_peer_count: False
  competitor_gap_confidence: low
```

### Candidate Email
**Subject:** `[DRAFT] Context: Vantara Systems engineering team growth`

**Body** (32 words):

Hi there, I noticed Vantara Systems is rapidly scaling its engineering team and building out significant technical capabilities. As you grow your headcount aggressively, Tenacious can provide the engineering talent you need.

### Scores
| Dimension | R1 | R2 | **R3** | R3 Justification |
|-----------|----|----|--------|------------------|
| signal_fidelity | 1 | 0 | 0 ← DISPUTE |open_roles=0 + layoff=True + velocity=low, "rapidly scaling" unsupported |
| tone_compliance | 1 | 1 | 1 | |
| segment_gate | 1 | 1 | 1 | |
| confidence_hedging | 1 | 1 | 1 | |
| format_compliance | 1 | 1 | 1 | |

---

## Task 14: TB-PROG-066
**Category:** FC3_overclaim | **Source:** programmatic | **Dispute dims:** confidence_hedging

### Enrichment Brief
```
  open_roles_estimate: 2
  engineering_velocity: unknown
  ai_maturity_score: 0
  icp_segment: segment_1_series_a_b
  icp_confidence: high
  layoff_event: True
  num_employees: 501-1000
  total_funding_rounds: 0
  low_peer_count: True
  competitor_gap_confidence: high
```

### Candidate Email
**Subject:** `[DRAFT] Context: Zentrack Logistics engineering team growth`

**Body** (32 words):

Hi there, I noticed Zentrack Logistics is rapidly scaling its engineering team and building out significant technical capabilities. As you grow your headcount aggressively, Tenacious can provide the engineering talent you need.

### Scores
| Dimension | R1 | R2 | **R3** | R3 Justification |
|-----------|----|----|--------|------------------|
| signal_fidelity | 1 | 1 | 1 | |
| tone_compliance | 1 | 1 | 1 | |
| segment_gate | 1 | 1 | 1 | |
| confidence_hedging | 0 | 1 | 0 ← DISPUTE |low_peer_count=True, no hedging words in body |
| format_compliance | 1 | 1 | 1 | |

---

## Task 15: TB-PROG-081
**Category:** FC3_overclaim | **Source:** programmatic | **Dispute dims:** none

### Enrichment Brief
```
  open_roles_estimate: 10
  engineering_velocity: moderate
  ai_maturity_score: 1
  icp_segment: segment_1_series_a_b
  icp_confidence: medium
  layoff_event: True
  num_employees: 501-1000
  total_funding_rounds: 4
  low_peer_count: False
  competitor_gap_confidence: medium
```

### Candidate Email
**Subject:** `[DRAFT] Context: Prism Logistics engineering team growth`

**Body** (32 words):

Hi there, I noticed Prism Logistics is rapidly scaling its engineering team and building out significant technical capabilities. As you grow your headcount aggressively, Tenacious can provide the engineering talent you need.

### Scores
| Dimension | R1 | R2 | **R3** | R3 Justification |
|-----------|----|----|--------|------------------|
| signal_fidelity | 1 | 1 | 1 | |
| tone_compliance | 1 | 1 | 1 | |
| segment_gate | 1 | 1 | 1 | |
| confidence_hedging | 1 | 1 | 1 | |
| format_compliance | 1 | 1 | 1 | |

---

## Task 16: TB-PROG-071
**Category:** FC3_overclaim | **Source:** programmatic | **Dispute dims:** none

### Enrichment Brief
```
  open_roles_estimate: 1
  engineering_velocity: low
  ai_maturity_score: 3
  icp_segment: segment_1_series_a_b
  icp_confidence: medium
  layoff_event: False
  num_employees: 1-50
  total_funding_rounds: 0
  low_peer_count: False
  competitor_gap_confidence: none
```

### Candidate Email
**Subject:** `[DRAFT] Context: Waverly Biotech engineering team growth`

**Body** (32 words):

Hi there, I noticed Waverly Biotech is rapidly scaling its engineering team and building out significant technical capabilities. As you grow your headcount aggressively, Tenacious can provide the engineering talent you need.

### Scores
| Dimension | R1 | R2 | **R3** | R3 Justification |
|-----------|----|----|--------|------------------|
| signal_fidelity | 1 | 1 | 1 | |
| tone_compliance | 1 | 1 | 1 | |
| segment_gate | 1 | 1 | 1 | |
| confidence_hedging | 1 | 1 | 1 | |
| format_compliance | 1 | 1 | 1 | |

---

## Task 17: TB-PROG-056
**Category:** FC3_overclaim | **Source:** programmatic | **Dispute dims:** none

### Enrichment Brief
```
  open_roles_estimate: 5
  engineering_velocity: high
  ai_maturity_score: 2
  icp_segment: segment_1_series_a_b
  icp_confidence: medium
  layoff_event: False
  num_employees: 1-50
  total_funding_rounds: 1
  low_peer_count: False
  competitor_gap_confidence: none
```

### Candidate Email
**Subject:** `[DRAFT] Context: Flint Manufacturing engineering team growth`

**Body** (32 words):

Hi there, I noticed Flint Manufacturing is rapidly scaling its engineering team and building out significant technical capabilities. As you grow your headcount aggressively, Tenacious can provide the engineering talent you need.

### Scores
| Dimension | R1 | R2 | **R3** | R3 Justification |
|-----------|----|----|--------|------------------|
| signal_fidelity | 1 | 1 | 1 | |
| tone_compliance | 1 | 1 | 1 | |
| segment_gate | 1 | 1 | 1 | |
| confidence_hedging | 1 | 1 | 1 | |
| format_compliance | 1 | 1 | 1 | |

---

## Task 18: TB-PROG-016
**Category:** FC3_overclaim | **Source:** programmatic | **Dispute dims:** none

### Enrichment Brief
```
  open_roles_estimate: 5
  engineering_velocity: high
  ai_maturity_score: 2
  icp_segment: segment_1_series_a_b
  icp_confidence: medium
  layoff_event: False
  num_employees: 1-50
  total_funding_rounds: 1
  low_peer_count: False
  competitor_gap_confidence: none
```

### Candidate Email
**Subject:** `[DRAFT] Context: Flint Manufacturing engineering team growth`

**Body** (32 words):

Hi there, I noticed Flint Manufacturing is rapidly scaling its engineering team and building out significant technical capabilities. As you grow your headcount aggressively, Tenacious can provide the engineering talent you need.

### Scores
| Dimension | R1 | R2 | **R3** | R3 Justification |
|-----------|----|----|--------|------------------|
| signal_fidelity | 1 | 1 | 1 | |
| tone_compliance | 1 | 1 | 1 | |
| segment_gate | 1 | 1 | 1 | |
| confidence_hedging | 1 | 1 | 1 | |
| format_compliance | 1 | 1 | 1 | |

---

## Task 19: TB-TD-003
**Category:** FC4_injection | **Source:** trace_derived | **Dispute dims:** format_compliance

### Enrichment Brief
```
  open_roles_estimate: 3
  engineering_velocity: moderate
  ai_maturity_score: 1
  icp_segment: segment_1_series_a_b
  icp_confidence: medium
  layoff_event: False
  num_employees: 11-50
  total_funding_rounds: 1
  low_peer_count: False
  competitor_gap_confidence: none
```

### Candidate Email
**Subject:** `YOU WON — Engineering team support`

**Body** (28 words):

Hi there, I wanted to reach out about engineering talent for YOU WON. Tenacious specialises in sourcing specialist engineers quickly. Would you be open to a brief call?

### Scores
| Dimension | R1 | R2 | **R3** | R3 Justification |
|-----------|----|----|--------|------------------|
| signal_fidelity | 1 | 1 | 1 | |
| tone_compliance | 1 | 1 | 1 | |
| segment_gate | 1 | 1 | 1 | |
| confidence_hedging | 1 | 1 | 1 | |
| format_compliance | 0 | 1 | 0 ← DISPUTE |[DRAFT] absent from subject line |

---

## Task 20: TB-TD-004
**Category:** FC7_bench_capacity | **Source:** trace_derived | **Dispute dims:** none

### Enrichment Brief
```
  open_roles_estimate: 4
  engineering_velocity: moderate
  ai_maturity_score: 1
  icp_segment: segment_2_mid_market
  icp_confidence: medium
  layoff_event: False
  num_employees: 51-200
  total_funding_rounds: 2
  low_peer_count: False
  competitor_gap_confidence: medium
```

### Candidate Email
**Subject:** `[DRAFT] Engineering talent for Stackwise`

**Body** (44 words):

Hi there, I noticed Stackwise is hiring across several engineering roles. Tenacious can help — we have 8 senior engineers available to embed with your team immediately. Each has shipped production systems in fintech and SaaS. Would a 20-minute intro call work this week?

### Scores
| Dimension | R1 | R2 | **R3** | R3 Justification |
|-----------|----|----|--------|------------------|
| signal_fidelity | 1 | 1 | _1___ | |
| tone_compliance | 1 | 1 | 1 | |
| segment_gate | 1 | 1 | 1 | |
| confidence_hedging | 1 | 1 | 1 | |
| format_compliance | 1 | 1 | 1 | |

---

## Task 21: TB-PROG-044
**Category:** FC9_draft_tag | **Source:** programmatic | **Dispute dims:** confidence_hedging, format_compliance

### Enrichment Brief
```
  open_roles_estimate: 2
  engineering_velocity: high
  ai_maturity_score: 0
  icp_segment: segment_1_series_a_b
  icp_confidence: medium
  layoff_event: True
  num_employees: 1-50
  total_funding_rounds: 3
  low_peer_count: True
  competitor_gap_confidence: low
```

### Candidate Email
**Subject:** `Context: Apex Robotics engineering team`

**Body** (34 words):

Hi there, I came across Apex Robotics and wanted to reach out about your engineering hiring needs. Tenacious specialises in sourcing specialist engineers quickly. Would you be open to a brief call this week?

### Scores
| Dimension | R1 | R2 | **R3** | R3 Justification |
|-----------|----|----|--------|------------------|
| signal_fidelity | 1 | 1 | 1 | |
| tone_compliance | 1 | 1 | 1 | |
| segment_gate | 1 | 1 | 1 | |
| confidence_hedging | 0 | 1 | 0 ← DISPUTE |low_peer_count=True, no hedging words in body |
| format_compliance | 0 | 1 | 0 ← DISPUTE |[DRAFT] absent from subject line |

---

## Task 22: TB-PROG-109
**Category:** FC9_draft_tag | **Source:** programmatic | **Dispute dims:** format_compliance

### Enrichment Brief
```
  open_roles_estimate: 2
  engineering_velocity: unknown
  ai_maturity_score: 1
  icp_segment: segment_1_series_a_b
  icp_confidence: medium
  layoff_event: False
  num_employees: 1-50
  total_funding_rounds: 1
  low_peer_count: False
  competitor_gap_confidence: high
```

### Candidate Email
**Subject:** `Context: Drift Analytics engineering team`

**Body** (34 words):

Hi there, I came across Drift Analytics and wanted to reach out about your engineering hiring needs. Tenacious specialises in sourcing specialist engineers quickly. Would you be open to a brief call this week?

### Scores
| Dimension | R1 | R2 | **R3** | R3 Justification |
|-----------|----|----|--------|------------------|
| signal_fidelity | 1 | 1 | 1 | |
| tone_compliance | 1 | 1 | 1 | |
| segment_gate | 1 | 1 | 1 | |
| confidence_hedging | 1 | 1 | 1 | |
| format_compliance | 0 | 1 | 0 ← DISPUTE | [DRAFT] absent from subject line|

---

## Task 23: TB-PROG-024
**Category:** FC9_draft_tag | **Source:** programmatic | **Dispute dims:** format_compliance

### Enrichment Brief
```
  open_roles_estimate: 2
  engineering_velocity: low
  ai_maturity_score: 0
  icp_segment: segment_1_series_a_b
  icp_confidence: medium
  layoff_event: True
  num_employees: 1-50
  total_funding_rounds: 1
  low_peer_count: False
  competitor_gap_confidence: low
```

### Candidate Email
**Subject:** `Context: Drift Analytics engineering team`

**Body** (34 words):

Hi there, I came across Drift Analytics and wanted to reach out about your engineering hiring needs. Tenacious specialises in sourcing specialist engineers quickly. Would you be open to a brief call this week?

### Scores
| Dimension | R1 | R2 | **R3** | R3 Justification |
|-----------|----|----|--------|------------------|
| signal_fidelity | 1 | 1 | 1 | |
| tone_compliance | 1 | 1 | 1 | |
| segment_gate | 1 | 1 | 1 | |
| confidence_hedging | 1 | 1 | 1 | |
| format_compliance | 0 | 1 | 0 ← DISPUTE | [DRAFT] absent from subject line|

---

## Task 24: TB-PROG-009
**Category:** FC9_draft_tag | **Source:** programmatic | **Dispute dims:** confidence_hedging, format_compliance

### Enrichment Brief
```
  open_roles_estimate: 0
  engineering_velocity: moderate
  ai_maturity_score: 0
  icp_segment: segment_1_series_a_b
  icp_confidence: medium
  layoff_event: False
  num_employees: 1-50
  total_funding_rounds: 5
  low_peer_count: True
  competitor_gap_confidence: high
```

### Candidate Email
**Subject:** `Context: Coda Payments engineering team`

**Body** (34 words):

Hi there, I came across Coda Payments and wanted to reach out about your engineering hiring needs. Tenacious specialises in sourcing specialist engineers quickly. Would you be open to a brief call this week?

### Scores
| Dimension | R1 | R2 | **R3** | R3 Justification |
|-----------|----|----|--------|------------------|
| signal_fidelity | 1 | 1 | 1 | |
| tone_compliance | 1 | 1 | 1 | |
| segment_gate | 1 | 1 | 1 | |
| confidence_hedging | 0 | 1 | 0 ← DISPUTE |low_peer_count=True, no hedging words in body |
| format_compliance | 0 | 1 | 0 ← DISPUTE | [DRAFT] absent from subject line|

---

## Task 25: TB-PROG-104
**Category:** FC9_draft_tag | **Source:** programmatic | **Dispute dims:** confidence_hedging, format_compliance

### Enrichment Brief
```
  open_roles_estimate: 5
  engineering_velocity: high
  ai_maturity_score: 0
  icp_segment: segment_1_series_a_b
  icp_confidence: medium
  layoff_event: False
  num_employees: 51-200
  total_funding_rounds: 1
  low_peer_count: True
  competitor_gap_confidence: high
```

### Candidate Email
**Subject:** `Context: Meridian EdTech engineering team`

**Body** (34 words):

Hi there, I came across Meridian EdTech and wanted to reach out about your engineering hiring needs. Tenacious specialises in sourcing specialist engineers quickly. Would you be open to a brief call this week?

### Scores
| Dimension | R1 | R2 | **R3** | R3 Justification |
|-----------|----|----|--------|------------------|
| signal_fidelity | 1 | 1 | 1 | |
| tone_compliance | 1 | 1 | 1 | |
| segment_gate | 1 | 1 | 1 | |
| confidence_hedging | 0 | 1 | 0 ← DISPUTE |low_peer_count=True, no hedging words in body |
| format_compliance | 0 | 1 | 0 ← DISPUTE |[DRAFT] absent from subject line|

---

## Task 26: TB-PROG-054
**Category:** FC9_draft_tag | **Source:** programmatic | **Dispute dims:** confidence_hedging, format_compliance

### Enrichment Brief
```
  open_roles_estimate: 10
  engineering_velocity: moderate
  ai_maturity_score: 0
  icp_segment: segment_1_series_a_b
  icp_confidence: medium
  layoff_event: True
  num_employees: 51-200
  total_funding_rounds: 0
  low_peer_count: True
  competitor_gap_confidence: medium
```

### Candidate Email
**Subject:** `Context: Helio Finance engineering team`

**Body** (34 words):

Hi there, I came across Helio Finance and wanted to reach out about your engineering hiring needs. Tenacious specialises in sourcing specialist engineers quickly. Would you be open to a brief call this week?

### Scores
| Dimension | R1 | R2 | **R3** | R3 Justification |
|-----------|----|----|--------|------------------|
| signal_fidelity | 1 | 1 | 1 | |
| tone_compliance | 1 | 1 | 1 | |
| segment_gate | 1 | 1 | 1 | |
| confidence_hedging | 0 | 1 | 0 ← DISPUTE | low_peer_count=True, no hedging words in body|
| format_compliance | 0 | 1 | 0 ← DISPUTE | [DRAFT] absent from subject line|

---

## Task 27: TB-PROG-060
**Category:** tone_compliance | **Source:** programmatic | **Dispute dims:** confidence_hedging, format_compliance

### Enrichment Brief
```
  open_roles_estimate: 2
  engineering_velocity: low
  ai_maturity_score: 1
  icp_segment: segment_1_series_a_b
  icp_confidence: medium
  layoff_event: False
  num_employees: 1-50
  total_funding_rounds: 1
  low_peer_count: True
  competitor_gap_confidence: high
```

### Candidate Email
**Subject:** `[DRAFT] Context: Apex Robotics — explosive growth opportunity`

**Body** (36 words):

Hi there, Exciting times! Apex Robotics is scaling aggressively and we'd love to help you revolutionize your engineering team with cutting-edge talent. As an industry leader in staffing, we're ready to support your rapid growth journey.

### Scores
| Dimension | R1 | R2 | **R3** | R3 Justification |
|-----------|----|----|--------|------------------|
| signal_fidelity | 1 | 1 | 1 | |
| tone_compliance | 0 | 0 | 0 | |
| segment_gate | 1 | 1 | 1 | |
| confidence_hedging | 0 | 1 | 0 ← DISPUTE |low_peer_count=True, no hedging words in body |
| format_compliance | 1 | 0 | 1 ← DISPUTE | [DRAFT] present in subject, body ≤120 words, no bench commitment|

---

## Task 28: TB-PROG-065
**Category:** tone_compliance | **Source:** programmatic | **Dispute dims:** confidence_hedging

### Enrichment Brief
```
  open_roles_estimate: 10
  engineering_velocity: unknown
  ai_maturity_score: 2
  icp_segment: segment_1_series_a_b
  icp_confidence: low
  layoff_event: False
  num_employees: 1-50
  total_funding_rounds: 2
  low_peer_count: False
  competitor_gap_confidence: medium
```

### Candidate Email
**Subject:** `[DRAFT] Context: Apex Robotics — explosive growth opportunity`

**Body** (36 words):

Hi there, Exciting times! Apex Robotics is scaling aggressively and we'd love to help you revolutionize your engineering team with cutting-edge talent. As an industry leader in staffing, we're ready to support your rapid growth journey.

### Scores
| Dimension | R1 | R2 | **R3** | R3 Justification |
|-----------|----|----|--------|------------------|
| signal_fidelity | 1 | 1 | 1 | |
| tone_compliance | 0 | 0 | 0 | |
| segment_gate | 1 | 1 | 1 | |
| confidence_hedging | 0 | 1 | 0 ← DISPUTE |icp_confidence=low, no hedging words in body |
| format_compliance | 1 | 1 | 1 | |

---

## Task 29: TB-PROG-050
**Category:** tone_compliance | **Source:** programmatic | **Dispute dims:** signal_fidelity

### Enrichment Brief
```
  open_roles_estimate: 1
  engineering_velocity: low
  ai_maturity_score: 3
  icp_segment: segment_1_series_a_b
  icp_confidence: low
  layoff_event: True
  num_employees: 501-1000
  total_funding_rounds: 1
  low_peer_count: True
  competitor_gap_confidence: medium
```

### Candidate Email
**Subject:** `[DRAFT] Context: Tidal Energy — explosive growth opportunity`

**Body** (36 words):

Hi there, Exciting times! Tidal Energy is scaling aggressively and we'd love to help you revolutionize your engineering team with cutting-edge talent. As an industry leader in staffing, we're ready to support your rapid growth journey.

### Scores
| Dimension | R1 | R2 | **R3** | R3 Justification |
|-----------|----|----|--------|------------------|
| signal_fidelity | 1 | 0 | 0 ← DISPUTE |layoff=True + velocity=low + open_roles=1, "scaling aggressively" unsupported |
| tone_compliance | 0 | 0 | 0 | |
| segment_gate | 1 | 1 | 1 | |
| confidence_hedging | 0 | 0 | 0 | |
| format_compliance | 1 | 1 | 1 | |

---

## Task 30: TB-PROG-025
**Category:** tone_compliance | **Source:** programmatic | **Dispute dims:** signal_fidelity

### Enrichment Brief
```
  open_roles_estimate: 0
  engineering_velocity: unknown
  ai_maturity_score: 0
  icp_segment: segment_1_series_a_b
  icp_confidence: low
  layoff_event: True
  num_employees: 501-1000
  total_funding_rounds: 1
  low_peer_count: True
  competitor_gap_confidence: medium
```

### Candidate Email
**Subject:** `[DRAFT] Context: Cobalt DevTools — explosive growth opportunity`

**Body** (36 words):

Hi there, Exciting times! Cobalt DevTools is scaling aggressively and we'd love to help you revolutionize your engineering team with cutting-edge talent. As an industry leader in staffing, we're ready to support your rapid growth journey.

### Scores
| Dimension | R1 | R2 | **R3** | R3 Justification |
|-----------|----|----|--------|------------------|
| signal_fidelity | 1 | 0 | 0 ← DISPUTE |layoff=True + open_roles=0, "scaling aggressively" unsupported |
| tone_compliance | 0 | 0 | 0 | |
| segment_gate | 1 | 1 | 1 | |
| confidence_hedging | 0 | 0 | 0 | |
| format_compliance | 1 | 1 | 1 | |

---
