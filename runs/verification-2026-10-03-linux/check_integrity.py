"""Independent offline integrity probes, kept outside the repository."""
import copy
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
from pilot import core

results = []
def rejects(label, fn, expected):
    try:
        fn()
    except expected as exc:
        results.append({'check': label, 'passed': True, 'error_type': type(exc).__name__, 'message': str(exc)})
    else:
        raise AssertionError(label + ' unexpectedly succeeded')

with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    tasks = root / 'tasks.jsonl'
    tasks.write_bytes((core.ROOT / 'data/fixtures/tasks.jsonl').read_bytes())
    key = root / 'key.jsonl'
    key.write_bytes((core.ROOT / 'data/fixtures/key.jsonl').read_bytes())
    frozen = root / 'freeze.json'
    out = root / 'run'
    core.freeze(core.ROOT/'config/fixture.json', tasks, core.ROOT/'data/fixtures/manifest.json', frozen)
    rejects('freeze refuses overwrite', lambda: core.freeze(core.ROOT/'config/fixture.json', tasks, core.ROOT/'data/fixtures/manifest.json', frozen), ValueError)
    signed = frozen.read_bytes()
    changed = json.loads(signed)
    changed['config']['temperature'] = .9
    core.write_json(frozen, changed)
    rejects('freeze field tampering rejected before run', lambda: core.run(frozen, tasks, out), ValueError)
    frozen.write_bytes(signed)
    original_tasks = tasks.read_bytes()
    tasks.write_bytes(original_tasks + b'\n')
    rejects('task byte tampering rejected before run', lambda: core.run(frozen, tasks, out), ValueError)
    tasks.write_bytes(original_tasks)
    with patch.object(core, 'http_reply', side_effect=AssertionError('Unexpected HTTP adapter')):
        core.run(frozen, tasks, out)
    ledger = (out/'events.jsonl').read_bytes()
    with patch.object(core, 'http_reply', side_effect=AssertionError('Unexpected HTTP adapter')):
        core.run(frozen, tasks, out, backend_override=lambda *a: (_ for _ in ()).throw(AssertionError('Duplicate fixture request')))
    assert (out/'events.jsonl').read_bytes() == ledger
    results.append({'check': 'resume performs no adapter calls and preserves ledger', 'passed': True})
    original_key = key.read_bytes()
    key.write_bytes(original_key + b'\n')
    rejects('answer key byte tampering rejected at analysis', lambda: core.analyze(out, key), ValueError)
    key.write_bytes(original_key)
    first_event = ledger.splitlines()[0]
    (out/'events.jsonl').write_bytes(ledger + first_event + b'\n')
    rejects('duplicate ledger event rejected on resume', lambda: core.run(frozen, tasks, out), ValueError)
    rejects('duplicate ledger event rejected at analysis', lambda: core.analyze(out, key), ValueError)
    (out/'events.jsonl').write_bytes(ledger)
    with core.run_lock(out):
        rejects('simultaneous run lock rejected', lambda: core.run(frozen, tasks, out), BlockingIOError)
    changed = json.loads(signed)
    changed['code_sha256'] = '0' * 64
    changed['freeze_id'] = core.digest(core.encode({k:v for k,v in changed.items() if k != 'freeze_id'}))
    core.write_json(frozen, changed)
    rejects('signed freeze with differing runtime hash rejected', lambda: core.run(frozen, tasks, out), ValueError)
print(json.dumps(results, indent=2))
