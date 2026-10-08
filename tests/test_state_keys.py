"""Every literal key an agent or graph node reads (or writes) on the state is a PageState field."""

import ast
from pathlib import Path

from core.state import PageState

ROOT = Path(__file__).resolve().parent.parent
SOURCES = sorted([*ROOT.glob("agents/*.py"), *ROOT.glob("workflow/*.py")])
# Names the state (or an agent's input dict) is bound to in node and agent functions.
STATE_NAMES = {"state", "inputs"}
# (file, key) -> reason. Only for dicts named like the state that are not PageState.
ALLOWED = {
    ("agents/repair_agent.py", "html"): "repair agent input dict, not PageState",
    ("agents/repair_agent.py", "problems"): "repair agent input dict, not PageState",
}


def _literal_keys(tree: ast.AST):
    """(line, key) for state["key"] and state.get("key", ...)."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript):
            receiver, key = node.value, node.slice
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "get"
            and node.args
        ):
            receiver, key = node.func.value, node.args[0]
        else:
            continue
        if (
            isinstance(receiver, ast.Name)
            and receiver.id in STATE_NAMES
            and isinstance(key, ast.Constant)
            and isinstance(key.value, str)
        ):
            yield node.lineno, key.value


def test_state_keys_read_by_agents_and_nodes_are_page_state_fields():
    fields = set(PageState.__annotations__)
    unknown = [
        f"{rel}:{line}: {key!r}"
        for path in SOURCES
        for rel in [path.relative_to(ROOT).as_posix()]
        for line, key in _literal_keys(ast.parse(path.read_text(encoding="utf-8")))
        if key not in fields and (rel, key) not in ALLOWED
    ]
    assert SOURCES, "no agent or graph modules found"
    assert unknown == []
