#!/usr/bin/env python3
"""Bounded A/B/C workflow pilot. Python 3.12 standard library; no agent framework."""
import argparse
import contextlib
import datetime as dt
import decimal
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import random
import re
import socket
import statistics
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
STAGES = ("A", "B1", "B2", "C1", "C2")
SCORER = "numeric-final-v1"


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def encode(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    tmp.replace(path)


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def numeric(text):
    """Strict decimal syntax, optional valid thousands separators. Never eval()."""
    value = str(text).strip()
    if not re.fullmatch(r"[+-]?(?:(?:\d{1,3}(?:,\d{3})+)|\d+)(?:\.\d+)?", value):
        return None
    return decimal.Decimal(value.replace(",", ""))


def answer(text):
    # Exactly one FINAL line, which must be the last nonempty line.
    lines = str(text).strip().splitlines()
    if not lines or sum(line.strip().startswith("FINAL:") for line in lines) != 1:
        return None
    if not lines[-1].strip().startswith("FINAL:"):
        return None
    return numeric(lines[-1].strip()[6:])


def load_tasks(path):
    data = rows(path)
    ids, questions = set(), set()
    for row in data:
        if set(row) != {"id", "question"}:
            raise ValueError("Task rows must contain ONLY id and question; no answers/metadata.")
        if not isinstance(row["id"], str) or not re.fullmatch(r"[A-Za-z0-9_.:-]+", row["id"]):
            raise ValueError("Invalid task id")
        if not isinstance(row["question"], str) or not row["question"].strip():
            raise ValueError("Empty question")
        q = row["question"].strip()
        if row["id"] in ids or q in questions:
            raise ValueError("Duplicate task id or question")
        ids.add(row["id"])
        questions.add(q)
    if not data:
        raise ValueError("No tasks")
    return data


def positive(value, name, allow_zero=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"Missing/invalid {name}")
    if value < 0 or (value == 0 and not allow_zero):
        raise ValueError(f"Invalid {name}")


def validate_config(c, manifest, n):
    if c["backend"] not in ("fixture", "http"):
        raise ValueError("Unsupported backend")
    for field in ("max_calls", "max_seconds", "timeout_seconds", "max_request_bytes"):
        positive(c[field], field)
    if type(c["max_calls"]) is not int or c["max_calls"] < n * 5:
        raise ValueError("max_calls must permit the complete planned sample (5 calls/task)")
    if not 0 <= c["temperature"] <= 2 or type(c["seed"]) is not int:
        raise ValueError("Invalid generation settings")
    for stage in STAGES:
        if type(c["max_tokens"][stage]) is not int or c["max_tokens"][stage] < 1:
            raise ValueError("Invalid stage token allowance")
    if c["max_tokens"]["B1"] != c["max_tokens"]["C1"] or c["max_tokens"]["B2"] != c["max_tokens"]["C2"]:
        raise ValueError("B/C token ceilings must match")
    if not manifest.get("source_revision") or not manifest.get("task_population"):
        raise ValueError("Missing data provenance")
    if c["backend"] == "fixture":
        if manifest.get("purpose") != "fixture-verification":
            raise ValueError("Fixture backend may only use the bundled verification tasks")
        return
    required = ("model", "deployment_revision", "authority_reference", "operator", "endpoint", "task_population_accepted")
    if any(not c.get(k) or str(c[k]).startswith("SET_") for k in required):
        raise ValueError("Live execution requires model, deployment, task acceptance and authority fields")
    if c.get("execution_authorized") is not True:
        raise ValueError("Live execution has not been authorised")
    u = urllib.parse.urlparse(c["endpoint"])
    if u.scheme != "https" or not u.hostname or u.username or u.password or u.query or u.fragment:
        raise ValueError("Endpoint must be HTTPS, without embedded credentials/query/fragment")
    for field in ("budget_usd", "per_call_reservation_usd", "input_usd_per_million", "output_usd_per_million"):
        positive(c.get(field), field, allow_zero=field.endswith("per_million"))
    if not c.get("reservation_basis") or not c.get("price_source"):
        raise ValueError("Document the all-inclusive call bound and dated pricing source")
    if c["budget_usd"] + 1e-10 < n * 5 * c["per_call_reservation_usd"]:
        raise ValueError("Budget does not cover conservative reservations for every planned call")
    if manifest.get("purpose") not in ("fixture-verification", "development", "feasibility"):
        raise ValueError("This harness supports verification, development and feasibility only")


def freeze(config_path, tasks_path, manifest_path, out):
    c, m = read_json(config_path), read_json(manifest_path)
    tasks = load_tasks(tasks_path)
    if digest(Path(tasks_path).read_bytes()) != m["tasks_sha256"]:
        raise ValueError("Task manifest mismatch")
    validate_config(c, m, len(tasks))
    if Path(out).exists():
        raise ValueError("Freeze already exists; use a new file and record an amendment")
    prompts = read_json(ROOT / "prompts.json")
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, stderr=subprocess.DEVNULL, text=True).strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip())
    except (OSError, subprocess.CalledProcessError):
        commit, dirty = None, None
    record = {"schema": 1, "created_at": now(), "config": c, "prompts": prompts,
              "data_manifest": m, "tasks_sha256": digest(Path(tasks_path).read_bytes()),
              "task_ids": [t["id"] for t in tasks], "code_sha256": digest(Path(__file__).read_bytes()),
              "code_commit": commit if dirty is False else None, "base_git_commit": commit,
              "git_worktree_dirty": dirty,
              "spec_sha256": digest((ROOT / "docs/experiment_spec.md").read_bytes()),
              "preparation_code_sha256": digest((ROOT / "pilot/prepare_data.py").read_bytes()),
              "scorer": SCORER, "study_type": m["purpose"],
              "verification_only": c["backend"] == "fixture" or m["purpose"] == "fixture-verification"}
    record["freeze_id"] = digest(encode(record))
    write_json(out, record)
    return record


