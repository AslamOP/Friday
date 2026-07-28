"""Operators — persistent, scheduled autonomous agents."""

from friday.operators.loader import load_operator
from friday.operators.manager import OperatorManager
from friday.operators.types import OperatorManifest

__all__ = ["OperatorManifest", "OperatorManager", "load_operator"]
