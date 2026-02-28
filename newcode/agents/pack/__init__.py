"""Workflow Agents - Specialized sub-agents coordinated by the Orchestrator.

This package contains the specialized agents that work together under
the Orchestrator's coordination for parallel multi-agent workflows:

- **Tracker** - Issue tracking specialist (bd only)
- **Workspace Manager** - Worktree management (git worktree from base branch)
- **Executor** - Task execution (coding work in worktrees)
- **Reviewer** - Code review critic (quality gatekeeper)
- **QA Checker** - QA critic (tests, coverage, quality)
- **Merger** - Local branch merging (git merge to base branch)

All work happens locally - no GitHub PRs or remote pushes.
Everything merges to a declared base branch.

Each agent is designed to do one thing well, following the Unix philosophy.
The Orchestrator coordinates them to execute complex parallel workflows.
"""

from .bloodhound import BloodhoundAgent
from .husky import HuskyAgent
from .retriever import RetrieverAgent
from .shepherd import ShepherdAgent
from .terrier import TerrierAgent
from .watchdog import WatchdogAgent

__all__ = [
    "BloodhoundAgent",
    "TerrierAgent",
    "RetrieverAgent",
    "HuskyAgent",
    "ShepherdAgent",
    "WatchdogAgent",
]
