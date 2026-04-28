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


BASE_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"  # fallback to 1.5B if 2B OOM on T4
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
- NEVER use banned phrases: scaling aggressively, rapid growth, explosive growth,
  industry leader, cutting-edge, revolutionize, bench capacity
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


def load_positive_pairs(jsonl_path: Path, min_score: float = 0.8) -> list[dict]:
    """Load tasks with score >= min_score as positive training pairs."""
    pairs = []
    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        task = json.loads(line)
        score = task.get("score")
        if score is not None and score >= min_score:
            pairs.append(task)
    print(f"Loaded {len(pairs)} positive pairs (score >= {min_score}) from {jsonl_path}")
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
        report_to="none",
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=MAX_SEQ_LEN,
        args=training_args,
    )

    trainer.train()

    output_dir.mkdir(parents=True, exist_ok=True)
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
