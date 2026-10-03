#!/usr/bin/env python3
"""Prepare deterministic public GSM8K samples. No model calls, no dependencies."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import re
import urllib.request

from .core import ROOT, digest, load_tasks, now, numeric, write_json


def dump_rows(path, items):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(i, ensure_ascii=False) + "\n" for i in items))


def prepare(source_dir, revision, out, dev_n=20, eval_n=60, seed=271828):
    if not re.fullmatch("[0-9a-f]{40}", revision):
        raise ValueError("Use an immutable 40-character source commit")
    raw = {}
    for split in ("train", "test"):
        path = Path(source_dir) / (split + ".jsonl")
        raw[split] = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    if not 1 <= dev_n <= len(raw["train"]) or not 1 <= eval_n <= len(raw["test"]):
        raise ValueError("Invalid sample size")
    # Predefine cross-split exact duplicates as ineligible, before seeing outputs.
    train_questions = {r["question"].strip() for r in raw["train"]}
    eligible = [i for i, r in enumerate(raw["test"]) if r["question"].strip() not in train_questions]
    rng = random.Random(seed)
    choices = {"dev": rng.sample(range(len(raw["train"])), dev_n),
               "eval": rng.sample(eligible, eval_n)}
    out = Path(out)
    if out.exists():
        raise ValueError("Output exists; use a new preparation directory")
    out.mkdir(parents=True)
    for partition, split in (("dev", "train"), ("eval", "test")):
        tasks, keys = [], []
        for i in choices[partition]:
            item = raw[split][i]
            gold = item["answer"].rsplit("####", 1)[-1].strip()
            if "####" not in item["answer"] or numeric(gold) is None:
                raise ValueError("Unscorable gold; investigate and amend rather than silently exclude")
            task_id = f"gsm8k-{split}-{i}"
            tasks.append({"id": task_id, "question": item["question"]})
            keys.append({"id": task_id, "answer": gold})
        task_path, key_path = out / f"{partition}_tasks.jsonl", out / "private" / f"{partition}_key.jsonl"
        dump_rows(task_path, tasks)
        dump_rows(key_path, keys)
        key_path.chmod(0o600)
        load_tasks(task_path)
        manifest = {"dataset": "GSM8K main", "hf_repository": "openai/gsm8k",
                    "hf_metadata_revision": "740312add88f781978c0658806c59bc2815b9866",
                    "acquisition_repository": "openai/grade-school-math", "source_revision": revision,
                    "source_file": f"grade_school_math/data/{split}.jsonl", "source_split": split,
                    "source_sha256": digest((Path(source_dir) / f"{split}.jsonl").read_bytes()),
                    "cross_split_exact_duplicates_excluded": len(raw["test"]) - len(eligible),
                    "partition": partition, "purpose": "feasibility" if partition == "eval" else "development",
                    "task_population": "English multistep grade-school arithmetic word problems",
                    "seed": seed, "sample_ids": [t["id"] for t in tasks], "n": len(tasks),
                    "tasks_sha256": digest(task_path.read_bytes()), "key_sha256": digest(key_path.read_bytes()),
                    "licence": "MIT (upstream dataset; not a licence for this entire project)",
                    "prepared_at": now(), "contamination_status": "Unknown; public benchmark may be in model training data"}
        write_json(out / f"{partition}_manifest.json", manifest)
    return {"development": dev_n, "evaluation": eval_n, "output": str(out)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--revision", required=True)
    p.add_argument("--source-dir", default="data/downloads")
    p.add_argument("--out", default="data/prepared")
    p.add_argument("--download", action="store_true")
    p.add_argument("--dev-n", type=int, default=20)
    p.add_argument("--eval-n", type=int, default=60)
    a = p.parse_args()
    if not re.fullmatch("[0-9a-f]{40}", a.revision):
        p.error("revision must be an immutable 40-character source commit")
    source = Path(a.source_dir)
    source.mkdir(parents=True, exist_ok=True)
    if a.download:
        for split in ("train", "test"):
            url = f"https://raw.githubusercontent.com/openai/grade-school-math/{a.revision}/grade_school_math/data/{split}.jsonl"
            with urllib.request.urlopen(url, timeout=30) as r:
                content = r.read(10_000_001)
            if len(content) > 10_000_000:
                raise ValueError("Unexpectedly large source")
            path = source / f"{split}.jsonl"
            if path.exists() and path.read_bytes() != content:
                raise ValueError("Source changed; use a new directory")
            path.write_bytes(content)
    print(json.dumps(prepare(source, a.revision, a.out, a.dev_n, a.eval_n)))


if __name__ == "__main__":
    main()
