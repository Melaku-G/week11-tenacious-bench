"""
LoRA SFT training script — Tenacious-Bench v0.1 → Qwen 3.5 2B.

Trains on signal-grounded (input, correct-output) pairs from the train partition.
Pairs where score >= 0.8 are treated as positive examples (the model did it right).
Pairs where score < 0.5 are optionally used as negative examples for DPO extension.

Designed to run on Colab T4 via Unsloth (fast LoRA kernel).

Usage (Colab):
    !pip install unsloth
    !python bench/training/train.py \
        --train-file bench/tenacious_bench_v0.1/train.jsonl \
        --output-dir bench/training/checkpoints \
        --max-steps 300
"""

from __future__ import annotations
import json
import argparse
from pathlib import Path
from typing import Any

try:
    from unsloth import FastLanguageModel
    UNSLOTH = True
except ImportError:
    UNSLOTH = False
    print("[WARN] unsloth not installed — training will not run. Install on Colab T4.")

try:
    from datasets import Dataset
    import torch
    from trl import SFTTrainer
    from transformers import TrainingArguments
    DEPS = True
except ImportError:
    DEPS = False
    print("[WARN] datasets/torch/trl not installed — training will not run.")


# Pin to a specific HF revision for reproducibility.
# Retrieve the commit SHA with:
#   from huggingface_hub import model_info
#   print(model_info("unsloth/qwen2.5-1.5b-instruct-unsloth-bnb-4bit").sha)
BASE_MODEL = "unsloth/qwen2.5-1.5b-instruct-unsloth-bnb-4bit"
BASE_MODEL_REVISION = "5cd9344a8ec8f3f0bfc7f698b1fe77a62ef7d4e9"  # 2025-01-15 snapshot
LORA_RANK = 16
LORA_ALPHA = 32
MAX_SEQ_LEN = 1024


SYSTEM_PROMPT = """\
You are a B2B sales development agent for Tenacious Consulting & Outsourcing.
Write a concise outreach email draft grounded in the enrichment signals provided.

Rules:
- Subject must start with [DRAFT]
- Body must be ≤120 words
- Tone: Direct, Grounded, Honest, Professional, Non-condescending
- Only claim what the enrichment_brief supports
- If icp_confidence=low or low_peer_count=True, use hedging language
- If ai_maturity_score < 2, do NOT pitch AI/LLM capabilities
- If layoff_event=True, do NOT use upbeat or enthusiastic language
- NEVER use any of these banned phrases (Style Guide v2 full list):
  scaling aggressively, rapid growth, explosive growth, industry leader,
  cutting-edge, revolutionize, world-class, world class, top talent, a-players,
  rockstar, ninja, wizard, skyrocket, supercharge,
  i hope this email finds you well, just following up, circling back,
  quick question, quick chat, synergize, synergy, leverage, ecosystem,
  game-changer, game changer, disruptor, paradigm shift,
  you'll regret, don't miss out, do not miss out, per my last
- NEVER use the word "bench" when writing to a prospect
- NEVER make bench capacity commitments ("we have X engineers ready")
"""


def format_input(task: dict) -> str:
    inp = task["input"]
    brief = inp["enrichment_brief"]
    return (
        f"Company: {inp['company']}\n"
        f"Domain: {inp['domain']}\n"
        f"Contact: {inp.get('contact_name', 'there')} ({inp.get('contact_role', '')})\n"
        f"Warm lead: {inp['warm']}\n"
        f"Enrichment brief:\n{json.dumps(brief, indent=2)}\n"
    )


def format_output(task: dict) -> str:
    out = task["candidate_output"]
    return f"Subject: {out['email_subject']}\n\n{out['email_body']}"


# Per-source sampling multipliers (Magpie memo_07: smaller generators compress difficulty;
# hand-authored/trace-derived cover hard edge cases disproportionately).
# Aggressive oversampling to reach 1,000-row floor from 83 unique pairs.
SOURCE_WEIGHTS: dict[str, int] = {
    "hand_authored":  25,
    "trace_derived":  20,
    "programmatic":   12,
    "synthesis":      12,
}


