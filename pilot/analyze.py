from __future__ import annotations

import argparse
import json
from collections import defaultdict


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarise pilot records")
    parser.add_argument("--input", required=True)
    args = parser.parse_args()
    groups = defaultdict(list)
    with open(args.input, encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            groups[record["condition"]].append(record)
    for condition, records in sorted(groups.items()):
        successful = [r for r in records if r["status"] == "ok"]
        scores = [r["score"]["lexical_recall"] for r in successful]
        mean = sum(scores) / len(scores) if scores else None
        calls = sum(r.get("calls", 0) for r in records)
        print(json.dumps({"condition": condition, "n": len(records), "successful": len(successful), "mean_development_score": mean, "total_calls": calls}, sort_keys=True))


if __name__ == "__main__":
    main()
