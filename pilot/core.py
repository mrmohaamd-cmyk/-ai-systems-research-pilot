from __future__ import annotations

import json
import os
import shlex
import subprocess
import time
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Protocol


PROMPT_VERSION = "prompts-v1"
RUNNER_VERSION = "runner-v1"


@dataclass(frozen=True)
class Task:
    task_id: str
    prompt: str
    reference: str
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class ModelResponse:
    text: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    latency_ms: float | None = None


class Backend(Protocol):
    name: str

    def complete(self, messages: list[dict[str, str]], condition: str) -> ModelResponse:
        ...


def load_tasks(path: str) -> list[Task]:
    tasks: list[Task] = []
    with open(path, encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                raw = json.loads(line)
                tasks.append(Task(
                    task_id=str(raw["task_id"]),
                    prompt=str(raw["prompt"]),
                    reference=str(raw["reference"]),
                    tags=tuple(raw.get("tags", [])),
                ))
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"Invalid task at {path}:{line_number}: {exc}") from exc
    if not tasks:
        raise ValueError(f"Dataset is empty: {path}")
    if len({task.task_id for task in tasks}) != len(tasks):
        raise ValueError("Dataset contains duplicate task_id values")
    return tasks


def _messages(task: Task, condition: str) -> list[dict[str, str]]:
    system = "Answer accurately and concisely. Do not claim to have used tools or sources you did not use."
    if condition == "direct":
        return [{"role": "system", "content": system}, {"role": "user", "content": task.prompt}]
    if condition == "additional_effort":
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": task.prompt},
            {"role": "user", "content": "Produce a fresh, independently considered answer. Improve accuracy and completeness."},
        ]
    raise ValueError(f"Unsupported single-stage condition: {condition}")


def _score(answer: str, reference: str) -> dict[str, Any]:
    """Transparent development score; replace with a validated task rubric before final evaluation."""
    answer_words = {word.strip(".,!?():;").lower() for word in answer.split() if word.strip()}
    reference_words = {word.strip(".,!?():;").lower() for word in reference.split() if word.strip()}
    overlap = len(answer_words & reference_words) / max(1, len(reference_words))
    return {"lexical_recall": round(overlap, 6), "answer_nonempty": bool(answer.strip())}


class MockBackend:
    name = "mock"

    def complete(self, messages: list[dict[str, str]], condition: str) -> ModelResponse:
        prompt = next(message["content"] for message in messages if message["role"] == "user")
        if condition == "critique":
            return ModelResponse("Check the answer for missing facts, unsupported claims, and directness.")
        prefix = {"direct": "Direct answer: ", "additional_effort": "Second-pass answer: ", "revision": "Revised answer: "}[condition]
        return ModelResponse(prefix + prompt)


class CommandBackend:
    name = "command"

    def __init__(self, command: str, timeout: int = 120):
        self.command = command
        self.timeout = timeout

    def complete(self, messages: list[dict[str, str]], condition: str) -> ModelResponse:
        request = {"messages": messages, "condition": condition}
        started = time.perf_counter()
        completed = subprocess.run(
            shlex.split(self.command), input=json.dumps(request) + "\n", text=True,
            capture_output=True, timeout=self.timeout, check=False,
        )
        latency = (time.perf_counter() - started) * 1000
        if completed.returncode != 0:
            raise RuntimeError(f"backend exited {completed.returncode}: {completed.stderr[-500:]}")
        try:
            raw = json.loads(completed.stdout.strip().splitlines()[-1])
            return ModelResponse(str(raw["text"]), raw.get("input_tokens"), raw.get("output_tokens"), raw.get("latency_ms", latency))
        except (IndexError, KeyError, TypeError, ValueError) as exc:
            raise RuntimeError("backend must emit JSON containing a text field") from exc


def run(tasks: Iterable[Task], condition: str, backend: Backend, run_id: str) -> list[dict[str, Any]]:
    records = []
    for task in tasks:
        started = time.perf_counter()
        record: dict[str, Any] = {
            "run_id": run_id, "task_id": task.task_id, "condition": condition,
            "backend": backend.name, "runner_version": RUNNER_VERSION,
            "prompt_version": PROMPT_VERSION, "tags": list(task.tags), "status": "ok",
        }
        try:
            if condition == "critique_revision":
                initial = backend.complete(_messages(task, "direct"), "direct")
                critique = backend.complete([
                    {"role": "system", "content": "Critique the proposed answer against the task. Identify concrete errors or omissions."},
                    {"role": "user", "content": f"Task: {task.prompt}\n\nProposed answer:\n{initial.text}"},
                ], "critique")
                final = backend.complete([
                    {"role": "system", "content": "Revise the answer using the critique. Return only the final answer."},
                    {"role": "user", "content": f"Task: {task.prompt}\n\nInitial answer:\n{initial.text}\n\nCritique:\n{critique.text}"},
                ], "revision")
                record.update(initial_text=initial.text, critique_text=critique.text, answer=final.text,
                              calls=3, input_tokens=_sum(initial, critique, final, attr="input_tokens"),
                              output_tokens=_sum(initial, critique, final, attr="output_tokens"))
            else:
                final = backend.complete(_messages(task, condition), condition)
                record.update(answer=final.text, calls=1, input_tokens=final.input_tokens, output_tokens=final.output_tokens)
            record["score"] = _score(record["answer"], task.reference)
        except Exception as exc:  # preserve failures; never silently drop the denominator
            record.update(status="error", error_type=type(exc).__name__, error=str(exc), calls=record.get("calls", 0))
        record["elapsed_ms"] = round((time.perf_counter() - started) * 1000, 3)
        records.append(record)
    return records


def _sum(*responses: ModelResponse, attr: str) -> int | None:
    values = [getattr(response, attr) for response in responses]
    return sum(values) if all(value is not None for value in values) else None


def write_jsonl(path: str, records: Iterable[dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
