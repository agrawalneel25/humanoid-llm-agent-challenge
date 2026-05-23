from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Optional, Protocol

from .environment import WorldConfig, make_default_world
from .schemas import AgentAction


SYSTEM_PROMPT = (
    "You control an agent in a small grid world. The agent's goal is in each "
    "observation. Each turn, return exactly one JSON object with keys "
    "'action', 'direction' (optional), and 'note' (optional). Valid actions: "
    "move (direction in forward/backward/left/right), turn (direction in "
    "left/right), look, pick_up, open (direction in forward/backward/left/"
    "right), finish. Directions are relative to the agent's current facing. "
    "Invalid actions are rejected and reported back in last_action; use that "
    "feedback to recover. Return only the JSON object, no prose."
)


class Agent(Protocol):
    def choose_action(self, observation: dict) -> AgentAction:
        ...


class ScriptedAgent:
    """Deterministic baseline. BFS-plans for any WorldConfig and replays."""

    def __init__(self, config: Optional[WorldConfig] = None) -> None:
        if config is None:
            config = make_default_world()
        from .solver import shortest_plan

        plan = shortest_plan(config)
        if plan is None:
            raise RuntimeError("BFS could not find a plan for the given config")
        self.plan = plan
        self.index = 0

    def choose_action(self, observation: dict) -> AgentAction:
        if self.index < len(self.plan):
            action = self.plan[self.index]
            self.index += 1
            return action
        return AgentAction(action="finish", note="plan exhausted")


class OpenAIAgent:
    """LLM agent over OpenAI's Responses API. Uses stdlib urllib, no deps."""

    def __init__(self, model: str = "gpt-4o-mini") -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("Set OPENAI_API_KEY to use the OpenAI agent.")
        self.api_key = api_key
        self.model = model

    def choose_action(self, observation: dict) -> AgentAction:
        text = self._call(json.dumps(observation, separators=(",", ":")))
        payload = self._extract_json(text)
        return AgentAction(
            action=payload["action"],
            direction=payload.get("direction"),
            note=str(payload.get("note", "")),
        )

    def _call(self, user_content: str) -> str:
        body = json.dumps(
            {
                "model": self.model,
                "input": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            "https://api.openai.com/v1/responses",
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenAI request failed: {exc.code} {detail}") from exc
        return _response_text(data)

    @staticmethod
    def _extract_json(text: str) -> dict:
        text = text.strip()
        if text.startswith("```"):
            stripped = text.split("\n", 1)[1] if "\n" in text else text
            stripped = stripped.rsplit("```", 1)[0]
            text = stripped.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match is None:
                raise RuntimeError(f"Could not extract JSON from model output: {text!r}")
            return json.loads(match.group(0))


def _response_text(data: dict) -> str:
    chunks: list[str] = []
    for item in data.get("output", []):
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []):
            if isinstance(content, dict) and content.get("type") == "output_text":
                chunks.append(str(content.get("text", "")))
    if chunks:
        return "\n".join(chunks)
    if "output_text" in data:
        return str(data["output_text"])
    raise RuntimeError(f"Response did not include output text: {data!r}")