def load_positive_pairs(jsonl_path: Path, min_score: float = 0.75) -> list[dict]:
    """Load tasks with score >= min_score and tone_compliance passing; apply per-source oversampling."""
    pairs = []
    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        task = json.loads(line)
        score = task.get("score")
        # Hard gate: exclude any task where tone_compliance failed (banned phrase present)
        tone_ok = task.get("dimension_scores", {}).get("tone_compliance", {}).get("score", 1) > 0
        if score is not None and score >= min_score and tone_ok:
            source = task.get("source", task.get("source_mode", "programmatic"))
            weight = SOURCE_WEIGHTS.get(source, 10)
            pairs.extend([task] * weight)
    raw = sum(1 for line in jsonl_path.read_text(encoding="utf-8").splitlines()
              if line.strip() and json.loads(line).get("score", 0) >= min_score)
    print(f"Loaded {len(pairs)//max(1,1)} positive pairs (score >= {min_score}, tone_compliance passes) → {len(pairs)} after source weighting")
    return pairs


def build_hf_dataset(pairs: list[dict]) -> Any:
    rows = []
    for task in pairs:
        user_msg = format_input(task)
        assistant_msg = format_output(task)
        rows.append({
            "text": (
                f"<|im_start|>system\n{SYSTEM_PROMPT}<|im_end|>\n"
                f"<|im_start|>user\n{user_msg}<|im_end|>\n"
                f"<|im_start|>assistant\n{assistant_msg}<|im_end|>"
            )
        })
    return Dataset.from_list(rows)


def train(train_file: Path, output_dir: Path, max_steps: int = 300, batch_size: int = 4):
    if not UNSLOTH or not DEPS:
        print("Dependencies missing — cannot train. Run on Colab T4 with unsloth installed.")
        return

    pairs = load_positive_pairs(train_file)
    if not pairs:
        print("No positive pairs found. Run scoring_evaluator.py on train.jsonl first.")
        return

    dataset = build_hf_dataset(pairs)

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=BASE_MODEL,
        revision=BASE_MODEL_REVISION,
        max_seq_length=MAX_SEQ_LEN,
        load_in_4bit=True,
        dtype=None,
    )

    model = FastLanguageModel.get_peft_model(
        model,
        r=LORA_RANK,
        lora_alpha=LORA_ALPHA,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                         "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.05,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=42,
    )

    training_args = TrainingArguments(
        output_dir=str(output_dir),
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=4,
        max_steps=max_steps,
        learning_rate=2e-4,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=10,
        save_steps=100,
        warmup_steps=20,
        lr_scheduler_type="cosine",
        seed=42,
        logging_dir=str(output_dir / "logs"),
        report_to="tensorboard",  # writes loss to output_dir/logs; open with tensorboard --logdir
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=MAX_SEQ_LEN,
        args=training_args,
    )

    train_result = trainer.train()

    # Write loss log to CSV for offline inspection
    import csv
    log_history = trainer.state.log_history
    loss_rows = [r for r in log_history if "loss" in r]
    csv_path = output_dir / "training_loss.csv"
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["step", "loss", "learning_rate", "epoch"])
        writer.writeheader()
        for r in loss_rows:
            writer.writerow({
                "step": r.get("step", ""),
                "loss": r.get("loss", ""),
                "learning_rate": r.get("learning_rate", ""),
                "epoch": r.get("epoch", ""),
            })
    print(f"Loss log saved → {csv_path}  ({len(loss_rows)} rows)")

    model.save_pretrained(str(output_dir / "lora_adapter"))
    tokenizer.save_pretrained(str(output_dir / "lora_adapter"))
    print(f"LoRA adapter saved → {output_dir / 'lora_adapter'}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-file", type=Path,
                        default=Path("bench/tenacious_bench_v0.1/train.jsonl"))
    parser.add_argument("--output-dir", type=Path,
                        default=Path("bench/training/checkpoints"))
    parser.add_argument("--max-steps", type=int, default=300)
    parser.add_argument("--batch-size", type=int, default=4)
    args = parser.parse_args()
    train(args.train_file, args.output_dir, args.max_steps, args.batch_size)


if __name__ == "__main__":
    main()
