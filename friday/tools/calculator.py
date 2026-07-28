from __future__ import annotations
import ast
import operator
from friday.core.tool import Tool

_SAFE_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow, ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod, ast.USub: operator.neg, ast.UAdd: operator.pos,
}

class Calculator(Tool):
    name = "calculator"
    description = "Evaluate a mathematical expression"
    parameters = {
        "type": "object",
        "properties": {
            "expression": {"type": "string", "description": "Math expression like 2 + 2 * 3"},
        },
        "required": ["expression"],
    }
    
    def run(self, expression: str) -> str:
        try:
            tree = ast.parse(expression.strip(), mode="eval")
            result = self._eval(tree.body)
            return str(result)
        except Exception as e:
            return f"Error: {e}"
    
    def _eval(self, node):
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.BinOp):
            op = _SAFE_OPS.get(type(node.op))
            if not op:
                raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
            return op(self._eval(node.left), self._eval(node.right))
        elif isinstance(node, ast.UnaryOp):
            op = _SAFE_OPS.get(type(node.op))
            if not op:
                raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
            return op(self._eval(node.operand))
        raise ValueError(f"Unsupported expression: {type(node).__name__}")
