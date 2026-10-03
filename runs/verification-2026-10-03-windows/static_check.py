"""Syntax/inventory checks only. Does not import or execute pilot code."""
import ast
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

root = Path(__file__).resolve().parents[2]
sources = sorted([*root.glob("pilot/*.py"), *root.glob("tests/*.py")])
inventory = {}
for path in sources:
    source = path.read_bytes()
    tree = ast.parse(source, filename=str(path))
    compile(tree, str(path), "exec")
    inventory[path.relative_to(root).as_posix()] = {
        "sha256": hashlib.sha256(source).hexdigest(),
        "test_methods": sum(isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
                            for node in ast.walk(tree)),
    }
json_files = sorted([*root.glob("config/*.json"), root / "prompts.json",
                     *root.glob("data/fixtures/*.json")])
for path in json_files:
    json.loads(path.read_text(encoding="utf-8"))
result = {
    "scope": "Static syntax and inventory only; no pilot import or runtime test execution",
    "base_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
    "platform": platform.system(), "python": sys.version.split()[0],
    "sources": inventory, "syntax_checks_passed": len(sources),
    "test_methods_defined_not_executed": sum(x["test_methods"] for x in inventory.values()),
    "json_parse_checks_passed": [p.relative_to(root).as_posix() for p in json_files],
}
output = Path(__file__).with_name("static-checks.json")
output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2))
