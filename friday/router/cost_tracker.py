import logging
logger = logging.getLogger("friday.cost_tracker")
class CostTracker:
    def __init__(self): self._total_tokens_in = 0; self._total_tokens_out = 0; self._total_cost = 0.0
    def log_usage(self, model: str = "", tokens_in: int = 0, tokens_out: int = 0, success: bool = True):
        self._total_tokens_in += tokens_in; self._total_tokens_out += tokens_out
        self._total_cost += (tokens_in + tokens_out) * 0.000001
    def get_stats(self) -> dict: return {"tokens_in": self._total_tokens_in, "tokens_out": self._total_tokens_out, "cost": round(self._total_cost, 6)}
