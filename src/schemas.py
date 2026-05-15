from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional


Direction = Literal["forward", "backward", "left", "right"]
ActionName = Literal["move", "turn", "look", "pick_up", "open", "finish"]


@dataclass
class AgentAction:
    action: ActionName
    direction: Optional[Direction] = None
    note: str = ""
