"""Skill source resolvers — Hermes, OpenClaw, generic GitHub."""

from friday.skills.sources.base import ResolvedSkill, SourceResolver
from friday.skills.sources.github import GitHubResolver
from friday.skills.sources.hermes import HERMES_REPO_URL, HermesResolver
from friday.skills.sources.openclaw import OPENCLAW_REPO_URL, OpenClawResolver

__all__ = [
    "GitHubResolver",
    "HERMES_REPO_URL",
    "HermesResolver",
    "OPENCLAW_REPO_URL",
    "OpenClawResolver",
    "ResolvedSkill",
    "SourceResolver",
]
