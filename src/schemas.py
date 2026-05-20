from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

try:
    from pydantic import BaseModel, Field
    PYDANTIC_AVAILABLE = True
except ImportError:  # Allows the scripted demo to run without optional deps.
    PYDANTIC_AVAILABLE = False

    def Field(default=None, **_: object) -> object:
        return default


Direction = Literal["forward", "backward", "left", "right"]
ActionName = Literal["move", "turn", "look", "pick_up", "open", "finish"]


if not PYDANTIC_AVAILABLE:

    @dataclass
    class AgentAction:
        action: ActionName
        direction: Optional[Direction] = None
        note: str = ""
else:

    class AgentAction(BaseModel):
        action: ActionName
        direction: Optional[Direction] = Field(
            default=None,
            description="Required for move/open/turn actions where relevant.",
        )
        note: str = Field(
            default="",
            description="Short private reason for debugging the trajectory log.",
        )
