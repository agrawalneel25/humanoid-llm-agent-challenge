from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .schemas import AgentAction


Position = tuple[int, int]

DIRECTIONS: list[str] = ["north", "east", "south", "west"]
DELTAS: dict[str, Position] = {
    "north": (0, -1),
    "east": (1, 0),
    "south": (0, 1),
    "west": (-1, 0),
}


@dataclass
class Cell:
    kind: str
    locked: bool = False
    open: bool = False


@dataclass
class StepResult:
    ok: bool
    message: str


@dataclass
class VirtualLab:
    width: int = 7
    height: int = 5
    position: Position = (1, 1)
    facing: str = "east"
    inventory: list[str] = field(default_factory=list)
    step: int = 0
    last_result: StepResult = field(default_factory=lambda: StepResult(True, "start"))

    def __post_init__(self) -> None:
        self.grid: dict[Position, Cell] = {}
        for x in range(self.width):
            self.grid[(x, 0)] = Cell("wall")
            self.grid[(x, self.height - 1)] = Cell("wall")
        for y in range(self.height):
            self.grid[(0, y)] = Cell("wall")
            self.grid[(self.width - 1, y)] = Cell("wall")
        self.grid[(2, 2)] = Cell("wall")
        self.grid[(3, 2)] = Cell("wall")
        self.grid[(4, 1)] = Cell("door", locked=True, open=False)
        self.grid[(1, 2)] = Cell("key")
        self.grid[(5, 1)] = Cell("red_cube")

    @property
    def goal(self) -> str:
        return "Find the key, open the locked lab door, reach the red cube, and finish."

    def observe(self) -> dict[str, Any]:
        visible = []
        px, py = self.position
        # 4-neighbourhood + current cell only. Tried the full grid first; model
        # stopped navigating and just read coordinates off the map.
        for dx, dy in [(0, -1), (1, 0), (0, 1), (-1, 0), (0, 0)]:
            pos = (px + dx, py + dy)
            cell = self.grid.get(pos, Cell("empty"))
            item: dict[str, Any] = {
                "relative": [dx, dy],
                "position": [pos[0], pos[1]],
                "type": cell.kind,
            }
            if cell.kind == "door":
                item["locked"] = cell.locked
                item["open"] = cell.open
            visible.append(item)
        return {
            "step": self.step,
            "position": [px, py],
            "facing": self.facing,
            "inventory": list(self.inventory),
            "goal": self.goal,
            "visible_cells": visible,
            "last_action": {
                "ok": self.last_result.ok,
                "message": self.last_result.message,
            },
        }

    def apply(self, action: AgentAction) -> StepResult:
        self.step += 1
        name = action.action
        if name == "look":
            result = StepResult(True, "refreshed observation")
        elif name == "turn":
            result = self._turn(action.direction)
        elif name == "move":
            result = self._move(action.direction)
        elif name == "pick_up":
            result = self._pick_up()
        elif name == "open":
            result = self._open(action.direction)
        elif name == "finish":
            result = StepResult(self.is_success(), "success" if self.is_success() else "goal not complete")
        else:
            result = StepResult(False, f"unknown action: {name}")
        self.last_result = result
        return result

    def is_success(self) -> bool:
        return self.position == (5, 1) and "key" in self.inventory and self.grid[(4, 1)].open

    def _turn(self, direction: str | None) -> StepResult:
        if direction not in {"left", "right"}:
            return StepResult(False, "turn requires left or right")
        idx = DIRECTIONS.index(self.facing)
        self.facing = DIRECTIONS[(idx + (1 if direction == "right" else -1)) % 4]
        return StepResult(True, f"now facing {self.facing}")

    def _move(self, direction: str | None) -> StepResult:
        target = self._relative_position(direction)
        if target is None:
            return StepResult(False, "move requires forward/backward/left/right")
        cell = self.grid.get(target, Cell("empty"))
        if cell.kind == "wall":
            return StepResult(False, f"blocked by wall at {target}")
        if cell.kind == "door" and not cell.open:
            return StepResult(False, f"blocked by closed door at {target}")
        self.position = target
        return StepResult(True, f"moved to {target}")

    def _pick_up(self) -> StepResult:
        cell = self.grid.get(self.position, Cell("empty"))
        if cell.kind != "key":
            return StepResult(False, "nothing to pick up")
        self.inventory.append("key")
        self.grid[self.position] = Cell("empty")
        return StepResult(True, "picked up key")

    def _open(self, direction: str | None) -> StepResult:
        target = self._relative_position(direction)
        if target is None:
            return StepResult(False, "open requires forward/backward/left/right")
        cell = self.grid.get(target, Cell("empty"))
        if cell.kind != "door":
            return StepResult(False, f"no door at {target}")
        if cell.locked and "key" not in self.inventory:
            return StepResult(False, "door is locked and key is missing")
        cell.locked = False
        cell.open = True
        return StepResult(True, f"opened door at {target}")

    def _relative_position(self, direction: str | None) -> Position | None:
        if direction not in {"forward", "backward", "left", "right"}:
            return None
        facing_idx = DIRECTIONS.index(self.facing)
        if direction == "backward":
            facing_idx += 2
        elif direction == "left":
            facing_idx -= 1
        elif direction == "right":
            facing_idx += 1
        dx, dy = DELTAS[DIRECTIONS[facing_idx % 4]]
        return (self.position[0] + dx, self.position[1] + dy)
