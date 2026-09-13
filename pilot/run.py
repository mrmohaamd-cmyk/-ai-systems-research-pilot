from __future__ import annotations

import argparse
import uuid

from .core import CommandBackend, MockBackend, load_tasks, run, write_jsonl


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the critique-and-revision pilot")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--condition", choices=["direct", "critique_revision", "additional_effort", "all"], default="all")
    parser.add_argument("--backend", choices=["mock", "command"], default="mock")
    parser.add_argument("--command", help="Command implementing the JSONL backend protocol")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    if args.backend == "command" and not args.command:
        parser.error("--command is required with --backend command")
    backend = MockBackend() if args.backend == "mock" else CommandBackend(args.command)
    conditions = ["direct", "critique_revision", "additional_effort"] if args.condition == "all" else [args.condition]
    tasks = load_tasks(args.dataset)
    records = []
    for condition in conditions:
        records.extend(run(tasks, condition, backend, uuid.uuid4().hex))
    write_jsonl(args.out, records)
    print(f"wrote {len(records)} records to {args.out}")


if __name__ == "__main__":
    main()
