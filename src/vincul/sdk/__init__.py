"""vincul.sdk — High-level SDK for building vincul agents and tools.

Reduces onboarding boilerplate by providing:
  - VinculContext: one-stop coalition setup (principals, contracts, scopes)
  - @vincul_tool / @vincul_tool_action: decorators for tool providers
  - @vincul_agent / @vincul_agent_action: decorators for agents
  - ToolResult: unified return type from decorated operations
"""

from vincul.sdk.context import VinculContext
from vincul.sdk.decorators import ToolResult, vincul_tool_action, vincul_tool
from vincul.sdk.agent import vincul_agent_action, vincul_agent

__all__ = [
    "VinculContext",
    "ToolResult",
    "vincul_tool_action",
    "vincul_tool",
    "vincul_agent_action",
    "vincul_agent",
]
