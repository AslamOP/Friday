"""Safe calculator tool."""

from __future__ import annotations

import ast
import operator

from friday._registry import Catalog
from friday._tools import Outcome, Proc, Spec

_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow,
    ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod,
    ast.USub: operator.neg, ast.UAdd: operator.pos,
}


def _eval(node):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.BinOp):
        return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp):
        return _OPS[type(node.op)](_eval(node.operand))
    raise ValueError(f"unsupported: {type(node).__name__}")


@Catalog.tag("proc", "calc")
class CalcProc(Proc):
    label = "calc"

    @property
    def spec(self) -> Spec:
        return Spec(
            name="calc",
            desc="Evaluate a math expression safely",
            params={
                "type": "object",
                "properties": {"expr": {"type": "string", "description": "Expression like 2 + 2 * 3"}},
                "required": ["expr"],
            },
        )

    def run(self, **kw) -> Outcome:
        expr = kw.get("expr", "")
        try:
            tree = ast.parse(expr.strip(), mode="eval")
            val = _eval(tree.body)
            return Outcome(action="calc", text=str(val))
        except Exception as e:
            return Outcome(action="calc", text=f"error: {e}", ok=False)