def check_freeze(path, tasks_path):
    frozen = read_json(path)
    original_id = frozen.pop("freeze_id")
    if digest(encode(frozen)) != original_id:
        raise ValueError("Freeze was modified")
    frozen["freeze_id"] = original_id
    if frozen["code_sha256"] != digest(Path(__file__).read_bytes()):
        raise ValueError("Runtime code changed; create a new freeze and run")
    if frozen["tasks_sha256"] != digest(Path(tasks_path).read_bytes()):
        raise ValueError("Task file changed")
    tasks = load_tasks(tasks_path)
    if [t["id"] for t in tasks] != frozen["task_ids"]:
        raise ValueError("Task IDs changed")
    validate_config(frozen["config"], frozen["data_manifest"], len(tasks))
    return frozen, tasks


def messages(prompts, task, stage, initial="", middle=""):
    # Delimit data as JSON. No task metadata, evaluator key, or tool definitions.
    payload = {"question": task["question"]}
    if stage != "A":
        payload["initial_answer"] = initial
    if stage.endswith("2"):
        payload["additional_material"] = middle
    instruction = prompts["direct" if stage == "A" else "critique" if stage == "B1" else "additional_solve" if stage == "C1" else "finalize"]
    return [{"role": "system", "content": prompts["system"]},
            {"role": "user", "content": instruction + "\nINPUT DATA:\n" + json.dumps(payload, ensure_ascii=False)}]


def fixture_reply(task, stage, request, config):
    # Scripted responses exercise correction, regression, parse failure and refusal.
    # They are NOT generated answers, estimates of accuracy, or actual token usage.
    cases = {
        "fixture-1": {"A": "FINAL: 8", "B2": "FINAL: 9", "C2": "FINAL: 8"},
        "fixture-2": {"A": "FINAL: 12", "B2": "FINAL: 10", "C2": "FINAL: 12"},
        "fixture-3": {"A": "FINAL: 20", "B2": "FINAL: 20", "C2": "20"},
        "fixture-4": {"A": "FINAL: 3", "B2": "I cannot answer.", "C2": "FINAL: 4"},
    }
    return {"text": cases[task["id"]].get(stage, "Scripted intermediate material."),
            "input_tokens": 100, "output_tokens": 12, "finish_reason": "stop",
            "response_model": "scripted-fixture-v1", "request_id": None,
            "system_fingerprint": None, "usage_origin": "synthetic-fixture"}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Endpoint redirects are disabled")


