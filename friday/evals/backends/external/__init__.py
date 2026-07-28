"""External-framework subprocess backends (Hermes Agent, OpenClaw)."""

from friday.evals.backends.external.hermes_agent import HermesBackend
from friday.evals.backends.external.openclaw import OpenClawBackend

__all__ = ["HermesBackend", "OpenClawBackend"]
