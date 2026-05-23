from __future__ import annotations

import argparse

from .agent import OpenAIAgent, ScriptedAgent
from .environment import VirtualLab
from .schemas import AgentAction
from .worlds import generate_room


def run(agent_name: str, model: str, max_steps: int, seed: int | None, render: bool) -> int:
    config = generate_room(seed=seed) if seed is not None else None
    env = VirtualLab(config=config) if config is not None else VirtualLab()
    agent = OpenAIAgent(model) if agent_name == "openai" else ScriptedAgent(config=env.config)

    if render:
        print("initial state:")
        print(env.render())
        print()

    for _ in range(max_steps):
        obs = env.observe()
        action = agent.choose_action(obs)
        result = env.apply(action)
        direction = f" {action.direction}" if action.direction else ""
        print(f"{env.step:02d} action={action.action}{direction} ok={result.ok} msg={result.message}")
        if render:
            print(env.render())
            print()
        if action.action == "finish":
            return 0 if result.ok else 1
        if env.is_success():
            finish = AgentAction(action="finish")
            result = env.apply(finish)
            print(f"{env.step:02d} action=finish ok={result.ok} msg={result.message}")
            if render:
                print(env.render())
                print()
            return 0 if result.ok else 1
    print("step limit reached")
    return 1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent", choices=["scripted", "openai"], default="scripted")
    parser.add_argument("--model", default="gpt-4o-mini")
    parser.add_argument("--max-steps", type=int, default=100)
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="If set, runs a procedurally generated room with this seed.",
    )
    parser.add_argument("--render", action="store_true", help="Print the grid at each step.")
    args = parser.parse_args()
    raise SystemExit(run(args.agent, args.model, args.max_steps, args.seed, args.render))


if __name__ == "__main__":
    main()
