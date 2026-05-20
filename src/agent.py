from __future__ import annotations

import json
import os
from typing import Protocol

from .schemas import AgentAction


class Agent(Protocol):
    def choose_action(self, observation: dict) -> AgentAction:
        ...


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


class OpenAIAgent:
    def __init__(self, model: str) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Install requirements.txt to use the OpenAI agent.") from exc
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("Set OPENAI_API_KEY to use the OpenAI agent.")
        self.client = OpenAI()
        self.model = model

    def choose_action(self, observation: dict) -> AgentAction:
        response = self.client.responses.parse(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": (
                        "You control an agent in a small robotics lab. "
                        "Return exactly one valid JSON action. Prefer making progress toward the goal. "
                        "Do not narrate. Use move/open directions relative to current facing."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(observation, separators=(",", ":")),
                },
            ],
            text_format=AgentAction,
        )
        for output in response.output:
            if output.type != "message":
                continue
            for item in output.content:
                if getattr(item, "parsed", None):
                    return item.parsed
        raise RuntimeError("Model response did not include a parsed AgentAction.")
