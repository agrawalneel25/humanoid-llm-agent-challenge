from __future__ import annotations

from collections import deque
from typing import Optional

from .environment import DELTAS, DIRECTIONS, Position, WorldConfig
from .schemas import AgentAction


def _cardinal_to_relative(target_cardinal: str, facing: str) -> str:
    target_idx = DIRECTIONS.index(target_cardinal)
    facing_idx = DIRECTIONS.index(facing)
    delta = (target_idx - facing_idx) % 4
    return {0: "forward", 1: "right", 2: "backward", 3: "left"}[delta]


def _border_walls(width: int, height: int) -> set[Position]:
    walls: set[Position] = set()
    for x in range(width):
        walls.add((x, 0))
        walls.add((x, height - 1))
    for y in range(height):
        walls.add((0, y))
        walls.add((width - 1, y))
    return walls


def walls_of(config: WorldConfig) -> set[Position]:
    return _border_walls(config.width, config.height) | config.interior_walls


def shortest_plan(config: WorldConfig) -> Optional[list[AgentAction]]:
    """BFS over (position, has_key, door_open) states.

    Returns an env-compatible action sequence (ending in `finish`), or None if
    the world is unsolvable. The plan never turns; every move uses an
    agent-relative direction computed from the initial facing.
    """
    walls = walls_of(config)
    facing = config.agent_facing
    start_state = (config.agent_start, False, False)
    goal_cell = config.cube

    queue: deque[tuple[tuple[Position, bool, bool], list[AgentAction]]] = deque()
    queue.append((start_state, []))
    visited: set[tuple[Position, bool, bool]] = {start_state}

    while queue:
        (pos, has_key, door_open), path = queue.popleft()

        if pos == goal_cell and has_key and door_open:
            return path + [AgentAction(action="finish")]

        for cardinal in DIRECTIONS:
            dx, dy = DELTAS[cardinal]
            new_pos = (pos[0] + dx, pos[1] + dy)
            if new_pos in walls:
                continue
            if new_pos == config.door and not door_open:
                continue
            new_state = (new_pos, has_key, door_open)
            if new_state in visited:
                continue
            visited.add(new_state)
            rel = _cardinal_to_relative(cardinal, facing)
            queue.append((new_state, path + [AgentAction(action="move", direction=rel)]))

        if pos == config.key and not has_key:
            new_state = (pos, True, door_open)
            if new_state not in visited:
                visited.add(new_state)
                queue.append((new_state, path + [AgentAction(action="pick_up")]))

        if has_key and not door_open:
            for cardinal in DIRECTIONS:
                dx, dy = DELTAS[cardinal]
                adj = (pos[0] + dx, pos[1] + dy)
                if adj == config.door:
                    new_state = (pos, has_key, True)
                    if new_state not in visited:
                        visited.add(new_state)
                        rel = _cardinal_to_relative(cardinal, facing)
                        queue.append(
                            (new_state, path + [AgentAction(action="open", direction=rel)])
                        )
                    break

    return None
