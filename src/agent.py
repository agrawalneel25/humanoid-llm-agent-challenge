from __future__ import annotations

from .schemas import AgentAction


class ScriptedAgent:
    """Deterministic baseline that proves the environment and success checks work."""

    def __init__(self) -> None:
        self.actions = [
            AgentAction(action="move", direction="right", note="step onto key"),
            AgentAction(action="pick_up", note="collect key"),
            AgentAction(action="move", direction="left", note="return to corridor"),
            AgentAction(action="move", direction="forward", note="move toward door"),
            AgentAction(action="move", direction="forward", note="stand left of door"),
            AgentAction(action="open", direction="forward", note="unlock door"),
            AgentAction(action="move", direction="forward", note="enter door cell"),
            AgentAction(action="move", direction="forward", note="reach cube"),
            AgentAction(action="finish", note="complete goal"),
        ]

    def choose_action(self, observation: dict) -> AgentAction:
        idx = observation["step"]
        if idx < len(self.actions):
            return self.actions[idx]
        return AgentAction(action="finish", note="step limit fallback")
