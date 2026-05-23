from __future__ import annotations

import random

from .environment import DIRECTIONS, WorldConfig


def generate_room(
    seed: int,
    width: int = 9,
    height: int = 7,
    max_attempts: int = 200,
) -> WorldConfig:
    """Generate a random solvable two-chamber room.

    The room is split by a single straight wall with one door. The key and
    the agent start on one side, the cube on the other. Solvability is checked
    by BFS; layouts that fail are retried.
    """
    rng = random.Random(seed)

    for _ in range(max_attempts):
        vertical_divider = rng.random() < 0.5
        interior_walls: set[tuple[int, int]] = set()
        if vertical_divider:
            wx = rng.randint(2, width - 3)
            for y in range(1, height - 1):
                interior_walls.add((wx, y))
            door_y = rng.randint(1, height - 2)
            interior_walls.discard((wx, door_y))
            door = (wx, door_y)
            left_cells = [(x, y) for x in range(1, wx) for y in range(1, height - 1)]
            right_cells = [(x, y) for x in range(wx + 1, width - 1) for y in range(1, height - 1)]
        else:
            wy = rng.randint(2, height - 3)
            for x in range(1, width - 1):
                interior_walls.add((x, wy))
            door_x = rng.randint(1, width - 2)
            interior_walls.discard((door_x, wy))
            door = (door_x, wy)
            left_cells = [(x, y) for x in range(1, width - 1) for y in range(1, wy)]
            right_cells = [(x, y) for x in range(1, width - 1) for y in range(wy + 1, height - 1)]

        if len(left_cells) < 2 or not right_cells:
            continue

        agent_start = rng.choice(left_cells)
        key_candidates = [c for c in left_cells if c != agent_start]
        key = rng.choice(key_candidates)
        cube = rng.choice(right_cells)
        agent_facing = rng.choice(DIRECTIONS)

        config = WorldConfig(
            width=width,
            height=height,
            agent_start=agent_start,
            agent_facing=agent_facing,
            interior_walls=interior_walls,
            key=key,
            door=door,
            cube=cube,
            goal_text="Find the key, open the door, reach the red cube, and finish.",
        )

        from .solver import shortest_plan

        if shortest_plan(config) is not None:
            return config

    raise RuntimeError(f"Could not generate a solvable room within {max_attempts} attempts")
