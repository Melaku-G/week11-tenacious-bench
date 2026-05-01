from fpdf import FPDF, XPos, YPos

class PDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 11)
        self.cell(0, 10, "Tenacious-Bench v0.1 - Executive Memo",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font("Helvetica", "", 9)
        self.cell(0, 6, "To: CEO, CFO | From: Melaku Y. | Date: 2026-05-01",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(4)

pdf = PDF()
pdf.add_page()
pdf.set_auto_page_break(auto=True, margin=15)

sections = [
    ("PAGE 1: THE DECISION", "B", 12),
    ("What Was Built", "B", 10),
    ("Tenacious-Bench v0.1 is a domain-specific evaluation benchmark for B2B sales outreach agents. It contains 408 tasks across train, dev, and held-out partitions, covering six failure classes: signal overclaim, hallucinated firmographics, segment-gate bypass, tone violations, confidence hedging failures, and format non-compliance. A LoRA adapter was trained on 1,016 signal-grounded pairs using Qwen2.5-1.5B-Instruct. Training took 6 minutes on a T4 GPU.", "", 10),
    ("Headline Results", "B", 10),
    ("Unguarded baseline (Week 10): 0.6976\nPrompt-only guarded: 0.7992 (+0.1016)\nTrained adapter v0.1: 0.8863 (+0.1887)\n\nDelta A: +0.1887 (95% CI [+0.155, +0.224], p<0.0001, paired bootstrap, n=62)\nDelta B: +0.0871 - training beat prompt engineering alone (p<0.0001)\nDelta C: +0.1863 vs tau2-Bench retail baseline (0.70)", "", 10),
    ("Cost Per Task Delta", "B", 10),
    ("Base model latency: 7.17s avg | Trained adapter: 2.98s avg | Speedup: 2.4x faster\nThe adapter is simultaneously more accurate AND faster. This is a Pareto improvement.", "", 10),
    ("Production Recommendation", "B", 10),
    ("Deploy the adapter immediately for cold outreach generation.\n\n1. Replace the unguarded generation call with the LoRA adapter on Qwen2.5-1.5B-Instruct. Estimated latency: ~3s per email on T4-class hardware.\n\n2. Add the enrichment signal gate before generation. Tasks with icp_segment=abstain or icp_confidence=low + low_peer_count=True should route to human review, not direct send.\n\n3. Instrument signal_fidelity scoring on all outbound drafts. Flag any draft containing fabricated funding round claims before delivery to SDR inbox.\n\nExpected outcome: hallucination rate drops from ~30% to less than 5% based on held-out pass rate (0.8863).", "", 10),
    ("PAGE 2: THE SKEPTIC'S APPENDIX", "B", 12),
    ("Failure Modes the Benchmark Does Not Capture", "B", 10),
    ("1. Multi-turn conversation quality. Tenacious-Bench evaluates single outreach drafts only. Follow-up email quality and reply handling are not measured.\n\n2. Real prospect response rate. The rubric scores signal fidelity and tone. It does not measure whether emails get replies.\n\n3. Out-of-distribution enrichment signals. Segments outside segment_1 to segment_4 (e.g., government, NGO, pre-revenue) are not evaluated.\n\n4. Prompt injection robustness. Adversarial enrichment briefs crafted by a motivated attacker have limited held-out coverage.", "", 10),
    ("Public-Signal Lossiness in Ground Truth", "B", 10),
    ("Enrichment signals are derived from public data proxies with ~20-30% error rate vs ground truth company state. An email grounded in a wrong brief scores well but sends false information to the prospect.", "", 10),
    ("One Honest Unresolved Failure", "B", 10),
    ("TB-TD-001 (Karibu Tech trace) passed the score==1.0 filter in earlier pipeline versions despite containing banned phrases. The scorer regex did not catch these paraphrase variants. After manual removal, 0 such cases remain in training data, but the scorer gap may allow future reintroduction without detection.", "", 10),
    ("Kill-Switch Trigger", "B", 10),
    ("Suspend adapter deployment if any of the following occur:\n- Signal fidelity score drops below 0.75 on a rolling 50-task production sample\n- More than 3 confirmed hallucinated funding claims reach SDR inboxes in a 7-day window\n- A prospect complaint referencing fabricated company information is received\n- Delta A on quarterly re-evaluation falls below +0.10 vs unguarded baseline\n\nReversion path: disable LoRA adapter, fall back to prompt-only guarded baseline (score 0.7992).", "", 10),
]

for section in sections:
    text, style, size = section
    pdf.set_font("Helvetica", style, size)
    if style == "B" and size >= 12:
        pdf.ln(6)
        pdf.cell(0, 8, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(2)
    elif style == "B":
        pdf.ln(4)
        pdf.cell(0, 7, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    else:
        pdf.set_font("Helvetica", "", size)
        pdf.multi_cell(0, 6, text)
    pdf.ln(1)

pdf.output("memo.pdf")
print("memo.pdf created successfully")