def http_reply(task, stage, request, config):
    key = os.getenv(config.get("api_key_env", "PILOT_API_KEY"))
    if not key:
        raise ValueError("Missing endpoint credential in configured environment variable")
    payload = {"model": config["model"], "messages": request,
               "max_tokens": config["max_tokens"][stage], "temperature": config["temperature"],
               "stream": False}
    if config.get("send_seed", False):
        payload["seed"] = config["seed"]
    req = urllib.request.Request(config["endpoint"], data=encode(payload),
                                 headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    with urllib.request.build_opener(NoRedirect()).open(req, timeout=config["timeout_seconds"]) as response:
        raw = response.read(1024 * 1024 + 1)
        if len(raw) > 1024 * 1024:
            raise ValueError("Oversized API response")
        result = json.loads(raw)
    choice = result["choices"][0]
    usage = result.get("usage") or {}
    return {"text": choice.get("message", {}).get("content") or "",
            "input_tokens": usage.get("prompt_tokens"), "output_tokens": usage.get("completion_tokens"),
            "finish_reason": choice.get("finish_reason"), "response_model": result.get("model"),
            "request_id": result.get("id"), "system_fingerprint": result.get("system_fingerprint"),
            "usage_origin": "provider-reported"}


def append(path, value):
    with Path(path).open("a") as f:
        f.write(json.dumps(value, ensure_ascii=False, allow_nan=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def audit_events(events, expected):
    starts, finishes = {}, {}
    for event in events:
        key = event.get("call_id")
        if key not in expected:
            raise ValueError("Unexpected call in ledger")
        if event["event"] == "start":
            if key in starts or key in finishes:
                raise ValueError("Duplicate call start")
            starts[key] = event
        elif event["event"] == "finish":
            if key in finishes:
                raise ValueError("Duplicate call result")
            if event["status"] not in ("skipped_dependency", "skipped_input_limit") and key not in starts:
                raise ValueError("Result without durable start")
            finishes[key] = event
        else:
            raise ValueError("Unknown ledger event")
    return starts, finishes


@contextlib.contextmanager
def run_lock(directory):
    with (directory / ".lock").open("a") as f:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def run(freeze_path, tasks_path, out, backend_override=None):
    frozen, tasks = check_freeze(freeze_path, tasks_path)
    c = frozen["config"]
    if c["backend"] == "http" and not os.getenv(c.get("api_key_env", "PILOT_API_KEY")):
        raise ValueError("Missing endpoint credential; no requests sent")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    with run_lock(out):
        return run_locked(frozen, tasks, out, backend_override)


def run_locked(frozen, tasks, out, backend_override):
    c = frozen["config"]
    meta_path, log = out / "run.json", out / "events.jsonl"
    if meta_path.exists():
        meta = read_json(meta_path)
        if meta["freeze_id"] != frozen["freeze_id"]:
            raise ValueError("Cannot resume with a different freeze")
    else:
        meta = {"run_id": out.name, "freeze_id": frozen["freeze_id"], "started_at": now(),
                "frozen": frozen, "verification_only": frozen["verification_only"], "status": "started"}
        write_json(meta_path, meta)
    expected = {f'{t["id"]}/{s}' for t in tasks for s in STAGES}
    starts, done = audit_events(rows(log) if log.exists() else [], expected)
    # At-most-one attempt. A crash after request acceptance has an unknown charge.
    for key in starts.keys() - done.keys():
        event = {"event": "finish", "call_id": key, "at": now(), "status": "interrupted_unknown",
                 "text": "", "elapsed_s": None, "estimated_cost_usd": None}
        append(log, event)
        done[key] = event
    if any(e["status"] in ("usage_missing", "usage_invalid", "cost_bound_exceeded") for e in done.values()):
        meta.update(status="stopped", stop_reason="Unresolved usage/budget incident", updated_at=now())
        write_json(meta_path, meta)
        return meta
    rng = random.Random(c["seed"])
    order = list(tasks)
    rng.shuffle(order)
    reservation = c.get("per_call_reservation_usd", 0) if c["backend"] == "http" else 0
    called = len(starts)
    backend = backend_override or (fixture_reply if c["backend"] == "fixture" else http_reply)
    stop_reason = None
    for task in order:
        branch_order = ["B", "C"]
        rng.shuffle(branch_order)
        stages = ["A"] + [f"{b}{s}" for b in branch_order for s in (1, 2)]
        for stage in stages:
            key = f'{task["id"]}/{stage}'
            if key in done:
                continue
            age = (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(meta["started_at"])).total_seconds()
            if called >= c["max_calls"] or age >= c["max_seconds"] or (reservation and (called + 1) * reservation > c["budget_usd"] + 1e-10):
                stop_reason = "Execution limit reached; remaining tasks stay in denominator"
                break
            parents = [] if stage == "A" else [f'{task["id"]}/A']
            if stage.endswith("2"):
                parents.append(f'{task["id"]}/{stage[0]}1')
            if any(done.get(p, {}).get("status") != "ok" for p in parents):
                event = {"event": "finish", "call_id": key, "at": now(), "status": "skipped_dependency",
                         "text": "", "elapsed_s": 0, "estimated_cost_usd": 0}
                append(log, event)
                done[key] = event
                continue
            request = messages(frozen["prompts"], task, stage,
                               done[parents[0]]["text"] if parents else "",
                               done[parents[1]]["text"] if len(parents) == 2 else "")
            if len(encode(request)) > c["max_request_bytes"]:
                event = {"event": "finish", "call_id": key, "at": now(), "status": "skipped_input_limit",
                         "text": "", "elapsed_s": 0, "estimated_cost_usd": 0}
                append(log, event)
                done[key] = event
                continue
            start = {"event": "start", "call_id": key, "at": now(), "messages": request,
                     "max_tokens": c["max_tokens"][stage], "reservation_usd": reservation}
            append(log, start)
            called += 1
            clock = time.perf_counter()
            event = {"event": "finish", "call_id": key, "at": now(), "text": "", "estimated_cost_usd": None}
            try:
                reply = backend(task, stage, request, c)
                event.update(reply)
                inp, output = reply.get("input_tokens"), reply.get("output_tokens")
                if type(inp) is not int or type(output) is not int or min(inp, output) < 0:
                    event["status"] = "usage_missing"
                    stop_reason = "Provider usage unavailable; reconcile before another run"
                else:
                    cost = (inp * c.get("input_usd_per_million", 0) + output * c.get("output_usd_per_million", 0)) / 1e6
                    event["estimated_cost_usd"] = cost
                    event["status"] = "ok" if reply.get("finish_reason") == "stop" else "provider_nonstop"
                    if output > c["max_tokens"][stage]:
                        event["status"] = "usage_invalid"
                        stop_reason = "Provider output exceeded configured token ceiling"
                    if c["backend"] == "http" and cost > reservation + 1e-10:
                        event["status"] = "cost_bound_exceeded"
                        stop_reason = "Per-call cost bound exceeded; reconcile billing and revise bound"
            except (TimeoutError, socket.timeout):
                event["status"] = "timeout_unknown_charge"
            except urllib.error.HTTPError as e:
                event.update(status="http_error", http_status=e.code)
            except Exception as e:
                # Never log exception text that may contain credentials/provider payloads.
                event.update(status="request_error", error_type=type(e).__name__)
            event["elapsed_s"] = time.perf_counter() - clock
            event["at"] = now()
            append(log, event)
            done[key] = event
            if stop_reason:
                break
        if stop_reason:
            break
    meta.update(status="complete" if len(done) == len(expected) and not stop_reason else "stopped", updated_at=now(),
                stop_reason=stop_reason, physical_calls=called, reserved_cost_upper_usd=called * reservation)
    write_json(out / "run.json", meta)
    return meta


def binom_cdf(k, n, p):
    if p <= 0:
        return 1.0
    if p >= 1:
        return float(k >= n)
    return min(1.0, math.fsum(math.exp(math.lgamma(n+1) - math.lgamma(i+1) - math.lgamma(n-i+1)
                                     + i*math.log(p) + (n-i)*math.log1p(-p)) for i in range(k+1)))


def binomial_interval(k, n, alpha=0.05):
    """Clopper-Pearson by inversion; deliberately nonzero width at boundaries."""
    if n <= 0:
        return [None, None]
    def root(k, target):
        lo, hi = 0.0, 1.0
        for _ in range(65):
            mid = (lo + hi) / 2
            if binom_cdf(k, n, mid) > target:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2
    return [0.0 if k == 0 else root(k-1, 1-alpha/2), 1.0 if k == n else root(k, alpha/2)]


def paired_summary(first, second):
    n = len(first)
    gains = sum(x == 1 and y == 0 for x, y in zip(first, second))
    losses = sum(x == 0 and y == 1 for x, y in zip(first, second))
    # Four rate intervals (gain/loss for two contrasts), Bonferroni family >=95%.
    gi, li = binomial_interval(gains, n, 0.0125), binomial_interval(losses, n, 0.0125)
    d = gains + losses
    return {"n": n, "gains": gains, "regressions": losses, "difference": (gains-losses)/n,
            "familywise_95_interval": [gi[0]-li[1], gi[1]-li[0]],
            "mcnemar_exact_p_unadjusted": min(1.0, 2 * binom_cdf(min(gains, losses), d, 0.5)) if d else 1.0}


def tail(values, q):
    return sorted(values)[max(0, math.ceil(len(values)*q)-1)] if values else None


def analyze(run_dir, key_path):
    run_dir = Path(run_dir)
    meta = read_json(run_dir / "run.json")
    frozen = meta["frozen"]
    unsigned = {k: v for k, v in frozen.items() if k != "freeze_id"}
    if digest(encode(unsigned)) != frozen["freeze_id"]:
        raise ValueError("Embedded experimental freeze was modified")
    if frozen["code_sha256"] != digest(Path(__file__).read_bytes()):
        raise ValueError("Scoring code changed; restore frozen version or document a separate reanalysis")
    if digest(Path(key_path).read_bytes()) != frozen["data_manifest"]["key_sha256"]:
        raise ValueError("Answer-key hash mismatch")
    key_rows = rows(key_path)
    keys = {r["id"]: numeric(r["answer"]) for r in key_rows}
    ids = frozen["task_ids"]
    if len(keys) != len(key_rows) or set(keys) != set(ids) or any(v is None for v in keys.values()):
        raise ValueError("Answer-key IDs/values invalid")
    expected = {f"{i}/{s}" for i in ids for s in STAGES}
    starts, events = audit_events(rows(run_dir / "events.jsonl") if (run_dir / "events.jsonl").exists() else [], expected)
    outcomes, scores = [], {c: [] for c in "ABC"}
    for i in ids:
        item = {"id": i}
        for condition, stage in (("A", "A"), ("B", "B2"), ("C", "C2")):
            final = events.get(f"{i}/{stage}", {})
            parsed = answer(final.get("text", ""))
            ok = final.get("status") == "ok" and parsed is not None
            score = int(ok and parsed == keys[i])
            scores[condition].append(score)
            item[condition] = {"score": score, "parsed_answer": str(parsed) if parsed is not None else None,
                               "status": final.get("status", "not_executed"), "format_valid": parsed is not None}
        outcomes.append(item)
    n = len(ids)
    summaries = {}
    for c in "ABC":
        relevant = ["A"] if c == "A" else ["A", c+"1", c+"2"]
        complete_times, costs, input_counts, output_counts = [], [], [], []
        for i in ids:
            es = [events.get(f"{i}/{s}", {}) for s in relevant]
            if all(e.get("status") == "ok" and e.get("elapsed_s") is not None for e in es):
                complete_times.append(sum(e["elapsed_s"] for e in es))
            costs.extend(e.get("estimated_cost_usd") for e in es if e.get("estimated_cost_usd") is not None)
            input_counts.extend(e["input_tokens"] for e in es if type(e.get("input_tokens")) is int)
            output_counts.extend(e["output_tokens"] for e in es if type(e.get("output_tokens")) is int)
        summaries[c] = {"correct": sum(scores[c]), "planned_tasks": n, "accuracy": sum(scores[c])/n,
                        "accuracy_95_interval": binomial_interval(sum(scores[c]), n),
                        "latency_complete_workflows_n": len(complete_times),
                        "mean_complete_request_time_s": statistics.mean(complete_times) if complete_times else None,
                        "p95_complete_request_time_s_exploratory": tail(complete_times, .95),
                        "known_standalone_cost_estimate_usd": sum(costs),
                        "known_standalone_input_tokens": sum(input_counts),
                        "known_standalone_output_tokens": sum(output_counts),
                        "final_numeric_changes_from_A": sum(x[c]["parsed_answer"] != x["A"]["parsed_answer"] for x in outcomes),
                        "correct_initial_text_changed": sum(x["A"]["score"] == 1 and
                            events.get(f'{x["id"]}/A', {}).get("text") != events.get(f'{x["id"]}/{"A" if c == "A" else c+"2"}', {}).get("text")
                            for x in outcomes),
                        "invalid_final_formats": sum(not x[c]["format_valid"] for x in outcomes),
                        "non_ok_finals": sum(x[c]["status"] != "ok" for x in outcomes)}
    contrasts = {"B_minus_A": paired_summary(scores["B"], scores["A"]),
                 "B_minus_C": paired_summary(scores["B"], scores["C"])}
    for contrast in contrasts.values():
        contrast["bonferroni_p"] = min(1, contrast["mcnemar_exact_p_unadjusted"] * 2)
    estimated = [e.get("estimated_cost_usd") for e in events.values() if not e["status"].startswith("skipped_")]
    report = {"run_id": meta["run_id"], "freeze_id": frozen["freeze_id"], "scorer": SCORER,
              "verification_only": meta["verification_only"], "run_status": meta["status"],
              "study_type": frozen["study_type"], "conditions": summaries, "contrasts": contrasts,
              "physical_calls": len(starts), "known_physical_cost_estimate_usd": sum(x for x in estimated if x is not None),
              "unpriced_attempts": sum(x is None for x in estimated) + len(starts.keys()-events.keys()),
              "call_status_counts": {s: sum(e["status"] == s for e in events.values()) for s in sorted({e["status"] for e in events.values()})},
              "missing_stage_records": len(expected-events.keys()), "outcomes": outcomes,
              "decision": "NO_EFFICACY_INFERENCE_FIXTURE" if meta["verification_only"] else "FEASIBILITY_ONLY_NO_AUTOMATIC_ADOPTION",
              "limitations": ["Accuracy includes every planned task; failures/missing outputs score zero.",
                              "Time statistics sum request durations for successful workflows; exclude orchestration overhead and are not measured standalone end-to-end latency.",
                              "Costs calculated from supplied rates are estimates, not reconciled invoices.",
                              "Shared A is charged in each standalone workflow but only once in physical totals.",
                              "Intervals assume independent task units; benchmark contamination and transfer remain unresolved.",
                              "Fixture token counts are synthetic and fixture latency is not model latency."]}
    write_json(run_dir / "analysis.json", report)
    return report


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    f = sub.add_parser("freeze")
    for flag in ("config", "tasks", "manifest", "out"):
        f.add_argument("--"+flag, required=True)
    r = sub.add_parser("run")
    for flag in ("freeze", "tasks", "out"):
        r.add_argument("--"+flag, required=True)
    a = sub.add_parser("analyze")
    a.add_argument("--run", required=True)
    a.add_argument("--key", required=True)
    args = p.parse_args(argv)
    if args.command == "freeze":
        result = freeze(args.config, args.tasks, args.manifest, args.out)
        print(json.dumps({"freeze_id": result["freeze_id"], "verification_only": result["verification_only"]}))
    elif args.command == "run":
        result = run(args.freeze, args.tasks, args.out)
        print(json.dumps({k: result[k] for k in ("run_id", "status", "physical_calls", "verification_only")}))
    else:
        result = analyze(args.run, args.key)
        print(json.dumps({"run_id": result["run_id"], "decision": result["decision"], "physical_calls": result["physical_calls"]}))


if __name__ == "__main__":
    main()
