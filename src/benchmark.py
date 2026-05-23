from __future__ import annotations

import argparse
from collections import deque
from typing import Iterable

from .agent import ScriptedAgent
from .environment import VirtualLab, WorldConfig
from .schemas import AgentAction
from .solver import walls_of
from .worlds import generate_room


def _count_reachable(config: WorldConfig) -> int:
    walls = walls_of(config)
    queue: deque[tuple[int, int]] = deque([config.agent_start])
    visited: set[tuple[int, int]] = {config.agent_start}
    while queue:
        x, y = queue.popleft()
        for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
            nb = (x + dx, y + dy)
            if nb in walls or nb in visited:
                continue
            visited.add(nb)
            queue.append(nb)
    return len(visited)


def _run_one(config: WorldConfig, max_steps: int) -> tuple[bool, int, int]:
    env = VirtualLab(config=config)
    agent = ScriptedAgent(config=config)
    invalid = 0
    while env.step < max_steps:
        action = agent.choose_action(env.observe())
        result = env.apply(action)
        if not result.ok:
            invalid += 1
        if action.action == "finish":
            return result.ok, env.step, invalid
        if env.is_success():
            result = env.apply(AgentAction(action="finish"))
            return result.ok, env.step, invalid
    return env.is_success(), env.step, invalid


def benchmark(seeds: Iterable[int], width: int, height: int, max_steps: int) -> str:
    lines: list[str] = []
    lines.append("# Procedural-room benchmark")
    lines.append("")
    lines.append(
        f"World size {width}x{height}. Each row is one random room; the BFS-driven "
        "scripted agent runs to completion or `max_steps`."
    )
    lines.append("")
    lines.append("| seed | reachable cells | plan steps | invalid actions | succeeded |")
    lines.append("| ---: | ---: | ---: | ---: | :---: |")

    successes = 0
    total_steps = 0
    total_invalid = 0
    count = 0

    for seed in seeds:
        config = generate_room(seed=seed, width=width, height=height)
        succeeded, steps, invalid = _run_one(config, max_steps=max_steps)
        reachable = _count_reachable(config)
        successes += int(succeeded)
        total_steps += steps
        total_invalid += invalid
        count += 1
        flag = "yes" if succeeded else "no"
        lines.append(f"| {seed} | {reachable} | {steps} | {invalid} | {flag} |")

    lines.append("")
    lines.append("## Summary")
    lines.append(f"- success rate: {successes}/{count} ({100 * successes / count:.1f}%)")
    lines.append(f"- mean steps per run: {total_steps / count:.1f}")
    lines.append(f"- mean invalid actions per run: {total_invalid / count:.2f}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-seeds", type=int, default=20)
    parser.add_argument("--width", type=int, default=9)
    parser.add_argument("--height", type=int, default=7)
    parser.add_argument("--max-steps", type=int, default=200)
    args = parser.parse_args()
    print(benchmark(range(args.num_seeds), args.width, args.height, args.max_steps))


if __name__ == "__main__":
    main()
